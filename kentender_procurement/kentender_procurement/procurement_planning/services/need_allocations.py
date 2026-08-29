"""Accepted Departmental Need to Procurement Planning allocation.

BOUNDARY (firm D1 decision, 2026-08-29): Departmental Needs and Procurement
Planning are separate modules within `kentender_procurement`. Planning consumes
Accepted Needs **only** through the published handoff contract. Direct access to
Departmental Needs DocTypes, tables or internal services is prohibited and is
enforced by the Phase 9 architecture test (NDS-910).

This module now honours that boundary. Every fact about a Need arrives through
one of two published contracts:

- `departmental_needs.services.events.current_accepted_events()` — the §7.1
  `DepartmentalNeedAccepted.v2` payloads for a PE/FY/OU context, replayed from
  the outbox; and
- `departmental_needs.services.workspace.get_current_accepted_need()` — §8.1's
  typed single-Need source contract, which returns `NDS_SOURCE_STALE` or
  `NDS_NOT_ACCEPTED` rather than letting Planning act on a stale version.

NDS-CHG-001 v1.1 §1.1 also removes partial Need allocation: Planning takes the
full accepted quantity of the current accepted version and cannot split, combine
or override it (NDS-AC-014). Allocation is therefore per accepted version, not
per Need line — the item child table no longer exists.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_core.services.authorization_policy import ResourceContext, require_capability
from kentender_procurement.departmental_needs.services.events import current_accepted_events
from kentender_procurement.departmental_needs.services.workspace import get_current_accepted_need
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	new_concurrency_token,
)

# Planning-owned capabilities. Departmental Needs itself uses native Frappe
# permissions only (NDS-AC-044); these identifiers belong to Planning's own
# authorization model and are not a Departmental Needs permission source.
CAP_ALLOCATE = "procurement_planning.need_allocate"
CAP_READ_ACCEPTED_FOR_PLANNING = "procurement_planning.read_accepted_need"


def _actor(user: str | None) -> str:
	return cstr(user or frappe.session.user).strip()


def _plan_context(plan) -> ResourceContext:
	return ResourceContext("Procurement Plan", plan.name, plan.procuring_entity, plan.financial_year)


def _allocated(need: str, statuses: tuple[str, ...]) -> float:
	return flt(
		frappe.db.sql(
			"""
			select coalesce(sum(allocated_quantity), 0)
			from `tabPlan Need Allocation`
			where departmental_need = %s and status in %s
			""",
			(need, statuses),
		)[0][0]
	)


def list_eligible_needs(*, plan: str, user: str | None = None) -> dict[str, Any]:
	"""Accepted Needs not yet represented in this Plan.

	Sourced from the published accepted-event payloads, so Planning sees exactly
	what the event stream published and never a Need table.
	"""
	principal = _actor(user)
	plan_doc = frappe.get_doc("Procurement Plan", plan)
	require_capability(principal, CAP_READ_ACCEPTED_FOR_PLANNING, _plan_context(plan_doc))
	out = []
	for payload in current_accepted_events(
		procuring_entity=plan_doc.procuring_entity, financial_year=plan_doc.financial_year
	):
		# Already represented at its full accepted quantity: nothing left to add.
		if _allocated(payload["need_id"], ("Draft", "Effective")) > 0:
			continue
		out.append(
			{
				"need": payload["need_id"],
				"reference": payload["need_reference"],
				"organisation_unit": payload["org_unit_id"],
				"accepted_version": payload["accepted_version_id"],
				"content_hash": payload["content_hash"],
				"title": payload["title"],
				"description": payload["description"],
				"expected_operational_result": payload["expected_operational_result"],
				"quantity": flt(payload["indicative_quantity"]),
				"unit": payload["unit_id"],
				"required_by": payload["required_by_date"],
			}
		)
	return {"ok": True, "plan": plan_doc.name, "needs": out, "eligible_need_count": len(out)}


def _parse(value) -> list[dict[str, Any]]:
	rows = json.loads(value) if isinstance(value, str) else value
	if not isinstance(rows, list) or not rows:
		frappe.throw("At least one Need allocation is required.", title="NDS_ALLOCATION_REQUIRED")
	return rows


def allocate_need_lines(
	*,
	plan: str,
	plan_item: str,
	allocations,
	expected_version_token: str,
	idempotency_key: str,
	reason: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	principal, key = _actor(user), cstr(idempotency_key).strip()
	if not key:
		frappe.throw("An idempotency key is required.", title="NDS_IDEMPOTENCY_KEY_REQUIRED")
	existing = frappe.get_all(
		"Plan Need Allocation", filters={"idempotency_key": ["like", f"{key}:%"]}, pluck="name"
	)
	if existing:
		return {"ok": True, "idempotent": True, "allocations": existing}
	plan_doc = frappe.get_doc("Procurement Plan", plan)
	item = frappe.get_doc("Procurement Plan Item", plan_item)
	if item.plan != plan_doc.name:
		frappe.throw("Plan Item does not belong to the selected Plan.", title="NDS_PLAN_ITEM_MISMATCH")
	version_name = cstr(plan_doc.open_draft_version)
	if not version_name:
		frappe.throw("The Plan has no open Draft Version.", title="NDS_PLAN_DRAFT_REQUIRED")
	require_capability(principal, CAP_ALLOCATE, _plan_context(plan_doc))
	frappe.db.sql(
		"select name from `tabProcurement Plan Version` where name=%s for update", version_name
	)
	assert_version_concurrency(version_name, expected_version_token)
	rows = _parse(allocations)
	created = []
	for index, row in enumerate(rows, 1):
		need_name = cstr(row.get("departmental_need"))
		# §8.1 — the typed source contract validates acceptance, context and
		# staleness for us, and raises NDS_NOT_ACCEPTED / NDS_SOURCE_STALE
		# rather than returning a Need this Plan must not use.
		source = get_current_accepted_need(
			need=need_name,
			expected_procuring_entity=plan_doc.procuring_entity,
			expected_financial_year=plan_doc.financial_year,
			expected_content_hash=cstr(row.get("content_hash") or ""),
			user=principal,
		)
		require_capability(
			principal,
			CAP_ALLOCATE,
			ResourceContext(
				"Departmental Need",
				source["need"],
				plan_doc.procuring_entity,
				plan_doc.financial_year,
				source["organisation_unit"],
			),
		)
		# §7.2 / NDS-AC-014 — the full accepted quantity, exactly once.
		quantity = flt(source["indicative_quantity"])
		if quantity <= 0:
			frappe.throw("The accepted Need has no usable quantity.", title="NDS_ALLOCATION_INVALID")
		frappe.db.sql(
			"select name from `tabPlan Need Allocation` where departmental_need=%s and status in ('Draft','Effective') for update",
			source["need"],
		)
		if _allocated(source["need"], ("Draft", "Effective")) > 0:
			frappe.throw(
				"This Need is already represented in the Plan at its full accepted quantity.",
				title="NDS_ALLOCATION_EXCEEDS_AVAILABLE",
			)
		allocation = frappe.get_doc(
			{
				"doctype": "Plan Need Allocation",
				"plan_item": item.name,
				"departmental_need": source["need"],
				"departmental_need_version": source["accepted_version"],
				"source_content_hash": source["content_hash"],
				"source_organisation_unit": source["organisation_unit"],
				"allocated_quantity": quantity,
				"status": "Draft",
				"proposed_in_version": version_name,
				"reason": cstr(reason),
				"idempotency_key": f"{key}:{index}",
			}
		).insert(ignore_permissions=True)
		created.append(allocation.name)
	new_token = new_concurrency_token()
	frappe.db.set_value(
		"Procurement Plan Version", version_name, "concurrency_token", new_token, update_modified=True
	)
	return {
		"ok": True,
		"idempotent": False,
		"plan": plan_doc.name,
		"plan_item": item.name,
		"allocations": created,
		"concurrency_token": new_token,
	}


def activate_need_allocations(*, version: str) -> list[str]:
	"""Make this version's Draft allocations Effective.

	The accepted quantity is re-read through the §8.1 source contract at the
	moment of activation, so a Need superseded or withdrawn since the Draft was
	proposed fails here rather than becoming an Active Plan dependency.
	"""
	rows = frappe.get_all(
		"Plan Need Allocation",
		filters={"proposed_in_version": version, "status": "Draft"},
		pluck="name",
	)
	if not rows:
		return []
	frappe.db.sql(
		"select name from `tabPlan Need Allocation` where name in %(names)s for update", {"names": rows}
	)
	for name in rows:
		allocation = frappe.get_doc("Plan Need Allocation", name)
		source = get_current_accepted_need(
			need=allocation.departmental_need,
			expected_content_hash=cstr(allocation.source_content_hash or ""),
		)
		accepted = flt(source["indicative_quantity"])
		effective = _allocated(allocation.departmental_need, ("Effective",))
		if effective + flt(allocation.allocated_quantity) > accepted:
			frappe.throw(
				"Approved allocation would exceed the accepted Need quantity.",
				title="NDS_EFFECTIVE_ALLOCATION_EXCEEDS_LINE",
			)
	now = now_datetime()
	for name in rows:
		frappe.db.set_value(
			"Plan Need Allocation",
			name,
			{"status": "Effective", "effective_from_version": version, "effective_at": now},
			update_modified=True,
		)
	return rows


def reverse_need_allocations(*, plan_item: str, version: str, reason: str) -> list[str]:
	rows = frappe.get_all(
		"Plan Need Allocation",
		filters={"plan_item": plan_item, "status": ["in", ["Draft", "Effective"]]},
		pluck="name",
	)
	now = now_datetime()
	for name in rows:
		frappe.db.set_value(
			"Plan Need Allocation",
			name,
			{"status": "Reversed", "reversed_by_version": version, "reversed_at": now, "reason": reason},
			update_modified=True,
		)
	return rows
