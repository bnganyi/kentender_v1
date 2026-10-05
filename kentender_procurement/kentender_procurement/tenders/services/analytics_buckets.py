# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §5.2 — the one Tender classifier for Procurement Analytics
(plan D5; FU-ANL-05, FU-ANL-15).

A pure function over a facts dict: no database read, no clock, no session. The
provider (`analytics_provider.py`) gathers the facts, so this module is unit
tested without a world. Every Tender lands in exactly one bucket of
`analytics_contract.BUCKETS`, and the position wording is built from the bucket
label plus the owner's own text for the stage; a reason is never invented.

Facts read (`f`):

- ``status``       the Tender's `overall_status`
- ``at``           the read instant (naive site time)
- ``submission_deadline``  the effective deadline (datetime or None). The hourly job
                   that sets "Submission period ended" can lag, so a Published — open
                   Tender whose deadline has passed at ``at`` is classified as closed
                   for submission here too (FU-ANL-15)
- ``cancelled``    True when an authoritative cancellation decision exists
- ``cancellation_complete``  True / False / None: the compliance evidence of a
                   cancellation (None: not known, wording leaves it out)
- ``department``   True for a department-limited reader: the Award position then carries only "decision recorded" (or nothing)
- ``note``         the owner's wording for a Tender in preparation (a return, a reopen)
- ``opening`` / ``evaluation`` / ``award``  the stage owners' facts, each a dict,
                   None (the owner has no case for this Tender) or `FAILED` (the owner
                   read failed or its shape could not be used)

A failed read that the classification needs gives Status unavailable. A stage
that the classification does not need is never read, so its failure is
irrelevant (an empty opening does not need Award). Nothing is guessed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from kentender_core.services.analytics_contract import AWARD, CLOSED, CONTRACT, EVALUATION, OPEN, OPENING, PREPARATION, UNAVAILABLE

FAILED = "owner read failed"

# Bucket labels as the Tender rows word them (ANL §10A.4). Core holds the chart labels; these prefix the position.
LABELS = {
	PREPARATION: "Tender preparation", OPEN: "Open for bids", OPENING: "Opening", EVALUATION: "Evaluation", AWARD: "Award",
	CONTRACT: "Sent to Contract Management", CLOSED: "Closed", UNAVAILABLE: "Status unavailable",
}
PREPARATION_STATUSES = {
	"Draft": "draft", "Awaiting procurement approval": "awaiting procurement approval", "Approved": "awaiting publication authorisation",
	"Publication authorised": "publication confirmation required", "Requisition correction requested": "requisition correction requested",
}
PUBLISHED_OPEN, SUBMISSION_ENDED, CANCELLED = "Published — open", "Submission period ended", "Cancelled"

COMPLETE_AWAITING_RECEIPT = "complete; awaiting Evaluation receipt"
REPORT_DELIVERED = "Evaluation report delivered — Award receipt pending"


def lower_first(text: str) -> str:
	"""A sentence start as a phrase after a dash: "Automatic checks…" → "automatic checks…", "PPRA report" unchanged."""
	text = (text or "").strip()
	return text[:1].lower() + text[1:] if len(text) > 1 and text[1].islower() else text


def first_sentence(text: str) -> str:
	return (text or "").strip().split(". ")[0].strip().rstrip(".").strip()


def last_sentence(text: str) -> str:
	return (text or "").strip().split(". ")[-1].strip().rstrip(".").strip()


def position(label: str, detail: str = "") -> str:
	detail = (detail or "").strip()
	return f"{label} — {detail}" if detail else label


def result(bucket: str, detail: str = "", *, outcome: str = "") -> dict[str, str]:
	"""``outcome`` names the exact closing outcome of a Closed Tender ("cancelled", "no_bids", "no_evaluation", "no_award")."""
	return {"bucket": bucket, "position": position(LABELS[bucket], detail), "outcome": outcome}


def _usable(value: Any) -> bool:
	return isinstance(value, dict)


def _owner_detail(facts: dict[str, Any], outstanding_fallback: str = "", *, pick=first_sentence) -> str:
	"""The stage owner's own wording: its `position` when it supplies one, else one sentence of its outstanding matter. Evaluation's
	leads with the state of the work ("Automatic checks complete; committee review outstanding. The chair …"), so it takes the first;
	Award's ends with the pending work ("Award decision recorded. Required bidder notices are awaiting delivery."), so it takes the last."""
	text = (facts.get("position") or "").strip()
	if text:
		return lower_first(text)
	out = facts.get("outstanding")
	if _usable(out) and (out.get("text") or "").strip():
		return lower_first(pick(out["text"]))
	return outstanding_fallback


def opening_complete(opening: Any) -> bool:
	"""A nonempty opening that the owner records as complete."""
	return _usable(opening) and opening.get("outcome") == "Bids opened" and bool(opening.get("opening_complete_at"))


def _empty_opening_final(opening: Any) -> bool:
	"""Bid Opening gives an outcome only for a final opening, so "No bids" is a completed empty opening."""
	return _usable(opening) and opening.get("outcome") == "No bids"


def _after_close(f: dict[str, Any]) -> dict[str, str]:
	opening, evaluation, award = f.get("opening"), f.get("evaluation"), f.get("award")
	if opening == FAILED:
		return result(UNAVAILABLE)
	if _empty_opening_final(opening):
		return result(CLOSED, "no bids received; no evaluation required", outcome="no_bids")
	evaluation_received = _usable(evaluation) and bool(evaluation.get("opening_completed_at"))
	award_received = _usable(award) and bool(award.get("received_at"))
	if not (opening_complete(opening) or evaluation_received or award_received):
		# no case yet, or a case not complete: the opening is still pending or active ("a case existing before the opening is not Evaluation")
		if _usable(evaluation) and evaluation.get("no_evaluation_required"):
			return result(CLOSED, "no evaluation required", outcome="no_evaluation")
		state = (opening.get("status") if _usable(opening) else "") or ""
		return result(OPENING, lower_first(state) or "submission closed; opening not yet started")
	# the opening is complete (the Bid Opening owner says so, or Evaluation confirms the receipt)
	if evaluation == FAILED:
		return result(UNAVAILABLE)
	if evaluation is None:
		return result(OPENING, COMPLETE_AWAITING_RECEIPT)
	if not _usable(evaluation):
		return result(UNAVAILABLE)
	if evaluation.get("no_evaluation_required"):
		return result(CLOSED, "no evaluation required", outcome="no_evaluation")
	if evaluation.get("case_state") == "Cancelled":
		# a cancelled Evaluation under a Tender that is not cancelled cannot be explained from what was read
		return result(UNAVAILABLE)
	if not evaluation.get("opening_completed_at"):
		return result(OPENING, COMPLETE_AWAITING_RECEIPT)
	delivered = bool(evaluation.get("report_sent_at")) or evaluation.get("case_state") == "Report sent"
	if not delivered and not award_received:
		return result(EVALUATION, _owner_detail(evaluation, str(evaluation.get("case_state") or "").lower()))
	if award == FAILED:
		return result(UNAVAILABLE)
	if not award_received:
		return {"bucket": EVALUATION, "position": REPORT_DELIVERED, "outcome": ""}
	return _award(award, department=bool(f.get("department")))


def _award(award: dict[str, Any], *, department: bool = False) -> dict[str, str]:
	outcome = award.get("decision_outcome")
	if award.get("cancelled"):
		return result(CLOSED, "cancelled", outcome="cancelled")
	if award.get("closed") or award.get("stage") == "Closed":
		recorded = {"No award": "No award recorded", "Award": "Award decision recorded"}.get(outcome or "", "")
		return result(CLOSED, recorded, outcome="no_award" if outcome == "No award" else "closed")
	if award.get("sent_to_contracting") or award.get("stage") == "Sent to Contracting":
		return result(CONTRACT)
	if department:
		# OVS-CHG-001 v0.6 §4.1: a Head of User Department reads scoped status and the final decision, not the professional opinion or
		# unissued notices, so the working stages carry no owner wording
		return result(AWARD, "decision recorded" if award.get("decision_at") else "")
	stage = str(award.get("stage") or "").lower()
	return result(AWARD, _owner_detail(award, stage, pick=last_sentence))


def classify(f: dict[str, Any]) -> dict[str, str]:
	"""``{"bucket", "position", "outcome"}`` for one Tender. See the module docstring for the facts."""
	status = str(f.get("status") or "")
	at: datetime = f["at"]
	if f.get("cancelled") or status == CANCELLED:
		# terminal cancellation takes precedence; any earlier report or decision stays history
		complete = f.get("cancellation_complete")
		detail = "cancelled" + ("; cancellation compliance evidence complete" if complete is True else ("; cancellation compliance evidence outstanding" if complete is False else ""))
		return result(CLOSED, detail, outcome="cancelled")
	if status in PREPARATION_STATUSES:
		return result(PREPARATION, f.get("note") or PREPARATION_STATUSES[status])
	if status == PUBLISHED_OPEN:
		deadline = f.get("submission_deadline")
		if deadline is None or deadline > at:
			return result(OPEN)
		return _after_close(f)
	if status == SUBMISSION_ENDED:
		return _after_close(f)
	return result(UNAVAILABLE)


def needs_stage_reads(f: dict[str, Any]) -> bool:
	"""Whether the stage owners are asked about this Tender at all: only once submission has closed (or the Tender is cancelled,
	whose retained facts still count). A Tender in preparation or open for bids has no opening, evaluation or award."""
	status = str(f.get("status") or "")
	if f.get("cancelled") or status == CANCELLED or status == SUBMISSION_ENDED:
		return True
	deadline = f.get("submission_deadline")
	return status == PUBLISHED_OPEN and deadline is not None and deadline <= f["at"]
