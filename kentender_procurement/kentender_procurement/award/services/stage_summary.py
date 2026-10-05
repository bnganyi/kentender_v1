# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award's summary on the Tender record (OVS-CHG-001 v0.6 §4.1, §8, §13;
AWD-CHG-001 v0.5 §6, §7; plan D4, D9; tracker OVS6-0304).

The Head of Procurement Function, the Accounting Officer and the Auditor read
Award as AWD already lets them. A Head of User Department whose unit
contributed sees the stage, and once the Accounting Officer's decision is
recorded the decision, its outcome, date and reason (OVS-P03), and nothing of
the draft opinion, unissued notices or correspondence. Wording is Award's
own: the stage and outcome words and the notification status come from the
case. The person the professional opinion is with is named only when exactly
one person holds the responsibility."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.utils.display import display_datetime
from kentender_procurement.award.services import guards, people, records, state
from kentender_procurement.tenders.services import stage_summary as ss
from kentender_procurement.tenders.services import tender_authorization as authz

KEY, LABEL = "award", "Award"


def department_of(tender: str, user: str) -> bool:
	"""A Head of User Department whose unit contributed to the Tender, and who holds no Award role."""
	if guards.can_read(user) or people.technical(user) or not tender:
		return False
	return authz.is_department_head_of(frappe.get_doc("Tender", tender), user)


def for_tender(*, tender: str, user: str) -> list[dict[str, Any]]:
	name = frappe.db.get_value(records.CASE, {"tender": tender}, "name")
	if not name:
		return []
	readable = guards.can_read(user)
	technical = people.technical(user)
	department = not (readable or technical) and authz.is_department_head_of(frappe.get_doc("Tender", tender), user)
	if not (readable or technical or department):
		return []
	doc = frappe.get_doc(records.CASE, name)
	return ss.guarded(KEY, LABEL, lambda: _build(doc, readable=readable, department=department))


def outstanding(doc) -> dict[str, str] | None:
	"""Who the stage is with, in Award's terms; a person is named only when one person holds the responsibility."""
	role = {"Opinion": people.HEAD_OF_PROCUREMENT, "Decision": people.ACCOUNTING_OFFICER}.get(doc.stage)
	if not role or doc.cancelled:
		return None
	holders = people.holders(role)
	who = people.full_name(holders[0]) if len(holders) == 1 else ""
	subject = who or ("The Head of Procurement Function" if role == people.HEAD_OF_PROCUREMENT else "The Accounting Officer")
	text = f"{subject} is preparing the professional opinion." if doc.stage == "Opinion" else f"The award decision is with {who or 'the Accounting Officer'}."
	return {"text": text, "holder": who}


def _build(doc, *, readable: bool, department: bool) -> dict[str, Any]:
	decision = state.committed_decision(doc)
	links = [ss.link("view-record", "View award", ["award", doc.name])]  # a department head's route is the department view (reads.department_record)
	facts: list[dict[str, str]] = []  # the badge already names the stage
	outcome = {"label": "Outcome", "value": doc.outcome} if doc.outcome else None
	if decision:
		when = display_datetime(decision.decided_at) if decision.decided_at else ""
		facts += [ss.fact("Outcome", doc.outcome), ss.fact("Decision recorded", when)]
		if readable:
			facts.append(ss.fact("Notices", doc.notification_status))
		return ss.summary(key=KEY, label=LABEL, status=doc.stage, disclosure=ss.FULL if readable else ss.SUMMARY, facts=facts, outcome=outcome,
			actor=people.full_name(decision.decided_by) if decision.decided_by else "", recorded_at=when, reason=cstr(decision.reason),
			outstanding=outstanding(doc), links=links)
	return ss.summary(key=KEY, label=LABEL, status=doc.stage, disclosure=ss.STATUS_ONLY, facts=facts, outstanding=outstanding(doc), links=links)
