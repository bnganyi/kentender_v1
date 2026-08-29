"""Needs context and intake window (NDS-CHG-001 v1.1 §4.1, §5.4, §8.1, §8.2).

The intake window is a real `Needs Intake Window` record for one PE/FY, and its
`Scheduled` / `Open` / `Closed` state is derived at read time from the stored
instants — never stored (§4.1). Boundaries are inclusive on both ends
(NDS-AC-003), so a command at exactly `opens_at` or exactly `closes_at`
succeeds.

Only initial creation and initial submission are gated on an Open window
(NDS-BR-002). A correction of a version submitted before close may be
resubmitted after close, and an accepted successor may be proposed while the
PE/FY context remains active (NDS-BR-003).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate, now_datetime, nowdate

from kentender_procurement.departmental_needs.constants import (
	INTAKE_CLOSED,
	INTAKE_NOT_CONFIGURED,
	INTAKE_OPEN,
	INTAKE_SCHEDULED,
	ROLE_PROCUREMENT_PLANNER,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	creation_contexts,
	has_role,
	is_administrative,
	require_intake_window_command,
)


def _financial_year_row(financial_year: str) -> dict[str, Any]:
	"""One `Financial Year` record, normalised.

	Departmental Needs scope is the governed `Financial Year` catalogue — the
	same doctype the Need's Link field, the `Financial Year` User Permission
	dimension and the reference generator all use. It is deliberately *not*
	ERPNext's `Fiscal Year`, whose identifiers (`2027/28`) belong to a different
	space from the governed ones (`FY-2027-2028`).
	"""
	wanted = cstr(financial_year).strip()
	row = frappe.db.get_value(
		"Financial Year",
		wanted,
		["name", "label", "start_year", "start_date", "end_date", "record_status"],
		as_dict=True,
	)
	if not row:
		fail("NDS_CONTEXT_REQUIRED", f"Financial year {wanted or '(blank)'} is not configured.")
	today = getdate(nowdate())
	return {
		"id": row.name,
		"label": cstr(row.label or row.name),
		"start_year": row.start_year,
		"start_date": str(row.start_date),
		"end_date": str(row.end_date),
		"record_status": cstr(row.record_status),
		"is_current": getdate(row.start_date) <= today <= getdate(row.end_date),
		"is_future": getdate(row.start_date) > today,
		"is_past": getdate(row.end_date) < today,
	}


def selectable_financial_year(financial_year: str) -> dict:
	"""The FY must be an available, unexpired context (§5.4 NDS-BR-001).

	A *future* target year is the normal case, not an error: §14.1's intake
	window collects FY 2027/28 Needs between 1 Sep and 25 Nov 2026. What governs
	*when* a Need may be created is the intake window (NDS-BR-002), not whether
	the target year has started. Only a missing, non-Available or expired year
	fails closed, with the §9 `NDS_CONTEXT_REQUIRED` code rather than an
	invented one.
	"""
	row = _financial_year_row(financial_year)
	if row["record_status"] != "Available":
		fail("NDS_CONTEXT_REQUIRED", "That financial year is not available for Departmental Needs.")
	if row["is_past"]:
		fail("NDS_CONTEXT_REQUIRED", "That financial year is closed for Departmental Needs.")
	return row


# --- §4.1 intake window ----------------------------------------------------


def _may_maintain(user: str | None = None) -> bool:
	"""§6/NDS-AC-043 — only the Procurement Planner maintains the window.

	Reported on the read so NDS-UI-08 can withhold the Save control from a user
	who reaches the route another way. This is presentation, not the control:
	`save_intake_window` refuses on its own with NDS_SCOPE_DENIED, and §17
	forbids treating a hidden button as authorization. Offering a command the
	role does not hold is the same defect fixed for Create need (NDS-807).
	"""
	principal = actor(user)
	return has_role(principal, ROLE_PROCUREMENT_PLANNER) or is_administrative(principal)


def intake_window(
	procuring_entity: str, financial_year: str, *, at=None, user: str | None = None
) -> dict[str, Any]:
	"""The PE/FY window and its derived state at `at` (default: now).

	Returns a result for every input, including a missing window, so that read
	surfaces can render an honest "not configured" state without an exception.
	"""
	can_maintain = _may_maintain(user)
	pe, fy = cstr(procuring_entity).strip(), cstr(financial_year).strip()
	row = frappe.db.get_value(
		"Needs Intake Window",
		{"procuring_entity": pe, "financial_year": fy},
		["name", "opens_at", "closes_at", "record_version"],
		as_dict=True,
	)
	if not row:
		return {
			"procuring_entity": pe,
			"financial_year": fy,
			"configured": False,
			"state": INTAKE_NOT_CONFIGURED,
			"window": "",
			"opens_at": "",
			"closes_at": "",
			"record_version": 0,
			"can_maintain": can_maintain,
		}
	moment = get_datetime(at) if at else now_datetime()
	opens_at, closes_at = get_datetime(row.opens_at), get_datetime(row.closes_at)
	# Inclusive on both boundaries (NDS-AC-003).
	if moment < opens_at:
		state = INTAKE_SCHEDULED
	elif moment <= closes_at:
		state = INTAKE_OPEN
	else:
		state = INTAKE_CLOSED
	return {
		"procuring_entity": pe,
		"financial_year": fy,
		"configured": True,
		"state": state,
		"window": row.name,
		"opens_at": str(row.opens_at),
		"closes_at": str(row.closes_at),
		"record_version": int(row.record_version or 0),
		"can_maintain": can_maintain,
	}


def require_open_intake(procuring_entity: str, financial_year: str, *, at=None) -> dict[str, Any]:
	"""Gate initial creation and initial submission on an Open window (NDS-BR-002)."""
	window = intake_window(procuring_entity, financial_year, at=at)
	if window["state"] != INTAKE_OPEN:
		fail(
			"NDS_INTAKE_NOT_OPEN",
			"The Departmental Needs intake window for this entity and financial year is not open.",
		)
	return window


def save_intake_window(
	*,
	procuring_entity: str,
	financial_year: str,
	opens_at: str,
	closes_at: str,
	expected_version: int = 0,
	user: str | None = None,
) -> dict[str, Any]:
	"""§8.2 `save_needs_intake_window` — one window per PE/FY, Planner-only.

	Ordering and single-window uniqueness are enforced by the DocType controller,
	so this command owns authorization and the optimistic-lock check only.
	"""
	principal = actor(user)
	pe, fy = cstr(procuring_entity).strip(), cstr(financial_year).strip()
	require_intake_window_command(principal, procuring_entity=pe, financial_year=fy)
	existing = frappe.db.get_value(
		"Needs Intake Window", {"procuring_entity": pe, "financial_year": fy}, "name"
	)
	if existing:
		rows = frappe.db.sql(
			"select name, record_version from `tabNeeds Intake Window` where name=%s for update",
			existing,
			as_dict=True,
		)
		if cstr(rows[0].record_version) != cstr(expected_version):
			fail(
				"NDS_STALE_WRITE",
				"This intake window changed after it was opened. Reload and try again.",
			)
		doc = frappe.get_doc("Needs Intake Window", existing)
		doc.opens_at = opens_at
		doc.closes_at = closes_at
		doc.record_version = int(doc.record_version or 0) + 1
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Needs Intake Window",
				"needs_intake_window_id": f"NDS-IW-{pe}-{fy}",
				"procuring_entity": pe,
				"financial_year": fy,
				"opens_at": opens_at,
				"closes_at": closes_at,
				"record_version": 1,
			}
		).insert(ignore_permissions=True)
	return {"ok": True, **intake_window(pe, fy)}


# --- §8.1 resolve_needs_contexts -------------------------------------------


def selectable_financial_years() -> list[dict[str, Any]]:
	"""Every Available, unexpired year, including future ones (§8.1)."""
	rows = frappe.get_all(
		"Financial Year",
		filters={"record_status": "Available", "end_date": (">=", nowdate())},
		pluck="name",
		order_by="start_year asc",
		limit_page_length=0,
	)
	return [_financial_year_row(name) for name in rows]


def resolve_creation_context(*, user: str | None = None) -> dict:
	"""Exact eligible PE/OU/FY contexts and their intake state (§8.1)."""
	contexts = creation_contexts(user)
	financial_years = selectable_financial_years()
	entities = sorted({row["procuring_entity"] for row in contexts})
	intake = [
		intake_window(entity, cstr(fy["id"]))
		for entity in entities
		for fy in financial_years
	]
	return {
		"ok": bool(contexts),
		"outcome": "READY" if contexts else "NO_ACTIVE_OPERATIONAL_ASSIGNMENT",
		"contexts": contexts,
		"requires_selection": len(contexts) > 1,
		"financial_years": financial_years,
		"intake": intake,
	}
