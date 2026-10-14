# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The evaluation secretary (EVL-CHG-001 v0.8 §3, §7.2, §8, EVL-A20; board
D02-DELEGATE).

By office: when the Accounting Officer appoints the committee, the same
transaction records the authoritative Head of Procurement Function as
secretary — the person the Act calls "the person in charge of the
procurement function" (section 46(4)(c)). No task, waiting item or hand-off
exists for it.

By delegation: `DelegateEvaluationSecretary` is the Head's written
appointment of another procurement officer under the same section. Only the
authorised Head may use it; anyone else gets Not found and nothing is
written. Secretary status alone gives no member vote, finding or signature;
a secretary who is also validly appointed as a member acts as a member only
in that capacity. A new record supersedes the earlier one and every record
is kept."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import clock, guards, notify, people, prc, records, references, separation
from kentender_procurement.bid_evaluation.services.errors import Guards
from kentender_procurement.services import sequence

SECRETARY = "Evaluation Secretary Appointment"
BY_OFFICE = "By office"
WRITTEN = "Written appointment"


def office_holder(checks: Guards, tender: str = "") -> str | None:
	"""The authoritative Head of Procurement Function: the one person who holds
	an Active Head responsibility now. None, several or the Accounting Officer
	add a refusal and return None (EVL_SECRETARY_OFFICE_UNCLEAR,
	EVL_SECRETARY_INELIGIBLE)."""
	found = people.head_holders()
	if len(found) != 1:
		checks.add("EVL_SECRETARY_OFFICE_UNCLEAR", reason="head_unclear")
		return None
	holder = found[0]
	reason = separation.panel_refusal(holder, as_member=False, as_secretary=True)
	if reason:
		checks.add("EVL_SECRETARY_INELIGIBLE", person=holder, person_name=people.full_name(holder), reason=reason,
			explanation=f"{people.full_name(holder)} is the Accounting Officer, who decides the award and cannot sit on its evaluation.")
		return None
	if tender:
		from kentender_procurement.bid_submission.services import security_duty

		# Project Owner, 10 Oct 2026: a Head who has exercised the tender-security intake for this Tender cannot be its secretary
		blocked = security_duty.committee_blocker(tender, holder, "the evaluation secretary", "Evaluation secretary")
		if blocked:
			checks.add("EVL_SECRETARY_INELIGIBLE", person=holder, person_name=people.full_name(holder), reason="security_intake", explanation=blocked)
			return None
	return holder


def _next(doc) -> tuple[int, str]:
	number = sequence.next_count(SECRETARY, {"evaluation_case": doc.name})
	return number, references.secretary(doc.tender_reference, number - 1)


def _supersede(case: str) -> None:
	for name in frappe.get_all(SECRETARY, filters={"evaluation_case": case, "status": "Current"}, pluck="name"):
		prior = frappe.get_doc(SECRETARY, name)
		prior.status = "Superseded"
		records.save(prior)


def _record(doc, *, secretary: str, basis: str, by: str, authority: str, source_appointment: str, idempotency_key: str):
	number, reference = _next(doc)
	_supersede(doc.name)
	row = records.insert(frappe.get_doc({
		"doctype": SECRETARY, "secretary_appointment_id": f"{doc.name}-SEC-{number:02d}", "evaluation_case": doc.name, "secretary_user": secretary,
		"full_name": people.full_name(secretary), "appointment_reference": reference, "basis": basis, "appointing_authority": authority,
		"source_appointment": source_appointment or None, "assigned_by": by, "assigned_at": clock.now(), "status": "Current",
	}))
	event = prc.owner_event(doc, "SecretaryAssigned", f"secretary:{row.name}", {"secretary": secretary, "reference": row.appointment_reference, "basis": basis},
		idempotency_key=idempotency_key)
	return row, event


def record_by_office(doc, *, holder: str, appointment, appointing_officer: str, idempotency_key: str):
	"""Called inside `AppointEvaluationCommittee`'s transaction, after the
	appointment is inserted. Returns (secretary record, owner event)."""
	authority = (f"{people.full_name(appointing_officer)}, Accounting Officer — committee appointment {appointment.appointment_reference}, "
		f"{clock.now():%-d %b %Y, %H:%M} EAT")
	return _record(doc, secretary=holder, basis=BY_OFFICE, by=appointing_officer, authority=authority, source_appointment=appointment.name,
		idempotency_key=idempotency_key)


def ineligibility(doc, named: str) -> tuple[str, str] | None:
	"""Why `named` cannot be delegated the secretary's duties on this evaluation: (reason code, explanation), or None.
	The record picker lists a person by this, so the list and DelegateEvaluationSecretary say the same thing."""
	from kentender_procurement.bid_evaluation.services import roster
	from kentender_procurement.bid_submission.services import security_duty

	name = people.full_name(named)
	if named == roster.secretary(doc.name):
		return "already_secretary", f"{name} is already the secretary."
	if separation.panel_refusal(named, as_member=False, as_secretary=True):
		return "accounting_officer", f"{name} is the Accounting Officer, who decides the award and cannot sit on its evaluation."
	if not people.holds(named, people.PROCUREMENT_OFFICER):
		return "not_procurement_officer", f"{name} is not a procurement officer."
	# Project Owner, 10 Oct 2026: intake and evaluation duties exclude each other on the same Tender
	blocked = security_duty.committee_blocker(doc.tender, named, "the evaluation secretary", "Evaluation secretary")
	return ("security_intake", blocked) if blocked else None


def delegate_secretary(*, tender: str, secretary: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	if not people.holds(user, people.HEAD_OF_PROCUREMENT):
		raise frappe.DoesNotExistError("Not found")
	payload = {"secretary": secretary, "expected_version": expected_version}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		checks = guards.open_case(doc, "appointments")
		checks.raise_if_any()
		records.check_version(doc, expected_version)
		checks = Guards()
		named = cstr(secretary).strip()

		def refuse(reason: str, explanation: str) -> None:
			checks.add("EVL_SECRETARY_INELIGIBLE", person=named, person_name=people.full_name(named), reason=reason, explanation=explanation)

		problem = ineligibility(doc, named)
		if problem:
			refuse(*problem)
		checks.raise_if_any()
		authority = f"{people.full_name(user)}, Head of Procurement Function — written appointment, section 46(4)(c) of the Act"
		row, event = _record(doc, secretary=named, basis=WRITTEN, by=user, authority=authority, source_appointment=cstr(doc.current_appointment),
			idempotency_key=idempotency_key)
		records.bump(doc, secretary_appointment=row.name, last_committed_event=event)
		notify.tell(doc, [named], subject=f"Evaluation secretary for {doc.tender_reference}",
			message=f"You are the secretary of the evaluation of {doc.tender_reference}.", key=f"secretary-{row.name}")
		return records.summary(doc, secretary_appointment=row.name, reference=row.appointment_reference)

	return records.command("DelegateEvaluationSecretary", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)
