# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Start guard (BOP-CHG-001 v0.10 §5 Ready to open, §7 BeginOpening, §8;
BOP-N02, BOP-N10, BOP-A02, BOP-A13).

Every refusal carries its reason code, named holder and a working fix; all
refusals are returned together (KT-STD-001 §3B.2). Nothing here reveals the
bid count: an empty and a nonempty box give the same answers before Start.

Two guard reason codes are not in §8 because §8 has no code for them; they
follow KT-STD-001 §11 conventions and use the boards' own words:
`BOP_ATTENDANCE_NOT_PUBLISHED` (board a3) and `BOP_ATTENDANCE_SERVICE_UNAVAILABLE`
(§10 branch (4))."""

from __future__ import annotations

from typing import Any

from frappe.utils import get_datetime

from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import (
	appointment, arrangements, availability, clock, custody_participation, errors, incidents, labels, people, presence,
)

SUPPORT = "Opening access support"
INCIDENT_CODES = {
	"Opening profile unavailable": "BOP_OPENING_PROFILE_UNAVAILABLE", "Credential unavailable": "BOP_CREDENTIAL_UNAVAILABLE",
	"Attendance service unavailable": "BOP_ATTENDANCE_SERVICE_UNAVAILABLE",
}


def _ao_fix(label: str, fix_id: str) -> dict[str, Any]:
	return ns.fix(label, responsibility=people.ACCOUNTING_OFFICER, kind=ns.FIX_ROUTE, fix_id=fix_id, person=", ".join(people.full_name(u) for u in people.accounting_officers()))


def _problem_fix(incident_id: str = "") -> dict[str, Any]:
	return ns.fix("View problem details", responsibility=SUPPORT, kind=ns.FIX_FOCUS, fix_id="view_problem_details", target=incident_id)


def start_guards(doc) -> list[dict[str, Any]]:
	"""Every guard on Start, in the §8 order."""
	out: list[dict[str, Any]] = []
	now = clock.now()
	if now < get_datetime(doc.effective_deadline):
		out.append(ns.guard(False, reason_code="BOP_DEADLINE_NOT_REACHED", message=errors.message("BOP_DEADLINE_NOT_REACHED", deadline=labels.when(doc.effective_deadline)),
			fixes=[ns.fix("Wait for submissions to close", responsibility="System", kind=ns.FIX_TEXT, fix_id="wait_for_close")]))
		return out
	if not doc.manifest_digest:
		out.append(ns.guard(False, reason_code="BOP_CLOSE_MANIFEST_UNAVAILABLE", message=errors.message("BOP_CLOSE_MANIFEST_UNAVAILABLE"), fixes=[_problem_fix()]))
	roster = appointment.roster(doc.name)
	if len(roster) < 3:
		out.append(ns.guard(False, reason_code="BOP_COMMITTEE_INCOMPLETE", message=errors.message("BOP_COMMITTEE_INCOMPLETE"), fixes=[_ao_fix("Appoint committee", "appoint")]))
	elif not any(m["is_independent"] for m in roster):
		out.append(ns.guard(False, reason_code="BOP_INDEPENDENT_MEMBER_REQUIRED", message=errors.message("BOP_INDEPENDENT_MEMBER_REQUIRED"),
			fixes=[_ao_fix("Add an independent third member", "appoint")]))
	if not arrangements.current(doc.name):
		out.append(ns.guard(False, reason_code="BOP_ATTENDANCE_NOT_PUBLISHED", message="The opening cannot start until attendance details are published.",
			fixes=[_ao_fix("Publish how to attend", "publish")]))
	present = presence.present_members(doc.name)
	for member in roster:
		if member["member_user"] not in present:
			out.append(ns.guard(False, reason_code="BOP_MEMBER_ABSENT", message=errors.message("BOP_MEMBER_ABSENT", name=member["full_name"]),
				figures={"member": member["member_user"]},
				fixes=[ns.fix(f"Notify {member['full_name']}", responsibility=member["committee_role"], kind=ns.FIX_COMMAND, fix_id="notify_member",
					person=member["full_name"], target=member["member_user"])]))
	verdict = availability.get_opening_availability()
	if not verdict["available"]:
		out.append(ns.guard(False, reason_code=verdict["code"], message=verdict["message"], fixes=[_problem_fix()]))
	for row in incidents.open_incidents(doc.name):
		code = INCIDENT_CODES.get(row.incident_type)
		if code and not any(g["reason_code"] == code for g in out):
			message = errors.message(code) if code.startswith("BOP_") and code in errors.ERROR_CODES else "The public attendance service is unavailable."
			out.append(ns.guard(False, reason_code=code, message=message, figures={"incident": row.incident_id}, fixes=[_problem_fix(row.incident_id)]))
	if not availability.attendance_channel_available() and not any(g["reason_code"] == "BOP_ATTENDANCE_SERVICE_UNAVAILABLE" for g in out):
		out.append(ns.guard(False, reason_code="BOP_ATTENDANCE_SERVICE_UNAVAILABLE", message="The public attendance service is unavailable.", fixes=[_problem_fix()]))
	if doc.manifest_digest and len(present) == len(roster) and roster and not custody_participation.valid(doc) and not out:
		out.append(ns.guard(False, reason_code="BOP_CREDENTIAL_UNAVAILABLE", message=errors.message("BOP_CREDENTIAL_UNAVAILABLE"), fixes=[_problem_fix()]))
	return out


def start_guard(doc) -> dict[str, Any]:
	guards = start_guards(doc)
	return ns.combine(*guards) if guards else ns.allowed()
