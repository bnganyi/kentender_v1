# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award work items (AWD-CHG-001 v0.4 §5.9 task names; plan D12;
`reconciliation/next_step_register.md`).

Each item is derived from the current state and keyed by (case, cycle,
source event, responsibility), so a retry never duplicates one and resolving
one issue never clears another. An item appears when its event happens and
clears only when the recorded action it names is committed; opening or
reading never clears anything. Technical work is the core Support Issue's
own row. Suppliers have no Desk task: their notice is in the portal.
`my_work_rows` feeds My Work; the Award workspace (D01) lists the same items."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import checks, eligibility, explanation, issues, notices, people, profile, records, restrictions, state

OPEN_STAGES = ("Opinion", "Decision", "Notices", "Waiting to proceed", "Sent to Contracting", "Closed")


def _item(doc, key: str, task: str, role: str, since=None, holder: str = "") -> dict[str, Any]:
	return {"key": f"{doc.name}:{doc.current_cycle}:{key}", "award": doc.name, "tender_reference": doc.tender_reference, "tender_title": doc.tender_title,
		"task": task, "role": role, "since": cstr(since or ""), "holder": holder}


def for_user(doc, user: str) -> list[dict[str, Any]]:
	if doc.cancelled:
		return []
	hop = people.holds(user, people.HEAD_OF_PROCUREMENT)
	ao = people.holds(user, people.ACCOUNTING_OFFICER)
	name = people.full_name(user)
	out: list[dict[str, Any]] = []
	c = state.cycle(doc)
	if hop:
		if doc.stage == "Opinion" and not cint(c.awaiting_report):
			returned = [d for d in state.decisions(doc, c.number) if d.outcome == "Return for correction"]
			signed = state.signed_opinion(doc)
			if returned and not (signed and signed.signed_at and signed.signed_at > returned[-1].decided_at):
				out.append(_item(doc, f"returned:{returned[-1].name}", "Resolve returned decision", people.HEAD_OF_PROCUREMENT, returned[-1].decided_at, name))
			else:
				out.append(_item(doc, f"opinion:{c.source_report}", "Prepare professional opinion", people.HEAD_OF_PROCUREMENT, doc.received_at, name))
		for i in issues.open_issues(doc):
			detail = records.loads(i.detail_json)
			if detail.get("proposal"):
				continue
			task = {
				notices.DELIVERY_SUBTYPE: "Resolve notice delivery", checks.VALIDITY_EXPIRED: "Resolve expired validity",
				eligibility.RESPONSE_SUBTYPE_DECLINED: "Resolve supplier response", eligibility.RESPONSE_SUBTYPE_OVERDUE: "Resolve supplier response",
				"Report correction": "Review report correction", "Opening update": "Review opening update", "Revised notice treatment": "Resolve revised notice treatment",
				"Restriction": "Review restriction", "Cancellation after notification": "Review restriction", checks.FUNDING: "Resolve funding",
				checks.RULES_UNVERIFIED: "Resolve rules issue",
			}.get(i.subtype)
			if task and i.owner_role == people.HEAD_OF_PROCUREMENT:
				out.append(_item(doc, f"issue:{i.name}", task, people.HEAD_OF_PROCUREMENT, i.received_at, name))
		for r in explanation.open_requests(doc):
			out.append(_item(doc, f"request:{r.name}", "Respond to request", people.HEAD_OF_PROCUREMENT, r.requested_at, name))
		d = state.committed_decision(doc)
		if d and d.outcome == "No award" and d.next_action_state == "Open" and d.next_action_owner == user:
			out.append(_item(doc, f"next:{d.name}", cstr(d.next_action), people.HEAD_OF_PROCUREMENT, d.decided_at, name))
	if ao:
		if doc.stage == "Decision":
			correction = cint(c.number) > 1 or bool(state.latest_committed(doc))
			out.append(_item(doc, f"decide:{c.opinion}", "Decide correction" if correction else "Decide award", people.ACCOUNTING_OFFICER, None, name))
		if restrictions.proposals(doc) and state.latest_committed(doc) and doc.stage != "Decision":
			first = restrictions.proposals(doc)[0]
			out.append(_item(doc, f"proposal:{first.name}", "Decide correction", people.ACCOUNTING_OFFICER, first.modified, name))
		d = state.committed_decision(doc)
		if doc.stage == "Notices" and d and d.kind == "Correction" and d.outcome == "Award" and not d.notices_authorised and profile.revised_treatment_verified():
			out.append(_item(doc, f"revised:{d.name}", "Decide correction", people.ACCOUNTING_OFFICER, d.decided_at, name))
	return out


def all_for_user(user: str) -> list[dict[str, Any]]:
	if not user or user == "Guest" or people.technical(user):
		return []
	if not (people.holds(user, people.HEAD_OF_PROCUREMENT) or people.holds(user, people.ACCOUNTING_OFFICER)):
		return []
	out = []
	for name in frappe.get_all(records.CASE, filters={"stage": ("in", OPEN_STAGES), "cancelled": 0}, pluck="name", order_by="creation asc"):
		out += for_user(frappe.get_doc(records.CASE, name), user)
	return out


def my_work_rows(user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers`."""
	rows = []
	for t in all_for_user(user):
		rows.append({
			"task_id": t["key"], "task_type": f"award.{t['task'].lower().replace(' ', '-')}", "title": f"{t['task']} for {t['tender_reference']}",
			"reference": t["award"], "module": "Award", "stage": "Award", "fiscal_year": "", "organisation_unit": "", "assignment": t["role"], "status": "Assigned",
			"received_at": t["since"], "due_at": "", "action_label": "Open award", "route": ["award", t["award"]], "route_options": {}, "concurrency_token": "",
			"can_claim": False, "can_open": True, "comment": "",
		})
	return {"assigned": rows, "claimable": [], "waiting": []}
