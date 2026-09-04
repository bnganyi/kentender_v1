"""Planning usage projection (NDS-CHG-001 v1.1 §4.7, §7.2, §8.2).

Usage is `Not included`, `Fully included` or — since PLN-CHG-001 v1.12 §4.4 —
`Not proceeding` (the department recorded in its departmental plan that it is
not pursuing the accepted Need this financial year, with a reason).
`Partially included` is removed by §1.1 and forbidden by §17, along with any
partial Need allocation or Planning quantity override (NDS-AC-014, NDS-AC-015).

Usage is *not* lifecycle state and changes only from an idempotent Planning
projection event tied to an Active Plan (NDS-BR-014). Nothing here queries
Procurement Planning: the firm D1 boundary makes the event the only channel,
and Planning publishes `NeedPlanningUsageChanged.v1` when an Active Plan starts
or stops representing an accepted Need version (§7.2).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.departmental_needs.constants import (
	ROLE_PROCUREMENT_PLANNER,
	USAGE_FULL,
	USAGE_NOT_INCLUDED,
	USAGE_NOT_PROCEEDING,
	USAGE_VALUES,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	in_scope,
	is_administrative,
)


def _projection(accepted_version: str) -> dict[str, Any] | None:
	if not accepted_version:
		return None
	row = frappe.db.get_value(
		"Need Planning Usage Projection",
		cstr(accepted_version),
		["name", "usage", "active_plan", "active_plan_item", "not_proceeding_reason", "source_event_id", "source_event_time"],
		as_dict=True,
	)
	return dict(row) if row else None


def planning_usage(need: str) -> str:
	"""The current accepted version's usage, defaulting to `Not included`.

	A Need with no projection has never been reported by Planning, which is
	exactly `Not included` — the §14.3 design-clock value for all four seeded
	Needs.
	"""
	accepted_version = frappe.db.get_value("Departmental Need", need, "current_accepted_version")
	if not accepted_version:
		return USAGE_NOT_INCLUDED
	row = _projection(accepted_version)
	return cstr(row["usage"]) if row else USAGE_NOT_INCLUDED


def planning_usage_detail(need: str, accepted_version: str = "") -> dict[str, Any]:
	"""Usage plus the Plan references that support **View Plan Item** (§4.7)."""
	version = cstr(accepted_version) or cstr(
		frappe.db.get_value("Departmental Need", need, "current_accepted_version") or ""
	)
	row = _projection(version) or {}
	return {
		"need": cstr(need),
		"accepted_version": version,
		"usage": cstr(row.get("usage") or USAGE_NOT_INCLUDED),
		"active_plan": cstr(row.get("active_plan") or ""),
		"active_plan_item": cstr(row.get("active_plan_item") or ""),
		"not_proceeding_reason": cstr(row.get("not_proceeding_reason") or ""),
		"source_event_id": cstr(row.get("source_event_id") or ""),
	}


def project_planning_usage(
	*,
	departmental_need: str,
	accepted_version: str,
	usage: str,
	source_event_id: str,
	source_event_time: str | None = None,
	active_plan: str = "",
	active_plan_item: str = "",
	not_proceeding_reason: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""§8.2 `project_need_planning_usage` — accept one ordered Planning event.

	Idempotent on `source_event_id` and ordered on `source_event_time`, so a
	replayed event is a no-op and a late-arriving older event cannot overwrite a
	newer projection (§4.7).
	"""
	principal = actor(user)
	# The event is Planning's to publish; §6 gives no other role this
	# authority. Procurement Planner is Site-wide (AUTH-ADR-001 v1.6 §4.4),
	# so the Organisation Unit passed to the scope check is immaterial.
	if not (
		in_scope(principal, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="")
		or is_administrative(principal)
	):
		fail("NDS_SCOPE_DENIED", "Only Procurement Planning may project Need planning usage.")
	usage_value = cstr(usage).strip()
	if usage_value not in USAGE_VALUES:
		fail("NDS_FIELD_REQUIRED", f"Usage must be one of: {', '.join(sorted(USAGE_VALUES))}.")
	reason_value = cstr(not_proceeding_reason).strip() if usage_value == USAGE_NOT_PROCEEDING else ""
	if usage_value == USAGE_NOT_PROCEEDING and not reason_value:
		fail("NDS_FIELD_REQUIRED", "A not-proceeding outcome carries the department's reason.")
	event_id = cstr(source_event_id).strip()
	if not event_id:
		fail("NDS_FIELD_REQUIRED", "A source event identifier is required.")
	need = cstr(departmental_need).strip()
	version = cstr(accepted_version).strip()
	if not frappe.db.exists("Departmental Need", need):
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	occurred = source_event_time or now_datetime()

	frappe.db.sql(
		"select name from `tabNeed Planning Usage Projection` where name=%s for update", version
	)
	existing = _projection(version)
	if existing:
		if cstr(existing["source_event_id"]) == event_id:
			return {"ok": True, "idempotent": True, **planning_usage_detail(need, version)}
		if existing["source_event_time"] and str(occurred) < str(existing["source_event_time"]):
			# Out-of-order delivery: the newer projection stands.
			return {"ok": True, "idempotent": True, "superseded": True, **planning_usage_detail(need, version)}
		doc = frappe.get_doc("Need Planning Usage Projection", version)
		doc.update(
			{
				"usage": usage_value,
				"active_plan": cstr(active_plan),
				"active_plan_item": cstr(active_plan_item),
				"not_proceeding_reason": reason_value,
				"source_event_id": event_id,
				"source_event_time": occurred,
			}
		)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "Need Planning Usage Projection",
				"departmental_need": need,
				"accepted_version": version,
				"usage": usage_value,
				"active_plan": cstr(active_plan),
				"active_plan_item": cstr(active_plan_item),
				"not_proceeding_reason": reason_value,
				"source_event_id": event_id,
				"source_event_time": occurred,
			}
		).insert(ignore_permissions=True)
	return {"ok": True, "idempotent": False, **planning_usage_detail(need, version)}


def is_actively_included(accepted_version: str) -> bool:
	"""Whether an Active Plan currently represents this exact version (NDS-BR-016)."""
	row = _projection(accepted_version)
	return bool(row and cstr(row["usage"]) == USAGE_FULL)
