# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.12 §4.8 / CFG-CHG-002 v0.19 §4.10A, §7.1–7.2, §12 — the
staff home organisation unit.

A home unit records where a person works. It is display information, never
authority: nothing here reads or writes a User Responsibility Assignment, a
scope or a Frappe Role, and no authorization path reads the field.

- `set_staff_home_organisation_unit` (SetStaffHomeOrganisationUnit):
  Administrator or System Manager; one Active Organisation Unit or none;
  checked against the staff record's own modification stamp; idempotent by
  key; one audit event and one published `StaffHomeUnitChanged` per change; an
  unchanged value appends and publishes nothing.
- `list_staff_home_units` (ListStaffHomeUnits): the setup register.
- `get_staff_home_organisation_unit` (GetStaffHomeOrganisationUnit): the
  contracted read for consumers — Recorded or Not recorded, the unit's
  current name and its Active or Inactive status, and nothing else.

Consumers subscribe to the change through the `kt_staff_home_unit_changed`
hook, so this app depends on no downstream app. Handlers run in the same
transaction: a handler that raises fails the command with no partial write.
"""

from __future__ import annotations

import uuid
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.configuration_errors import fail_cfg
from kentender_core.services.reference_data_idempotency import request_payload, run_idempotent
from kentender_core.services.site_configuration import require_configuration_administrator

FIELD = "kt_home_organisation_unit"
HOOK = "kt_staff_home_unit_changed"
NOT_STAFF = ("Administrator", "Guest")
NOT_RECORDED = "Not recorded"
RECORDED = "Recorded"


def _handlers() -> list:
	return [frappe.get_attr(path) for path in frappe.get_hooks(HOOK)]


def _is_staff(user: str) -> bool:
	row = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
	return bool(row and row.enabled and row.user_type == "System User" and user not in NOT_STAFF)


def _unit_view(unit: str | None) -> dict[str, Any]:
	if not unit:
		return {"organisation_unit": "", "unit_name": "", "unit_status": ""}
	row = frappe.db.get_value("Organisation Unit", unit, ["unit_name", "status"], as_dict=True)
	if not row:
		return {"organisation_unit": "", "unit_name": "", "unit_status": ""}
	return {"organisation_unit": unit, "unit_name": cstr(row.unit_name), "unit_status": cstr(row.status)}


def _token(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "modified"))


def _row(user: str, full_name: str, unit: str | None) -> dict[str, Any]:
	view = _unit_view(unit)
	return {"user": user, "full_name": cstr(full_name), "state": RECORDED if view["organisation_unit"] else NOT_RECORDED, **view, "token": _token(user)}


def get_staff_home_organisation_unit(user: str) -> dict[str, Any]:
	"""GetStaffHomeOrganisationUnit — the person's home unit and nothing else.

	A consumer calls this in-process; it grants no authority and exposes no
	responsibility, role or scope."""
	if not frappe.db.exists("User", user):
		return {"user": user, "state": NOT_RECORDED, "organisation_unit": "", "unit_name": "", "unit_status": "", "token": ""}
	row = frappe.db.get_value("User", user, ["full_name", FIELD], as_dict=True)
	return _row(user, row.full_name, row.get(FIELD))


def list_staff_home_units(*, search: str = "", not_recorded: bool = False, page: int = 1, page_length: int = 50) -> dict[str, Any]:
	"""ListStaffHomeUnits — enabled staff accounts, one server predicate for rows and count."""
	require_configuration_administrator()
	filters: dict[str, Any] = {"enabled": 1, "user_type": "System User", "name": ("not in", NOT_STAFF)}
	if not_recorded:
		filters[FIELD] = ("is", "not set")
	or_filters = None
	if cstr(search).strip():
		like = f"%{cstr(search).strip()}%"
		or_filters = {"full_name": ("like", like), "name": ("like", like)}
	total = len(frappe.get_all("User", filters=filters, or_filters=or_filters, pluck="name", limit_page_length=0))
	page, page_length = max(int(page or 1), 1), min(max(int(page_length or 50), 1), 1000)
	users = frappe.get_all("User", filters=filters, or_filters=or_filters, fields=["name", "full_name", FIELD], order_by="full_name asc, name asc",
		limit_start=(page - 1) * page_length, limit_page_length=page_length)
	return {"rows": [_row(u.name, u.full_name, u.get(FIELD)) for u in users], "total": total, "page": page, "page_length": page_length}


def set_staff_home_organisation_unit(*, user: str, organisation_unit: str = "", expected_token: str | None = None, idempotency_key: str = "") -> dict[str, Any]:
	"""SetStaffHomeOrganisationUnit — set, change or clear (blank unit) one person's home unit."""
	request = request_payload(locals())
	actor = require_configuration_administrator()
	unit = cstr(organisation_unit).strip()

	def _do() -> dict[str, Any]:
		if not _is_staff(user):
			fail_cfg("CFG_HOME_UNIT_INVALID")
		if unit and cstr(frappe.db.get_value("Organisation Unit", unit, "status")) != "Active":
			fail_cfg("CFG_HOME_UNIT_INVALID")
		if cstr(expected_token) != _token(user):
			fail_cfg("CFG_VERSION_CONFLICT")
		before = cstr(frappe.db.get_value("User", user, FIELD))
		if before == unit:
			return {"ok": True, "changed": False, "user": user, **_unit_view(unit), "token": _token(user)}
		frappe.db.set_value("User", user, FIELD, unit or None)
		after_view = _unit_view(unit)
		before_view = _unit_view(before)
		instant = now_datetime()
		command_id = uuid.uuid4().hex
		log_audit_event(
			event_type="site_configuration", document_type="User", document_name=user, action="set_staff_home_organisation_unit", performed_by=actor,
			metadata={"before": {"organisation_unit": before, "unit_name": before_view["unit_name"]}, "after": {"organisation_unit": unit, "unit_name": after_view["unit_name"]},
				"command_id": command_id},
		)
		event = {"event": "StaffHomeUnitChanged", "user": user, "before": before, "after": unit, "before_name": before_view["unit_name"], "after_name": after_view["unit_name"],
			"actor": actor, "instant": instant, "command_id": command_id}
		for handler in _handlers():
			handler(event)
		return {"ok": True, "changed": True, "user": user, **after_view, "token": _token(user)}

	return run_idempotent(idempotency_key, "User", user, "set_staff_home_organisation_unit", _do, payload=request)
