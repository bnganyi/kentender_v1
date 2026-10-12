# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A committee member's department (EVL-CHG-001 v0.7 §3, §6, §7.2
`CompleteMemberDepartment`; AUTH-ADR-001 v1.12 §4.8).

The department is the person's staff **home organisation unit** — where they
work — read through the published core service and recorded on the
appointment as a snapshot when the action commits. It is display information:
it plays no part in eligibility, and a person with no home unit is appointed
with the department **Not recorded** (stored blank).

When a home unit is later recorded for someone whose current appointment shows
Not recorded, the department is completed exactly once, by the consumer of the
published `StaffHomeUnitChanged` event. A recorded department is never
replaced, a former member's record and a superseded appointment are never
completed, and no task is created for the administrator (Administrator and
System Manager hold no My Work items, KT-STD-001 §3A.6)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import staff_home_unit
from kentender_procurement.bid_evaluation.services import records, roster

NOT_RECORDED = "Not recorded"


def department_of(user: str) -> str:
	"""The unit's current name, or "" when no home unit is recorded."""
	return cstr(staff_home_unit.get_staff_home_organisation_unit(user)["unit_name"])


def display(department: str | None) -> str:
	return cstr(department).strip() or NOT_RECORDED


def on_home_unit_changed(event: dict[str, Any]) -> None:
	"""CompleteMemberDepartment — consume `StaffHomeUnitChanged`.

	Acts only when a unit has been recorded (a clearing completes nothing) and
	only on a current member of a current appointment whose department is
	blank. Idempotent: a replay finds nothing blank."""
	user, after = cstr(event.get("user")), cstr(event.get("after"))
	if not user or not after:
		return
	name = cstr(event.get("after_name")) or cstr(frappe.db.get_value("Organisation Unit", after, "unit_name"))
	if not name:
		return
	for appointment in frappe.get_all(roster.APPOINTMENT, filters={"status": "Current"}, pluck="name"):
		doc = frappe.get_doc(roster.APPOINTMENT, appointment)
		changed = False
		for member in doc.members:
			if member.member_user == user and member.status == "Current" and not cstr(member.department).strip():
				member.department = name
				member.department_recorded_by = cstr(event.get("actor")) or None
				member.department_recorded_at = event.get("instant")
				changed = True
		if changed:
			records.save(doc)
