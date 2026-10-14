# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Evaluation's sources for the shared record picker (kentender_core.services.record_picker).

`bid_evaluation.committee_member` answers "who may this Accounting Officer name to the evaluation committee
of this Tender" (the appointment form's rows and a replacement); `bid_evaluation.secretary` answers "who may
this Head of Procurement Function delegate the secretary's duties to". Both are the viewer's own to ask:
anyone else gets the masked not-found the commands give.

Eligibility is not decided here. `appointment.ineligibility` and `secretary.ineligibility` are the very
functions AppointEvaluationCommittee, ReplaceEvaluationMember and DelegateEvaluationSecretary call, and a
person is listed unavailable in their words, the tender-security duty's conflict included: a person missing
from a list with no explanation is worse than one shown with the command's reason (the approved plan)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import record_picker
from kentender_procurement.bid_evaluation.services import appointment, member_department, people, records, roster, secretary

COMMITTEE = "bid_evaluation.committee_member"
SECRETARY = "bid_evaluation.secretary"


def sources() -> list[dict[str, Any]]:
	base = "kentender_procurement.bid_evaluation.services.picker_sources."
	return [
		{"key": COMMITTEE, "noun": "person", "plural": "people", "match": "core", "provider": base + "committee_members",
			"hint": "Only staff members with an active KenTender account can be named here."},
		{"key": SECRETARY, "noun": "person", "plural": "people", "match": "core", "provider": base + "secretaries",
			"hint": "Only procurement officers can be delegated the secretary's duties."},
	]


def _case(context: dict) -> Any:
	name = frappe.db.get_value(records.CASE, {"tender_reference": cstr(context.get("tender_reference"))}, "name")
	if not name:
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(records.CASE, name)


def _row(user: str, designation: str, near: set[str], reason: str | None) -> dict[str, Any]:
	department = member_department.department_of(user)
	detail = " · ".join(part for part in (designation, department) if part)
	return record_picker.person_row(user, detail, near=user in near, disabled_reason=reason, extra={"designation": designation, "department": department})


def committee_members(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""context: `tender_reference`; `mode` "appoint" (the form being drafted: `taken` are the other rows) or "replace" (the current roster is taken)."""
	doc = _case(context)
	if not people.holds(actor, people.ACCOUNTING_OFFICER):
		raise frappe.DoesNotExistError("Not found")
	replacing = cstr(context.get("mode")) == "replace"
	drafted = {cstr(u) for u in context.get("taken") or []} if isinstance(context.get("taken"), list) else set()
	current = set(roster.member_users(doc.name)) if replacing else set()
	users = sorted(frappe.get_all("User", filters={"enabled": 1, "user_type": "System User", "name": ("not in", ("Administrator", "Guest"))}, pluck="name"))
	near = record_picker.people_near(actor, users)
	out = []
	for user in users:
		ok, designation = people.internal(user)
		if not ok:
			continue
		# the commands' own order: a name already on the roster is refused as such before anything else
		if replacing and user in current:
			code = "declared_conflict" if roster.status(doc.name, user)["conflict"] else "already_member"
		else:
			code = "duplicate" if user in drafted else appointment.ineligibility(doc, user)
		out.append(_row(user, designation, near, appointment.refusal_text(code, user) if code else None))
	return out


def secretaries(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""context: `tender_reference`. Procurement officers other than the Head, who is secretary by office and not a pick."""
	doc = _case(context)
	if not people.holds(actor, people.HEAD_OF_PROCUREMENT):
		raise frappe.DoesNotExistError("Not found")
	users = sorted(set(people.holders(people.PROCUREMENT_OFFICER)) - {actor})
	near = record_picker.people_near(actor, users)
	out = []
	for user in users:
		problem = secretary.ineligibility(doc, user)
		out.append(_row(user, people.internal(user)[1], near, problem[1] if problem else None))
	return out
