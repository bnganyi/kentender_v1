# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-decision corrections and decision cycles (AWD-CHG-001 v0.4 §5.7, §5.9
correction-cycle table, §5.10; AWD-AC-017, AC-029, AC-031).

A correction notice or opening update received after an Award or No award
decision becomes HOP's review item ("Review report correction" / "Review
opening update") with an immediate hold on further issue and delivery; the
original decision and notices are kept. HOP records the effect (§5.10). A
proposal to change the outcome goes to the Accounting Officer's
`RecordAwardCorrectionDecision`, which can:

- **Request corrected evaluation** — one numbered successor cycle on the same
  case, waiting for the corrected report from the controlled Evaluation route;
- **Authorise reconsideration** — a successor cycle on the current report;
- **Decline reconsideration** — the proposal closes, nothing resumes by itself;
- in a successor cycle's Decision stage: **Record corrected award** (with the
  exact revised batch authorised in the same action when its treatment is
  verified; otherwise held with no authorisation), **Record no award** or
  **Return for correction**;
- **Authorise revised notices** — later, against the existing corrected
  decision, creating no second decision.

A completed cycle, its decision and notices are never changed; the
current-cycle pointer moves only on the AO's authorised successor event;
cancellation cannot be reversed here."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import checks, clock, decision, guards, issues, notices, notify, profile, records, restrictions, sources, state
from kentender_procurement.award.services.errors import fail, invalid

REPORT_CORRECTION = "Report correction"
OPENING_UPDATE = "Opening update"
REVISED_TREATMENT = "Revised notice treatment"
OUTCOMES = ("Request corrected evaluation", "Authorise reconsideration", "Decline reconsideration", "Record corrected award", "Record no award",
	"Return for correction", "Authorise revised notices")


def on_evaluation_correction(tender: str) -> None:
	"""`kt_evaluation_correction_consumers`: a correction notice or opening
	update after delivery becomes Award's review item."""
	name = frappe.db.get_value(records.CASE, {"tender": tender}, "name")
	if name:
		pull_case(name)


def pull_case(award: str) -> int:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		return {"ok": True, "award": award, "count": pull(doc)}

	return records.command("ReceiveEvaluationCorrection", case=award, idempotency_key=f"corrections:{award}:{frappe.generate_hash(length=10)}", actor="system",
		payload={}, body=body)["count"]


def pull(doc) -> int:
	provider = sources.for_case(doc)
	count = 0
	for c in provider.corrections_after(doc.tender):
		source_event = cstr(c.get("source_event"))
		if frappe.db.exists(state.ISSUE, {"source_event": source_event}):
			provider.take_up_correction(c.get("reference"))
			continue
		closed = doc.stage == "Closed"
		kind = OPENING_UPDATE if c.get("kind") == OPENING_UPDATE else REPORT_CORRECTION
		if closed:
			title = "Review the correction to the closed award record."
		else:
			title = "Review the report correction before this award proceeds." if kind == REPORT_CORRECTION else "Review the opening update before this award proceeds."
		issue = issues.open_issue(doc, source_event=source_event, issue_type="Source correction", subtype=kind, title=title, holds=not closed,
			reason=cstr(c.get("reason")) or cstr(c.get("detail")), evidence=cstr(c.get("reference")), source="Evaluation",
			effective_at=c.get("effective_at"), detail={"correction": cstr(c.get("detail")), "reference": c.get("reference"), "closed_cycle": closed})
		provider.take_up_correction(c.get("reference"))
		restrictions._later_update(doc, issue)
		task = "Review report correction" if kind == REPORT_CORRECTION else "Review opening update"
		notify.tell(doc, [issues.hop_for(doc)], subject=f"{task} for {doc.tender_reference}", message=issue.reason, key=f"correction:{issue.name}")
		count += 1
	return count


def _successor(doc, *, instruction, awaiting: bool) -> Any:
	previous = state.cycle(doc)
	number = cint(previous.number) + 1
	c = records.new(state.CYCLE, cycle_id=f"{doc.name}-C{number}", award_case=doc.name, number=number, predecessor=previous.name,
		authorising_decision=instruction.name, source_report=previous.source_report, awaiting_report=1 if awaiting else 0, stage="Opinion", outcome="",
		started_at=clock.now(), fixture_namespace=doc.fixture_namespace)
	records.bump(doc, current_cycle=number, stage="Opinion", outcome="", closed_at=None)
	return c


def _instruction(doc, *, outcome: str, reason: str, user: str) -> Any:
	version = records.next_number(state.DECISION, {"award_case": doc.name})
	return records.new(state.DECISION, decision_id=f"{doc.name}-DEC-{version:02d}", award_case=doc.name, cycle=doc.current_cycle, version=version,
		kind="Correction", outcome=outcome, committed=0, decided_by=user, decided_at=clock.now(), reason=cstr(reason).strip(),
		predecessor_decision=(state.latest_committed(doc).name if state.latest_committed(doc) else ""), fixture_namespace=doc.fixture_namespace)


def _close_proposals(doc, *, disposition: str, reason: str, user: str, keep_open: bool = False) -> None:
	for i in restrictions.proposals(doc):
		detail = records.loads(i.detail_json)
		detail.setdefault("ao_decisions", []).append({"outcome": disposition, "reason": reason, "by": user, "at": str(clock.now())})
		if keep_open:
			detail["authorised"] = disposition
			records.update(i, detail_json=records.dumps(detail))
		else:
			detail.pop("proposal", None)
			records.update(i, detail_json=records.dumps(detail))
			issues.resolve(i, disposition=disposition, reason=reason, evidence="Accounting Officer's correction decision", user=user)


def _resolve_correction_holds(doc, *, reason: str, user: str) -> None:
	for i in issues.open_issues(doc):
		detail = records.loads(i.detail_json)
		if detail.get("authorised") or (detail.get("proposal") and i.issue_type in ("Source correction", "Supplier response", "Validity")):
			issues.resolve(i, disposition="Owner correction confirmed", reason=reason, evidence="Successor decision recorded", user=user)


def batch_ready(doc) -> bool:
	return profile.revised_treatment_verified()


def record(*, award: str, outcome: str, reason: str = "", next_action: str = "", expected_version=None, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_ao(user)
		guards.require_ao_not_opinion_author(user, doc)
		if doc.cancelled:
			fail("AWD_ON_HOLD", {"reason": "cancelled"})
		records.check_version(doc, expected_version)
		if outcome not in OUTCOMES:
			invalid({"outcome": "Choose a decision."})
		invalid({"reason": "Enter the reason." if not cstr(reason).strip() and outcome != "Authorise revised notices" else "",
			"next_action": "Name the next action." if outcome == "Record no award" and not cstr(next_action).strip() else ""})
		c = state.cycle(doc)
		committed_anywhere = state.latest_committed(doc)
		if not committed_anywhere:
			fail("AWD_RECORD_CHANGED", {"reason": "no_committed_decision"})
		result: dict[str, Any] = {}
		if outcome in ("Request corrected evaluation", "Authorise reconsideration", "Decline reconsideration"):
			if not restrictions.proposals(doc):
				fail("AWD_RECORD_CHANGED", {"reason": "no_proposal"})
			if outcome == "Decline reconsideration":
				_instruction(doc, outcome="Decline reconsideration", reason=reason, user=user)
				_close_proposals(doc, disposition="Reconsideration declined", reason=reason, user=user)
			else:
				instruction = _instruction(doc, outcome=outcome, reason=reason, user=user)
				_close_proposals(doc, disposition=outcome, reason=reason, user=user, keep_open=True)
				awaiting = outcome == "Request corrected evaluation"
				successor = _successor(doc, instruction=instruction, awaiting=awaiting)
				doc = state.reload(doc)
				result["cycle"] = successor.number
				if awaiting:
					rep = state.report(successor.source_report)
					back = sources.for_case(doc).return_for_correction(delivery=rep.source_delivery, comment=cstr(reason).strip(), instruction=instruction.name,
						authorised_by=user, idempotency_key=f"awd-correction:{instruction.name}")
					if back.get("ok") is False:
						fail("AWD_STATUS_UNAVAILABLE", {"reason": back.get("message") or "The evaluation correction could not be started."})
				notify.tell(doc, [issues.hop_for(doc)], subject=f"{'Evaluation is correcting the report' if awaiting else 'Prepare professional opinion'} for {doc.tender_reference}",
					message=cstr(reason).strip(), key=f"instruction:{instruction.name}")
				result["instruction"] = instruction.name
		elif outcome == "Authorise revised notices":
			d = state.committed_decision(doc, c.number)
			if not d or d.outcome != "Award" or d.notices_authorised:
				fail("AWD_RECORD_CHANGED", {"reason": "no_corrected_award_waiting"})
			if not batch_ready(doc):
				fail("AWD_RULE_UNVERIFIED", {"reason": "revised_notice_treatment"})
			_award_guards(doc, state.signed_opinion(doc))
			batch = notices.prepare_batch(doc, d, kind="Revised")
			notices.authorise(batch, user)
			records.update(d, notice_batch=batch.name, notices_authorised=1)
			for i in issues.open_issues(doc, subtype=REVISED_TREATMENT):
				issues.resolve(i, disposition="Owner correction confirmed", reason="The revised notices were authorised.", evidence=batch.name, user=user)
			notices.issue(state.reload(doc), batch, actor=user)
			result.update(decision=d.name, batch=batch.name)
		else:
			guards.stage(doc, "Decision")
			if cint(c.number) < 2:
				fail("AWD_RECORD_CHANGED", {"reason": "not_a_successor_cycle"})
			if state.committed_decision(doc, c.number):
				fail("AWD_RECORD_CHANGED", {"reason": "decision_committed"})
			opinion = state.signed_opinion(doc)
			if not opinion or c.opinion != opinion.name:
				fail("AWD_RECORD_CHANGED", {"reason": "no_current_signed_opinion"})
			if outcome == "Return for correction":
				d = decision.apply_return(doc, opinion, reason=reason, user=user, kind="Correction")
			elif outcome == "Record no award":
				d = decision.apply_no_award(doc, opinion, reason=reason, next_action=next_action, user=user, kind="Correction",
					predecessor=committed_anywhere.name)
				_resolve_correction_holds(state.reload(doc), reason="A corrected decision was recorded.", user=user)
			else:
				_award_guards(doc, opinion)
				ready = batch_ready(doc)
				d, batch = decision.apply_award(doc, opinion, reason=reason, user=user, kind="Correction", predecessor=committed_anywhere.name,
					authorise_batch=False)
				_resolve_correction_holds(state.reload(doc), reason="A corrected award was recorded.", user=user)
				doc = state.reload(doc)
				if ready:
					batch = notices.prepare_batch(doc, d, kind="Revised")
					notices.authorise(batch, user)
					records.update(d, notice_batch=batch.name, notices_authorised=1)
					notices.issue(state.reload(doc), batch, actor=user)
					result["batch"] = batch.name
				else:
					issues.open_issue(doc, source_event=f"revised-treatment:{d.name}", issue_type="Rules and notice audience", subtype=REVISED_TREATMENT,
						title="Confirm the required notice treatment before this award proceeds.", reason="The rules for revised notices have not been confirmed.",
						detail={"owner": "Legal-rule owner", "decision": d.name})
			result["decision"] = d.name
		records.audit(award, "RecordAwardCorrectionDecision", user, outcome=outcome, **{k: v for k, v in result.items() if isinstance(v, str)})
		return records.summary(state.reload(frappe.get_doc(records.CASE, award)), outcome=outcome, **result)

	return records.command("RecordAwardCorrectionDecision", case=award, idempotency_key=idempotency_key, actor=user,
		payload={"outcome": outcome, "reason": reason, "next_action": next_action, "expected": cstr(expected_version)}, body=body,
		authorise=lambda: guards.require_ao(user))


def _award_guards(doc, opinion) -> None:
	"""A corrected award needs the same support as an initial one; the only
	holds it does not answer to are the correction proposals this successor
	decision itself resolves and the revised-notice treatment."""
	g = guards.Guards()
	for i in issues.holding(doc):
		if records.loads(i.detail_json).get("authorised") or i.subtype == REVISED_TREATMENT:
			continue
		g.add("AWD_ON_HOLD", issue=i.name, title=i.title)
	rec = checks.recommendation(doc)
	if not rec["supported"]:
		g.add("AWD_NO_SUPPORTED_AWARD", reason=rec["reason"])
	if opinion.conclusion != "Recommend award":
		g.add("AWD_NO_SUPPORTED_AWARD", reason="The signed professional opinion has no current recommendation.")
	v = checks.validity(doc)
	if v["expired"]:
		g.add("AWD_VALIDITY_EXPIRED", valid_until=clock.when(v["end"]))
	guards.funding(doc, g)
	g.raise_if_any()


def revised_preview(doc) -> dict[str, Any]:
	"""V23p/V25: the revised notice's label and reply date, no waiting date
	before giving evidence exists."""
	version = records.next_number(state.BATCH, {"award_case": doc.name})
	deadline, _rule = profile.reply_deadline(clock.now())
	return {"label": f"Revised notice {version}", "reply_by": clock.when(deadline), "wait": "The waiting period will be calculated after notices are given."}

