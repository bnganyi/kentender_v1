"""Departmental Needs read projections (NDS-CHG-001 v1.1 §8.1).

Every read resolves rows through the same native scope predicate used by the
commands (`permissions.can_view`), so counts, rows, detail and exports cannot
diverge (NDS-BR-019, NDS-AC-021).

§1.1 removes the four summary cards, the separate action/waiting sections and
the advanced register filters in favour of one role-appropriate table with
minimal search/status filters; Phase 7 reshapes the screens onto this
projection. The support-lookup surface is removed by §1.1.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, formatdate

from kentender_procurement.departmental_needs.constants import (
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	TASK_OPEN,
	VERSION_CONTENT_FIELDS,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.context import selectable_financial_years
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	can_view,
	creation_contexts,
	is_owner,
	require_view,
)
from kentender_procurement.departmental_needs.services.usage import planning_usage


def _open_review_task(need: str) -> dict[str, str] | None:
	row = frappe.db.get_value(
		"Departmental Need Review Task",
		{"departmental_need": need, "status": TASK_OPEN},
		["name", "task_type", "decision_token"],
		order_by="opened_at desc",
		as_dict=True,
	)
	if not row:
		return None
	return {"name": row.name, "task_type": row.task_type, "decision_token": row.decision_token}


def _version_facts(version: str) -> dict[str, Any]:
	if not version:
		return {}
	row = frappe.db.get_value(
		"Departmental Need Version",
		version,
		["name", "version_number", "version_status", "content_hash", *VERSION_CONTENT_FIELDS],
		as_dict=True,
	)
	return dict(row) if row else {}


def _quantity_label(version: dict[str, Any]) -> str:
	quantity = flt(version.get("indicative_quantity"))
	if quantity <= 0:
		return ""
	value = int(quantity) if float(quantity).is_integer() else quantity
	label = cstr(
		frappe.db.get_value("Unit Of Measure", version.get("unit"), "unit_label")
		or version.get("unit")
		or ""
	)
	return f"{value} {label}".strip()


def _actions(doc, principal: str, profile: str) -> list[dict[str, str]]:
	"""One row exposes one action; the workspace button wires to actions[0]."""
	if doc.current_state == STATE_SUBMITTED and profile == "department" and not is_owner(doc, principal):
		task = _open_review_task(doc.name) or {}
		return [
			{
				"code": "review",
				"label": "Review",
				"task": task.get("name", ""),
				"decision_token": task.get("decision_token", ""),
			}
		]
	if profile == "owner" and doc.current_state in {STATE_DRAFT, STATE_RETURNED}:
		# A Draft or Returned Need is by definition incomplete, so its own author
		# lands straight in the editable form rather than a read-only preview.
		return [{"code": "edit", "label": "Continue"}, {"code": "view", "label": "View"}]
	return [{"code": "view", "label": "View"}] if profile != "none" else []


def _selected_context(principal: str, pe: str, ou: str) -> tuple[dict[str, str] | None, list[dict[str, str]]]:
	contexts = creation_contexts(principal)
	if not contexts:
		return None, contexts
	if pe or ou:
		selected = next(
			(
				row
				for row in contexts
				if row["procuring_entity"] == pe and row["organisation_unit"] == ou
			),
			None,
		)
		if not selected:
			fail(
				"NDS_SCOPE_DENIED",
				"The selected Departmental Needs context is outside your permitted scope.",
			)
		return selected, contexts
	if len(contexts) > 1:
		return None, contexts
	return contexts[0], contexts


def get_workspace(
	*,
	procuring_entity: str = "",
	organisation_unit: str = "",
	financial_year: str = "",
	search: str = "",
	status: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	principal = actor(user)
	selected, contexts = _selected_context(
		principal, cstr(procuring_entity).strip(), cstr(organisation_unit).strip()
	)
	if not selected:
		return {
			"ok": False,
			"outcome": "NO_AUTHORISED_CONTEXT" if not contexts else "CONTEXT_SELECTION_REQUIRED",
			"contexts": contexts,
			"financial_years": selectable_financial_years(),
			"needs": [],
			"actions": [],
		}
	fy = cstr(financial_year).strip()
	filters: dict[str, Any] = {
		"procuring_entity": selected["procuring_entity"],
		"organisation_unit": selected["organisation_unit"],
	}
	if fy:
		filters["financial_year"] = fy
	if cstr(status).strip():
		filters["current_state"] = cstr(status).strip()
	rows = frappe.get_all(
		"Departmental Need",
		filters=filters,
		fields=[
			"name",
			"need_reference",
			"owner",
			"procuring_entity",
			"organisation_unit",
			"financial_year",
			"current_state",
			"current_version",
			"current_accepted_version",
			"record_version",
		],
		order_by="need_reference asc",
		limit_page_length=0,
	)
	term = cstr(search).strip().lower()
	needs = []
	for row in rows:
		doc = frappe._dict(row)
		allowed, profile = can_view(doc, principal)
		if not allowed or doc.current_state == STATE_WITHDRAWN:
			continue
		version = _version_facts(doc.current_version)
		title = cstr(version.get("title"))
		if term and term not in title.lower() and term not in cstr(doc.need_reference).lower():
			continue
		required_by = version.get("required_by_date")
		needs.append(
			{
				"name": doc.name,
				"reference": doc.need_reference,
				"title": title,
				"author_label": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
				"quantity_label": _quantity_label(version),
				"required_by": str(required_by or ""),
				"required_by_label": formatdate(required_by, "d MMMM yyyy") if required_by else "",
				"status": doc.current_state,
				"planning_usage": planning_usage(doc.name),
				"record_version": doc.record_version,
				"actions": _actions(doc, principal, profile),
			}
		)
	return {
		"ok": True,
		"outcome": "READY",
		"contexts": contexts,
		"financial_years": selectable_financial_years(),
		"context": {**selected, "financial_year": fy},
		"needs": needs,
		"count_label": f"{len(needs)} need" if len(needs) == 1 else f"{len(needs)} needs",
		"actions": [{"code": "create", "label": "Create need"}],
	}


def get_need(*, need: str, user: str | None = None) -> dict[str, Any]:
	principal = actor(user)
	if not frappe.db.exists("Departmental Need", need):
		# §9 — disclose no protected record data, including its existence.
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	doc = frappe.get_doc("Departmental Need", need)
	profile = require_view(doc, principal)
	latest_return = None
	if doc.current_state == STATE_RETURNED:
		row = frappe.db.get_value(
			"Departmental Need Decision",
			{"departmental_need": doc.name, "action": "Return for correction"},
			["reason", "actor", "occurred_at"],
			order_by="occurred_at desc",
			as_dict=True,
		)
		if row:
			latest_return = {
				"reason": row.reason,
				"actor": row.actor,
				"actor_label": frappe.db.get_value("User", row.actor, "full_name") or row.actor,
				"occurred_at": str(row.occurred_at),
				"occurred_label": formatdate(row.occurred_at, "d MMMM y")
				+ " at "
				+ frappe.utils.format_time(row.occurred_at, "HH:mm"),
			}
	return {
		"ok": True,
		"need": doc.as_dict(no_nulls=True),
		"current_version": _version_facts(doc.current_version),
		"accepted_version": _version_facts(doc.current_accepted_version),
		"latest_return": latest_return,
		"author_label": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		"planning_usage": planning_usage(doc.name),
		"open_task": _open_review_task(doc.name),
		"actions": _actions(doc, principal, profile),
		"access_profile": profile,
	}
