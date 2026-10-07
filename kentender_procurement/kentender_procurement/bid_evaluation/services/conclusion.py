# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RecordCommitteeConclusion and RecordDisagreement (EVL-CHG-001 v0.4 §4.3,
§5.2, §7.2; tracker EVL4-605, EVL4-606; acceptance EVL-A05, EVL-A17; boards
D05-CONCLUSION, D05-CONCLUSION-Q, D05-MEMBER, D05-DISAGREE, D07-NO-AGREEMENT).

The chair or secretary records the committee's conclusion on one bid and
requirement, with the evidence and reasons, while every member of the
complete current eligible roster is personally present (§5.2; checked by
Proceedings on the active session). **Record conclusion** handles a resolved
finding or an explicit qualified-report disposition; clarification,
verification and technical repair use their own commands. The committee can
resolve how evidence is read under the published rule; it cannot waive a
failed mandatory condition, change a threshold, adjust a price or choose a
preferred bidder. The conclusion clears that bid and requirement's
discussion item. A member writes their own disagreement; the recorder cannot
attribute words to anyone, and a disagreement never blocks an accurate
report. If members cannot establish one supported recommendation, the
committee records **No agreed recommendation** with each attributed
position; no averaging, majority or casting vote."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import clock, discussion, findings, guards, prc, prc_owner, records, roster
from kentender_procurement.bid_evaluation.services.errors import fail, invalid

CONCLUSION = "Evaluation Conclusion"
DISAGREEMENT = "Evaluation Disagreement"
ITEM = "Evaluation Discussion Item"
CASE_KINDS = ("Due diligence basis", "No agreed recommendation")


def require_recorder(doc, user: str) -> None:
	if user not in (roster.chair(doc.name), roster.secretary(doc.name)):
		raise frappe.DoesNotExistError("Not found")


def collective(doc, idempotency_key: str) -> list[str]:
	"""Guards for a collective decision, then the lapse recheck; returns the
	complete current eligible roster whose presence Proceedings will require."""
	checks = discussion._collective_guards(doc)
	complete = roster.complete(doc.name)
	if not complete["complete"]:
		from kentender_procurement.bid_evaluation.services import people

		checks.add("EVL_MEMBERS_ABSENT", ineligible=[{"user": p["user"], "name": people.full_name(p["user"]), "reasons": p["reasons"]} for p in complete["pending"]],
			size_ok=complete["size_ok"])
	if not discussion.active_session(doc):
		checks.add("EVL_MEMBERS_ABSENT", reason="no_active_session")
	checks.raise_if_any()
	return complete["members"]


def committed(doc, *, event_type: str, owner_event_id: str, members: list[str], payload: dict[str, Any], note: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import sessions

	with prc_owner.acting(doc.name):
		return sessions.record_conclusion(**prc.ref(doc), event_type=event_type, owner_event_id=prc.bounded(owner_event_id), required_members=members, payload=payload,
			note=note, idempotency_key=prc.key(idempotency_key, "conclusion"), actor=prc.SYSTEM)


def insert(doc, *, kind: str, session: str, reason: str, recorded_by: str, participants: list[str], event: str, bid: str = "", requirement_key: str = "",
		result: str = "", evidence: list | None = None, next_action: str = "", item: str = "") -> Any:
	number = frappe.db.count(CONCLUSION, {"evaluation_case": doc.name}) + 1
	return records.insert(frappe.get_doc({
		"doctype": CONCLUSION, "conclusion_id": f"{doc.name}-CON-{number:02d}", "evaluation_case": doc.name, "session": session, "kind": kind,
		"evaluation_bid": bid, "requirement_key": requirement_key, "result": result, "reason": cstr(reason).strip(), "evidence_json": json.dumps(evidence or []),
		"next_action": next_action, "discussion_item": item, "recorded_by": recorded_by, "recorded_at": clock.now(), "participants_json": json.dumps(participants),
		"proceeding_event": event,
	}))


def open_item_for(doc, bid: str, requirement_key: str) -> str | None:
	return frappe.db.get_value(ITEM, {"evaluation_case": doc.name, "evaluation_bid": bid, "requirement_key": requirement_key, "status": "Open"}, "name")


def record_conclusion(*, tender: str, bid: str, requirement_key: str, result: str, reason: str, qualified: bool = False, evidence: list | None = None,
		idempotency_key: str, user: str) -> dict[str, Any]:
	payload = {"bid": bid, "requirement_key": requirement_key, "result": result, "reason": reason, "qualified": bool(qualified), "evidence": evidence or []}
	discussion.recheck_presence(tender)

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_recorder(doc, user)
		members = collective(doc, idempotency_key)
		requirement = findings._requirement(doc, bid, requirement_key)
		fields = {}
		if result not in findings.RESULTS:
			fields["result"] = "Choose Meets, Does not meet or Needs review."
		if not cstr(reason).strip():
			fields["reason"] = "Give the committee's reason."
		if result == "Needs review" and not qualified:
			fields["result"] = "Record a resolved result, or record this outcome for a qualified report."
		if requirement["unsupported_basis"] and result != "Needs review":
			fields["result"] = findings.UNSUPPORTED_MESSAGE
		if requirement["automatic"] == "Does not meet" and result == "Meets":
			fields["result"] = "A failed mandatory requirement cannot be waived. Report a suspected rule defect as an issue."
		invalid(fields)
		kind = "Qualified report" if result == "Needs review" else "Resolved finding"
		out = committed(doc, event_type="CommitteeConclusion", owner_event_id=f"conclusion:{doc.name}:{bid}:{requirement_key}:{idempotency_key}", members=members,
			payload={"bid": bid, "requirement": requirement_key, "result": result, "kind": kind}, note=cstr(reason).strip(), idempotency_key=idempotency_key)
		item = open_item_for(doc, bid, requirement_key)
		row = insert(doc, kind=kind, session=out["session_id"], reason=reason, recorded_by=user, participants=out["participants"], event=out["event_id"], bid=bid,
			requirement_key=requirement_key, result=result, evidence=evidence, next_action="Qualified report" if kind == "Qualified report" else "", item=item or "")
		if item:
			findings.clear_item(doc, item, kind=kind, reference=row.name)
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, conclusion=row.name, kind=kind, participants=out["participants"])

	return records.command("RecordCommitteeConclusion", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def record_case_conclusion(*, tender: str, kind: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""A conclusion about the case rather than one requirement: the basis for
	not undertaking due diligence, or No agreed recommendation."""
	if kind not in CASE_KINDS:
		raise ValueError(f"Unknown case conclusion {kind!r}")
	discussion.recheck_presence(tender)

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_recorder(doc, user)
		members = collective(doc, idempotency_key)
		invalid({"reason": "Give the committee's reason."} if not cstr(reason).strip() else {})
		out = committed(doc, event_type="CommitteeConclusion", owner_event_id=f"conclusion:{doc.name}:{kind}:{idempotency_key}", members=members,
			payload={"kind": kind}, note=cstr(reason).strip(), idempotency_key=idempotency_key)
		row = insert(doc, kind=kind, session=out["session_id"], reason=reason, recorded_by=user, participants=out["participants"], event=out["event_id"])
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, conclusion=row.name, kind=kind)

	return records.command("RecordCommitteeConclusion", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"kind": kind, "reason": reason}, body=body)


def record_disagreement(*, tender: str, statement: str, conclusion: str = "", report_version: str = "", idempotency_key: str, user: str) -> dict[str, Any]:
	payload = {"statement": statement, "conclusion": conclusion, "report_version": report_version}

	def body() -> dict[str, Any]:
		from kentender_procurement.proceedings.services import sessions

		doc = records.lock(tender)
		findings.require_member(doc, user)
		guards.closed(doc, guards.Guards()).raise_if_any()
		invalid({"statement": "Write your disagreement."} if not cstr(statement).strip() else {})
		linked = frappe.db.get_value(CONCLUSION, {"name": conclusion, "evaluation_case": doc.name}, "proceeding_event") if conclusion else ""
		if conclusion and not linked:
			raise frappe.DoesNotExistError("Not found")
		with prc_owner.acting(doc.name):
			out = sessions.record_member_statement(**prc.ref(doc), event_type="Disagreement", owner_event_id=prc.bounded(f"disagreement:{doc.name}:{idempotency_key}"),
				statement=cstr(statement).strip(), linked_event=linked or "", idempotency_key=prc.key(idempotency_key, "statement"), actor=user)
		number = frappe.db.count(DISAGREEMENT, {"evaluation_case": doc.name}) + 1
		row = records.insert(frappe.get_doc({
			"doctype": DISAGREEMENT, "disagreement_id": f"{doc.name}-DIS-{number:02d}", "evaluation_case": doc.name, "conclusion": conclusion,
			"report_version": report_version, "member_user": user, "statement": cstr(statement).strip(), "recorded_at": clock.now(), "proceeding_event": out["event_id"],
		}))
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, disagreement=row.name)

	return records.command("RecordDisagreement", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)
