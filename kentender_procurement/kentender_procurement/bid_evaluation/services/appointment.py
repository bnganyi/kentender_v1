# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AppointEvaluationCommittee and ReplaceEvaluationMember (EVL-CHG-001 v0.4 §3,
§7.2; tracker EVL4-403, EVL4-404; boards D02-A, D02-REPLACE, D02-INELIGIBLE).

The Accounting Officer appoints 3–5 members with recorded designation,
department and capacity (one Chair), under an appointment reference. The
independent member of the same tender's opening cannot evaluate it (BOP
v0.10 product policy, BOP-A17). A replacement is a reasoned appointment, not
a chair shortcut: it keeps the former membership and history, the incoming
member declares and reviews the whole current record, and a report being
signed is withdrawn for a new version signed by the current roster. Every
ineligible person is reported together, beside that person, with the
specific reason; nothing is appointed in part."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_evaluation.services import clock, guards, notify, people, prc, records, roster
from kentender_procurement.bid_evaluation.services.errors import Guards, fail

APPOINTMENT = roster.APPOINTMENT
CAPACITIES = ("Chair", "Member")
REASONS = {
	"not_internal": "{name} does not hold an active KenTender responsibility.",
	"opening_independent": "{name} was the independent member of this tender's bid opening.",
	"declared_conflict": "{name} has an unresolved declared conflict for this tender.",
	"duplicate": "{name} is listed more than once.",
	"already_member": "{name} is already on this committee.",
}


def _require_ao(user: str) -> None:
	if not people.holds(user, people.ACCOUNTING_OFFICER):
		raise frappe.DoesNotExistError("Not found")


def _ineligibility(doc, user: str) -> str | None:
	from kentender_procurement.bid_opening.services import evaluation_seam as opening

	ok, _designation = people.internal(user)
	if not ok:
		return "not_internal"
	if opening.is_excluded_from_evaluation(doc.tender, user):
		return "opening_independent"
	if frappe.db.exists(roster.DECLARATION, {"evaluation_case": doc.name, "member_user": user, "status": "Current", "choice": "Declare a conflict"}):
		return "declared_conflict"
	return None


def _reason(code: str, user: str) -> str:
	return REASONS[code].format(name=people.full_name(user))


def _rows(doc, members: list[dict[str, Any]], checks: Guards) -> list[dict[str, Any]]:
	rows, seen = [], set()
	for m in members:
		user = cstr(m.get("user")).strip()
		fields = {f: "Required." for f in ("user", "department", "capacity") if not cstr(m.get(f)).strip()}
		if cstr(m.get("capacity")) and m.get("capacity") not in CAPACITIES:
			fields["capacity"] = "Choose Chair or Member."
		if fields:
			checks.add("EVL_MEMBER_INELIGIBLE", person=user, fields=fields)
			continue
		code = "duplicate" if user in seen else _ineligibility(doc, user)
		seen.add(user)
		if code:
			checks.add("EVL_MEMBER_INELIGIBLE", person=user, person_name=people.full_name(user), reason=code, explanation=_reason(code, user))
			continue
		_ok, designation = people.internal(user)
		rows.append({"member_user": user, "full_name": people.full_name(user), "department": cstr(m["department"]).strip(),
			"designation": cstr(m.get("designation") or designation), "capacity": m["capacity"], "status": "Current"})
	return rows


def _size(rows: list[dict[str, Any]], checks: Guards) -> None:
	if not roster.MIN_MEMBERS <= len(rows) <= roster.MAX_MEMBERS:
		checks.add("EVL_MEMBER_INELIGIBLE", reason="committee_size", explanation=f"Appoint {roster.MIN_MEMBERS} to {roster.MAX_MEMBERS} members.")
	if sum(1 for r in rows if r["capacity"] == "Chair") != 1:
		checks.add("EVL_MEMBER_INELIGIBLE", reason="one_chair", explanation="Appoint exactly one Chair.")


def appoint_committee(*, tender: str, members: list[dict[str, Any]], appointment_reference: str, expected_version: int, idempotency_key: str,
		user: str) -> dict[str, Any]:
	_require_ao(user)
	payload = {"members": members, "appointment_reference": appointment_reference, "expected_version": expected_version}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		checks = guards.open_case(doc, "appointments")
		checks.raise_if_any()
		records.check_version(doc, expected_version)
		if roster.current_appointment(doc.name):
			fail("EVL_VERSION_CONFLICT", {"reason": "already_appointed"})
		if not cstr(appointment_reference).strip():
			checks.add("EVL_MEMBER_INELIGIBLE", fields={"appointment_reference": "Enter the appointment reference."})
		rows = _rows(doc, members, checks)
		if not checks:
			_size(rows, checks)
		checks.raise_if_any()
		appointment = frappe.get_doc({
			"doctype": APPOINTMENT, "appointment_id": f"{doc.name}-APT-01", "evaluation_case": doc.name, "version_number": 1,
			"appointment_reference": cstr(appointment_reference).strip(), "change_kind": "Initial", "appointed_by": user, "appointed_at": clock.now(), "status": "Current",
		})
		for row in rows:
			appointment.append("members", row)
		records.insert(appointment)
		event = prc.roster(doc, roster.prc_roster(doc.name), "Committee appointed", owner_event_id=f"appointment:{appointment.name}", idempotency_key=idempotency_key)
		records.bump(doc, current_appointment=appointment.name, last_committed_event=event)
		notify.tell(doc, [r["member_user"] for r in rows], subject=f"Declare interests for {doc.tender_reference}",
			message=f"You are appointed to evaluate {doc.tender_reference}. Declare any conflict before viewing bids.", key=f"declare-{appointment.name}")
		return records.summary(doc, appointment=appointment.name, members=[r["member_user"] for r in rows])

	return records.command("AppointEvaluationCommittee", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def replace_member(*, tender: str, outgoing: str, incoming: dict[str, Any], appointment_reference: str, reason: str, expected_version: int,
		idempotency_key: str, user: str) -> dict[str, Any]:
	_require_ao(user)
	payload = {"outgoing": outgoing, "incoming": incoming, "appointment_reference": appointment_reference, "reason": reason, "expected_version": expected_version}

	def body() -> dict[str, Any]:
		from kentender_procurement.bid_evaluation.services import lifecycle

		doc = records.lock(tender)
		checks = guards.open_case(doc, "appointments")
		checks.raise_if_any()
		records.check_version(doc, expected_version)
		current = roster.current_appointment(doc.name)
		members = roster.current_members(doc.name)
		if not current or outgoing not in [m["member_user"] for m in members]:
			fail("EVL_VERSION_CONFLICT", {"reason": "not_a_current_member"})
		fields = {f: "Required." for f, v in (("appointment_reference", appointment_reference), ("reason", reason)) if not cstr(v).strip()}
		if fields:
			checks.add("EVL_MEMBER_INELIGIBLE", fields=fields)
		incoming_user = cstr(incoming.get("user")).strip()
		new_rows: list[dict[str, Any]] = []
		if incoming_user in [m["member_user"] for m in members]:
			code = "declared_conflict" if roster.status(doc.name, incoming_user)["conflict"] else "already_member"
			checks.add("EVL_MEMBER_INELIGIBLE", person=incoming_user, person_name=people.full_name(incoming_user), reason=code,
				explanation=_reason(code, incoming_user))
		else:
			new_rows = _rows(doc, [{**incoming, "capacity": incoming.get("capacity") or next(m["capacity"] for m in members if m["member_user"] == outgoing)}], checks)
		checks.raise_if_any()
		incoming_row = new_rows[0]
		number = cint(current.version_number) + 1
		successor = frappe.get_doc({
			"doctype": APPOINTMENT, "appointment_id": f"{doc.name}-APT-{number:02d}", "evaluation_case": doc.name, "version_number": number,
			"appointment_reference": cstr(appointment_reference).strip(), "change_kind": "Replacement", "reason": cstr(reason).strip(), "appointed_by": user,
			"appointed_at": clock.now(), "status": "Current", "supersedes_appointment": current.name,
		})
		for m in members:
			if m["member_user"] == outgoing:
				successor.append("members", {**m, "status": "Replaced", "replaced_by_user": incoming_user, "change_reason": cstr(reason).strip()})
			else:
				successor.append("members", m)
		successor.append("members", incoming_row)
		current.status = "Superseded"
		records.save(current)
		records.insert(successor)
		for name in frappe.get_all(roster.DECLARATION, filters={"evaluation_case": doc.name, "member_user": outgoing, "status": "Current"}, pluck="name"):
			decl = frappe.get_doc(roster.DECLARATION, name)
			decl.status, decl.resolution = "Resolved", f"Replaced by {successor.name}"
			records.save(decl)
		for name in frappe.get_all(roster.UNAVAILABILITY, filters={"evaluation_case": doc.name, "member_user": outgoing, "status": "Open"}, pluck="name"):
			row = frappe.get_doc(roster.UNAVAILABILITY, name)
			row.status, row.resolution = "Resolved", f"Replaced by {successor.name}"
			records.save(row)
		event = prc.roster(doc, roster.prc_roster(doc.name), cstr(reason).strip(), owner_event_id=f"appointment:{successor.name}", idempotency_key=idempotency_key)
		records.bump(doc, current_appointment=successor.name, last_committed_event=event)
		lifecycle.roster_changed(doc, reason=cstr(reason).strip(), idempotency_key=idempotency_key, actor=user)
		notify.tell(doc, [incoming_user], subject=f"Declare interests for {doc.tender_reference}",
			message=f"You are appointed to evaluate {doc.tender_reference}. Declare any conflict before viewing bids.", key=f"declare-{successor.name}")
		return records.summary(doc, appointment=successor.name, replaced=outgoing, incoming=incoming_user)

	return records.command("ReplaceEvaluationMember", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)
