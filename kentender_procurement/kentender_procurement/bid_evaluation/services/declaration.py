# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DeclareEvaluationInterest and RecordMemberUnavailability (EVL-CHG-001 v0.4
§3, §7.2; tracker EVL4-406, EVL4-407; boards D02-D, D02-CONFLICT, D02-UNABLE).

Each appointed member personally chooses No conflict to declare or Declare a
conflict, and accepts: "I will keep bid information confidential and use it
only for this evaluation." A declared conflict stops that person's bid
access immediately and creates the Accounting Officer's task; it can be
declared at any time before delivery. A member records their own inability
to serve; the appointment is never silently removed, and the chair and the
Accounting Officer receive follow-up work."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import clock, guards, notify, people, prc, records, roster
from kentender_procurement.bid_evaluation.services.errors import Guards, fail
from kentender_procurement.services import sequence

CHOICES = ("No conflict to declare", "Declare a conflict")
CONFIDENTIALITY = "I will keep bid information confidential and use it only for this evaluation."


def declare_interest(*, tender: str, choice: str, confidentiality_accepted: bool, conflict_description: str = "", idempotency_key: str,
		user: str) -> dict[str, Any]:
	payload = {"choice": choice, "confidentiality_accepted": bool(confidentiality_accepted), "conflict_description": conflict_description}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if user not in roster.member_users(doc.name):
			raise frappe.DoesNotExistError("Not found")
		checks = guards.open_case(doc, "declarations")
		checks.raise_if_any()
		checks = Guards()
		fields = {}
		if choice not in CHOICES:
			fields["choice"] = "Choose No conflict to declare or Declare a conflict."
		if not confidentiality_accepted:
			fields["confidentiality_accepted"] = "Accept the confidentiality statement."
		if choice == "Declare a conflict" and not cstr(conflict_description).strip():
			fields["conflict_description"] = "Describe the conflict."
		if fields:
			checks.add("EVL_DECLARATION_REQUIRED", fields=fields)
		checks.raise_if_any()
		current = roster.declaration(doc.name, user)
		if current and current.choice == CHOICES[1] and choice == CHOICES[0]:
			# A declared conflict ends only through the Accounting Officer's reasoned replacement (EVL §3), never by the member's own re-declaration.
			fail("EVL_MEMBER_INELIGIBLE", {"reason": "declared_conflict", "explanation": "A declared conflict can be resolved only by the Accounting Officer."})
		if current and current.choice == choice and choice == "No conflict to declare":
			return records.summary(doc, declaration=current.declaration_id, unchanged=True)
		for name in frappe.get_all(roster.DECLARATION, filters={"evaluation_case": doc.name, "member_user": user, "status": "Current"}, pluck="name"):
			prior = frappe.get_doc(roster.DECLARATION, name)
			prior.status = "Superseded"
			records.save(prior)
		number = sequence.next_count(roster.DECLARATION, {"evaluation_case": doc.name})
		row = records.insert(frappe.get_doc({
			"doctype": roster.DECLARATION, "declaration_id": f"{doc.name}-DEC-{number:03d}", "evaluation_case": doc.name, "member_user": user,
			"appointment": doc.current_appointment, "choice": choice, "conflict_description": cstr(conflict_description).strip() if choice == CHOICES[1] else "",
			"confidentiality_accepted": 1, "declared_at": clock.now(), "status": "Current",
		}))
		event = prc.owner_event(doc, "DeclarationRecorded", f"declaration:{row.name}", {"member": user, "choice": choice}, idempotency_key=idempotency_key)
		records.bump(doc, last_committed_event=event)
		if choice == CHOICES[1]:
			from kentender_procurement.bid_evaluation.services import lifecycle

			lifecycle.roster_changed(doc, reason="A member declared a conflict.", idempotency_key=idempotency_key, actor=user)
			notify.tell(doc, people.holders(people.ACCOUNTING_OFFICER), subject=f"Resolve committee appointment for {doc.tender_reference}",
				message=f"{people.full_name(user)} declared a conflict on the evaluation of {doc.tender_reference}.", key=f"conflict-{row.name}")
		else:
			from kentender_procurement.bid_evaluation.services import review_tasks

			review_tasks.member_became_eligible(doc, user)
		return records.summary(doc, declaration=row.name, choice=choice)

	return records.command("DeclareEvaluationInterest", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def record_unavailability(*, tender: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if user not in roster.member_users(doc.name):
			raise frappe.DoesNotExistError("Not found")
		guards.closed(doc, Guards()).raise_if_any()
		if not cstr(reason).strip():
			fail("EVL_MEMBER_INELIGIBLE", {"fields": {"reason": "Give the reason."}})
		if roster.unavailable(doc.name, user):
			fail("EVL_VERSION_CONFLICT", {"reason": "already_recorded"})
		number = sequence.next_count(roster.UNAVAILABILITY, {"evaluation_case": doc.name})
		row = records.insert(frappe.get_doc({
			"doctype": roster.UNAVAILABILITY, "unavailability_id": f"{doc.name}-UNA-{number:02d}", "evaluation_case": doc.name, "member_user": user,
			"reason": cstr(reason).strip(), "recorded_at": clock.now(), "status": "Open",
		}))
		event = prc.owner_event(doc, "MemberUnableToServe", f"unavailable:{row.name}", {"member": user}, idempotency_key=idempotency_key, note=cstr(reason).strip())
		records.bump(doc, last_committed_event=event)
		from kentender_procurement.bid_evaluation.services import lifecycle

		lifecycle.roster_changed(doc, reason="A member recorded that they cannot continue.", idempotency_key=idempotency_key, actor=user)
		chair = roster.chair(doc.name)
		notify.tell(doc, [*people.holders(people.ACCOUNTING_OFFICER), *([chair] if chair and chair != user else [])],
			subject=f"Resolve committee appointment for {doc.tender_reference}",
			message=f"{people.full_name(user)} cannot continue on the evaluation of {doc.tender_reference}.", key=f"unable-{row.name}")
		return records.summary(doc, unavailability=row.name)

	return records.command("RecordMemberUnavailability", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"reason": reason}, body=body)
