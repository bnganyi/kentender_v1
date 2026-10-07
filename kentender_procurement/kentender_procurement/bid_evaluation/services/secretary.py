# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AssignEvaluationSecretary (EVL-CHG-001 v0.4 §3, §7.2; tracker EVL4-405;
board D02-S).

The secretary is the Head of Procurement or a procurement officer appointed
in writing by that head. Secretary status alone gives no member vote,
finding authority or signature; a secretary who is also validly appointed
as a member acts as a member only in that capacity. A new assignment
supersedes the earlier one and keeps it in history."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import clock, guards, notify, people, prc, records, separation
from kentender_procurement.bid_evaluation.services.errors import Guards
from kentender_procurement.services import sequence

SECRETARY = "Evaluation Secretary Appointment"


def assign_secretary(*, tender: str, secretary: str, appointment_reference: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	if not people.holds(user, people.HEAD_OF_PROCUREMENT):
		raise frappe.DoesNotExistError("Not found")
	payload = {"secretary": secretary, "appointment_reference": appointment_reference, "expected_version": expected_version}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		checks = guards.open_case(doc, "appointments")
		checks.raise_if_any()
		records.check_version(doc, expected_version)
		checks = Guards()
		if not cstr(appointment_reference).strip():
			checks.add("EVL_MEMBER_INELIGIBLE", fields={"appointment_reference": "Enter the appointment reference."})
		own = secretary == user
		if not own and not people.holds(secretary, people.PROCUREMENT_OFFICER):
			checks.add("EVL_MEMBER_INELIGIBLE", person=secretary, person_name=people.full_name(secretary), reason="not_procurement_officer",
				explanation=f"{people.full_name(secretary)} is not a procurement officer.")
		reason = separation.panel_refusal(secretary, as_member=False, as_secretary=True)
		if reason:
			checks.add("EVL_MEMBER_INELIGIBLE", person=secretary, person_name=people.full_name(secretary), reason=reason,
				explanation=f"{people.full_name(secretary)} is the Accounting Officer, who decides the award and cannot sit on its evaluation.")
		checks.raise_if_any()
		number = sequence.next_count(SECRETARY, {"evaluation_case": doc.name})
		for name in frappe.get_all(SECRETARY, filters={"evaluation_case": doc.name, "status": "Current"}, pluck="name"):
			prior = frappe.get_doc(SECRETARY, name)
			prior.status = "Superseded"
			records.save(prior)
		row = records.insert(frappe.get_doc({
			"doctype": SECRETARY, "secretary_appointment_id": f"{doc.name}-SEC-{number:02d}", "evaluation_case": doc.name, "secretary_user": secretary,
			"full_name": people.full_name(secretary), "appointment_reference": cstr(appointment_reference).strip(), "self_appointment": 1 if own else 0,
			"assigned_by": user, "assigned_at": clock.now(), "status": "Current",
		}))
		event = prc.owner_event(doc, "SecretaryAssigned", f"secretary:{row.name}", {"secretary": secretary, "reference": row.appointment_reference},
			idempotency_key=idempotency_key)
		records.bump(doc, secretary_appointment=row.name, last_committed_event=event)
		notify.tell(doc, [secretary], subject=f"Evaluation secretary for {doc.tender_reference}",
			message=f"You are the secretary of the evaluation of {doc.tender_reference}.", key=f"secretary-{row.name}")
		return records.summary(doc, secretary_appointment=row.name)

	return records.command("AssignEvaluationSecretary", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)
