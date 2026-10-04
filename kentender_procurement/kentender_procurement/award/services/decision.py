# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RecordAwardDecision (AWD-CHG-001 v0.4 §5.3, §5.7, §7; AWD-AC-004, AC-005,
AC-007, AC-031).

The Accounting Officer decides against the same signed report and opinion:

- **Award and notify bidders** records the reasoned award for the supported
  supplier and amount taken from the signed report — there is no supplier
  picker and no price editor — and authorises the exact generated notice
  batch in the same action; the system then issues it.
- **Return for correction** states the issue and returns it to the Head of
  Procurement as one "Resolve returned decision" task; nothing is sent.
- **Record no award** records why, and one concrete next action for the Head
  of Procurement; the cycle closes.

Each committed Award or No award retains one `AwardDecisionRecorded v1`
event in the same transaction. A cycle with a committed decision uses the
correction route instead."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import checks, clock, events, guards, issues, notices, notify, records, state
from kentender_procurement.award.services.errors import Guards, fail, invalid

OUTCOMES = ("Award", "No award", "Return for correction")


def _new_decision(doc, *, outcome: str, reason: str, user: str, opinion, kind: str = "Initial", committed: bool, **values) -> Any:
	version = records.next_number(state.DECISION, {"award_case": doc.name})
	return records.new(state.DECISION, decision_id=f"{doc.name}-DEC-{version:02d}", award_case=doc.name, cycle=doc.current_cycle, version=version, kind=kind,
		outcome=outcome, committed=1 if committed else 0, opinion=opinion.name if opinion else "", source_report=(opinion.source_report if opinion else
		doc.current_report), decided_by=user, decided_at=clock.now(), reason=cstr(reason).strip(), fixture_namespace=doc.fixture_namespace, **values)


def positive_guards(doc, opinion) -> Guards:
	g = guards.positive(doc)
	rec = checks.recommendation(doc)
	if not rec["supported"]:
		g.add("AWD_NO_SUPPORTED_AWARD", reason=rec["reason"])
	if opinion and opinion.conclusion != "Recommend award":
		g.add("AWD_NO_SUPPORTED_AWARD", reason="The signed professional opinion has no current recommendation.")
	v = checks.validity(doc)
	if v["expired"]:
		g.add("AWD_VALIDITY_EXPIRED", valid_until=clock.when(v["end"]))
	return g


def apply_award(doc, opinion, *, reason: str, user: str, kind: str = "Initial", predecessor: str = "", authorise_batch: bool = True, notice_kind: str = "Initial"):
	rec = checks.recommendation(doc)["recommended"]
	decision = _new_decision(doc, outcome="Award", reason=reason, user=user, opinion=opinion, kind=kind, committed=True,
		supplier_organisation=rec.get("organisation"), supplier_name=rec.get("bidder"), bid=rec.get("bid"), bid_reference=rec.get("bid_reference"),
		submitted_amount=rec.get("submitted_total"), evaluated_amount=rec.get("evaluated_total"), currency=rec.get("currency") or "KES",
		predecessor_decision=predecessor)
	c = state.cycle(doc)
	records.update(c, decision=decision.name)
	events.record(doc, decision)
	records.bump(doc, decision_status="Award recorded", current_decision=decision.name, outcome="")
	batch = None
	if authorise_batch:
		batch = notices.prepare_batch(doc, decision, kind=notice_kind)
		notices.authorise(batch, user)
		records.update(decision, notice_batch=batch.name, notices_authorised=1)
		state.set_stage(state.reload(doc), "Notices")
		notices.issue(state.reload(doc), batch, actor=user)
	else:
		state.set_stage(state.reload(doc), "Notices")
	return decision, batch


def apply_no_award(doc, opinion, *, reason: str, next_action: str, user: str, kind: str = "Initial", predecessor: str = ""):
	hop = issues.hop_for(doc)
	decision = _new_decision(doc, outcome="No award", reason=reason, user=user, opinion=opinion, kind=kind, committed=True, next_action=cstr(next_action).strip(),
		next_action_owner=hop or None, next_action_state="Open", predecessor_decision=predecessor)
	c = state.cycle(doc)
	records.update(c, decision=decision.name, outcome="No award", closed_at=clock.now(), stage="Closed")
	events.record(doc, decision)
	# the stopped, never-issued batch of an earlier award in this case stays as it is
	records.bump(doc, decision_status="No award recorded", current_decision=decision.name, outcome="No award", stage="Closed", closed_at=clock.now(),
		closed_reason=cstr(reason).strip())
	# The decision answers the matters that led to it; restrictions stay with their own authority.
	for i in issues.open_issues(doc):
		if i.issue_type in ("Validity", "Funding", "Supplier response") or i.subtype == checks.SOURCE_INCOMPLETE:
			issues.resolve(i, disposition="Closed by the no award decision", reason=cstr(reason).strip(), evidence=decision.name, user=user)
	notify.tell(doc, [hop], subject=f"{cstr(next_action).strip()} for {doc.tender_reference}", message="No award was made.", key=f"no-award:{decision.name}")
	return decision


def apply_return(doc, opinion, *, reason: str, user: str, kind: str = "Initial"):
	decision = _new_decision(doc, outcome="Return for correction", reason=reason, user=user, opinion=opinion, kind=kind, committed=False)
	if opinion and opinion.state == "Signed":
		records.update(opinion, state="Superseded")
	c = state.cycle(doc)
	records.update(c, opinion="", decision="")
	state.set_stage(doc, "Opinion")
	notify.tell(doc, [issues.hop_for(doc)], subject=f"Resolve returned decision for {doc.tender_reference}", message=cstr(reason).strip(),
		key=f"returned:{decision.name}")
	return decision


def record(*, award: str, outcome: str, reason: str = "", next_action: str = "", expected_version=None, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_ao(user)
		guards.open_case(doc).raise_if_any()
		records.check_version(doc, expected_version)
		guards.stage(doc, "Decision")
		if outcome not in OUTCOMES:
			invalid({"outcome": "Choose a decision."})
		invalid({"reason": "Enter the reason." if not cstr(reason).strip() else "",
			"next_action": "Name the next action." if outcome == "No award" and not cstr(next_action).strip() else ""})
		c = state.cycle(doc)
		if state.committed_decision(doc, c.number):
			fail("AWD_RECORD_CHANGED", {"reason": "decision_committed"})
		opinion = state.signed_opinion(doc)
		if not opinion or c.opinion != opinion.name:
			fail("AWD_RECORD_CHANGED", {"reason": "no_current_signed_opinion"})
		if outcome == "Award":
			positive_guards(doc, opinion).raise_if_any()
			decision, batch = apply_award(doc, opinion, reason=reason, user=user)
			result = {"decision": decision.name, "batch": batch.name if batch else ""}
		elif outcome == "No award":
			decision = apply_no_award(doc, opinion, reason=reason, next_action=next_action, user=user)
			result = {"decision": decision.name}
		else:
			decision = apply_return(doc, opinion, reason=reason, user=user)
			result = {"decision": decision.name}
		records.audit(doc.name, "RecordAwardDecision", user, outcome=outcome, decision=decision.name)
		return records.summary(state.reload(doc), **result)

	return records.command("RecordAwardDecision", case=award, idempotency_key=idempotency_key, actor=user,
		payload={"outcome": outcome, "reason": reason, "next_action": next_action, "expected": cstr(expected_version)}, body=body)
