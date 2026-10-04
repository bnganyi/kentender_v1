# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AppointOpeningCommittee (BOP-CHG-001 v0.10 §4 Appointment, §6, §7, §10.2;
BOP-A02, BOP-A17).

The Accounting Officer names at least three eligible members: one chair,
one recorder (the same person may be both), and at least one member who is
demonstrably independent of processing this Tender. A later appointment
supersedes the earlier one with history; nothing is overwritten. An
independent member is excluded from this Tender's later evaluation (the
conservative first-product policy). No Proceedings consumer (§7.1)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_opening.services import clock, errors, people, records
from kentender_procurement.tenders.services import opening_seam

APPOINTMENT = "Opening Committee Appointment"
ROLES = ("Chair and recorder", "Chair", "Recorder", "Member", "Independent member")
CHAIR_ROLES, RECORDER_ROLES = ("Chair and recorder", "Chair"), ("Chair and recorder", "Recorder")


def current(case: str) -> Any | None:
	name = frappe.db.get_value(APPOINTMENT, {"opening_case": case, "status": "Active"}, "name")
	return frappe.get_doc(APPOINTMENT, name) if name else None


def roster(case: str) -> list[dict[str, Any]]:
	doc = current(case)
	return [{f: m.get(f) for f in ("member_user", "full_name", "designation", "committee_role", "is_chair", "is_recorder", "is_independent")} for m in doc.members] if doc else []


def roster_digest(case: str) -> str:
	return records.digest(sorted((m["member_user"], m["committee_role"]) for m in roster(case)))


def member(case: str, user: str) -> dict[str, Any] | None:
	return next((m for m in roster(case) if m["member_user"] == user), None)


def chair(case: str) -> dict[str, Any] | None:
	return next((m for m in roster(case) if m["is_chair"]), None)


def recorder(case: str) -> dict[str, Any] | None:
	return next((m for m in roster(case) if m["is_recorder"]), None)


def is_excluded_from_evaluation(tender: str, user: str) -> bool:
	"""BOP-A17: the Evaluation appointment guard asks this (FU-BOP-11)."""
	case = records.case_for(tender)
	if not case:
		return False
	appointments = frappe.get_all(APPOINTMENT, filters={"opening_case": case}, pluck="name")
	return bool(appointments) and bool(frappe.db.exists("Opening Committee Member", {"parent": ("in", appointments), "member_user": user, "excluded_from_evaluation": 1}))


def validate(tender: str, members: list[dict[str, Any]]) -> dict[str, Any] | None:
	"""A correctable appointment is returned as data with its guard (§10.2 INCOMPLETE)."""
	from kentender_core.services import next_step as ns

	field_errors: dict[str, str] = {}
	seen: set[str] = set()
	for row in members:
		user, role = cstr(row.get("user")), cstr(row.get("committee_role"))
		if user in seen:
			field_errors[user] = "This person is already on the committee."
		seen.add(user)
		if role not in ROLES:
			field_errors[user] = "Choose the person's role on the committee."
		elif not people.eligibility(user)[0]:
			field_errors[user] = "This person cannot be appointed to the opening committee."
	roles = [cstr(r.get("committee_role")) for r in members]
	incomplete = field_errors or sum(r in CHAIR_ROLES for r in roles) != 1 or sum(r in RECORDER_ROLES for r in roles) != 1
	processing = opening_seam.processing_actors(tender)
	independent = [cstr(r["user"]) for r in members if r.get("committee_role") == "Independent member"]
	# Board a2: a draft with no independent member is told that first; "at
	# least three" applies once the independent member is there.
	if incomplete or (len(members) < 3 and independent):
		guard = ns.guard(False, reason_code="BOP_COMMITTEE_INCOMPLETE", message=errors.message("BOP_COMMITTEE_INCOMPLETE"),
			fixes=[ns.fix("Add member", responsibility=people.ACCOUNTING_OFFICER, kind=ns.FIX_FOCUS, fix_id="add_member", target="committee", primary=True)])
		return {"ok": False, "code": "BOP_COMMITTEE_INCOMPLETE", "message": guard["message"], "errors": field_errors, "guard": guard}
	if not independent or any(u in processing for u in independent):
		guard = ns.guard(False, reason_code="BOP_INDEPENDENT_MEMBER_REQUIRED", headline="The opening committee needs an independent third member",
			message=errors.message("BOP_INDEPENDENT_MEMBER_REQUIRED"),
			fixes=[ns.fix("Add an independent third member", responsibility=people.ACCOUNTING_OFFICER, kind=ns.FIX_FOCUS, fix_id="add_member", target="committee", primary=True)])
		return {"ok": False, "code": "BOP_INDEPENDENT_MEMBER_REQUIRED", "message": guard["message"], "errors": {u: "Involved in processing this Tender." for u in independent if u in processing}, "guard": guard}
	return None


def appoint_opening_committee(*, tender: str, members: list[dict[str, Any]], expected_version: int, idempotency_key: str, user: str, reason: str = "") -> dict[str, Any]:
	if not people.holds(user, people.ACCOUNTING_OFFICER):
		raise frappe.DoesNotExistError("Not found")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		records.check_version(doc, expected_version)
		if doc.state not in ("Awaiting deadline", "Ready to open", "Interrupted"):
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		if doc.state == "Interrupted" and not cstr(reason).strip():
			return {"ok": False, "code": "BOP_COMMITTEE_INCOMPLETE", "errors": {"reason": "Give the reason for appointing a replacement."}}
		invalid = validate(tender, members)
		if invalid:
			return invalid
		previous = current(doc.name)
		at = clock.now()
		number = frappe.db.count(APPOINTMENT, {"opening_case": doc.name}) + 1
		appointment = frappe.get_doc({
			"doctype": APPOINTMENT, "appointment_id": f"{doc.opening_id}-APT-{number:02d}", "opening_case": doc.name, "version_number": number, "appointed_by": user,
			"appointed_at": at, "status": "Active", "supersedes_appointment": previous.name if previous else "", "reason": cstr(reason).strip(),
		})
		for row in members:
			role = row["committee_role"]
			appointment.append("members", {
				"member_user": row["user"], "full_name": people.full_name(row["user"]), "designation": people.eligibility(row["user"])[1], "committee_role": role,
				"is_chair": int(role in CHAIR_ROLES), "is_recorder": int(role in RECORDER_ROLES), "is_independent": int(role == "Independent member"),
				"independence_basis": "Not involved in processing this Tender and will not evaluate it" if role == "Independent member" else "",
				"excluded_from_evaluation": int(role == "Independent member"),
			})
		records.insert(appointment)
		if previous:
			previous.status = "Superseded"
			records.save(previous)
		from kentender_procurement.bid_opening.services import custody_participation

		custody_participation.mark_stale(doc.name)
		if doc.state == "Interrupted":
			# A lawful successor joins from the point of resumption; earlier events keep
			# their actual roster (BOP-CHG-001 v0.10 §5, §7.1 "Roster and target scope").
			from kentender_procurement.bid_opening.services import prc
			from kentender_procurement.proceedings.services import lifecycle

			lifecycle.add_roster_segment(**prc.ref(doc.name), roster=[{"member_user": m.member_user, "full_name": m.full_name, "designation": m.designation,
				"committee_capacity": m.committee_role, "appointment_reference": appointment.name} for m in appointment.members], reason=cstr(reason).strip(),
				idempotency_key=prc.key(idempotency_key, "roster"), actor=user)
		records.bump(doc, current_appointment=appointment.name)
		from kentender_procurement.bid_opening.services import labels, notify

		notify.tell_members(doc, [m.member_user for m in appointment.members], subject=f"You are on the opening committee for {doc.tender_reference}",
			message=f"Join the opening from {labels.when(arrangements_join_opens(doc))}. The opening is at {labels.when(doc.effective_deadline)}.",
			event_type="Opening committee appointment", key=f"appointed:{appointment.name}")
		return records.summary(doc, appointment=appointment.name, appointed_at=str(at))

	return records.command("AppointOpeningCommittee", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"members": members, "expected_version": expected_version, "reason": reason}, body=body)


def candidates(tender: str) -> list[dict[str, Any]]:
	"""Who the Accounting Officer can appoint (board a1 "Eligibility"): enabled
	internal people holding an active KenTender responsibility, with their
	designation and whether they processed this Tender (so cannot be the
	independent member). Holding a responsibility is not an appointment."""
	processing = opening_seam.processing_actors(tender)
	users = frappe.get_all("User Responsibility Assignment", filters={"status": "Enabled"}, pluck="user", distinct=True)
	out = []
	for user in sorted(set(users)):
		eligible, designation = people.eligibility(user)
		if eligible:
			out.append({"user": user, "full_name": people.full_name(user), "designation": designation, "involved": user in processing})
	return sorted(out, key=lambda r: r["full_name"])


def arrangements_join_opens(doc):
	from kentender_procurement.bid_opening.services import arrangements

	return arrangements.join_opens_at(doc.effective_deadline) or doc.effective_deadline
