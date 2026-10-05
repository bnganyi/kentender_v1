# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — Award's facts for Procurement Analytics (plan Phase 2C; FU-ANL-07).

One function, `facts_for(*, user, tender_names, at)`, called by the Tenders Analytics provider. It answers for one
actor (never the session user) and only reads: no case is opened, advanced, swept or marked, and none of the
owner's summary reads (which may write) is called. It does not decide the audience: the Tenders provider decides
who may see Tender facts at all. What it does decide is the amount.

Per Tender with an Award case it returns:

- `stage`: `Award Case.stage`.
- `received_at`: `Award Case.received_at`, the instant Award received the delivered Evaluation report (T5 start).
- `decision_at`, `decision_outcome`: the FIRST committed Award or No award decision of decision cycle 1 (T5 end).
  `state.committed_decision` returns the cycle's latest, so the first is taken from `state.decisions`, never from it.
  A later correction or reconsideration changes neither.
- `decision_events`: the `decided_at` of every committed Award or No award decision version, oldest first
  (ANL §4A.2 "AO award decisions"). Return for correction is not committed and is not counted.
- `award_amount`: the `submitted_amount` of the CURRENT committed Award decision, the committed decision of the
  case's current cycle (ANL-M-10; ANL conflict C6, recommended by `letters.py`, which also uses `submitted_amount`,
  and by A1: 7,185,000 against an authorised 7,500,000; AWD to confirm, FU-ANL-07 b). None for No award, a pending or
  returned decision, a decision of an earlier cycle (superseded) and an Award decision that records no amount. A
  cancelled case keeps the amount of its committed decision (`cancelled` is returned for the caller to treat);
  the amount is the decision's fact.
- `award_amount_visible`: False when the actor's owner read carries no amount. Only the Head of Procurement
  Function, the Accounting Officer, the Auditor (`guards.can_read`) and technical readers (Administrator, System
  Manager, Technical Operator) read amounts; the Head of User Department scoped summary
  (`reads.department_record`) never exposes one, so for that actor, and for anyone else, `award_amount` is None
  and `award_amount_visible` is False. No supplier name, bid value other than that amount, score or opinion text
  ever leaves.
- `sent_to_contracting`: the case's `delivered_at` is set, or the current package is Delivered.
- `closed`: stage Closed. `cancelled`: the case is cancelled.
- `outstanding`: None, or `{text, holder, since}`: the owner's wording without any instant, the holder as a
  person (only when exactly one person holds the responsibility, as `stage_summary.outstanding` does) or the
  responsibility, and the RAW instant the matter reached its holder, from the case, opinion, decision and issue
  records. The cases are the ones Award itself calls outstanding on Home (Opinion, Decision, Notices, a hold) plus
  the open next action of a No award decision. Waiting to proceed has none unless the case is on hold. A matter whose real instant is not
  recorded is None, never an invented one.

- `position`: a short phrase for the stage, without any stage label (the Tenders provider prefixes its bucket): "on hold" (an open
  Review/order hold), "professional opinion outstanding" (Opinion), "award decision outstanding" (Decision), "required bidder notices
  awaiting delivery" (Notices), "waiting period running" (Waiting to proceed), "sent to Contract Management" (Sent to Contracting) and,
  for a Closed case, the owner's own closed wording ("No award was made." is Award's headline, so "no award was made"). A cancelled
  case reads "tender cancelled; award ended" (Award's own words). Empty when nothing applies.

Technical readers get these facts in full, unlike `reads.record` (operations only). A failed read raises."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_core.services import analytics_contract as contract
from kentender_core.services.home_viewer import is_technical_reader
from kentender_procurement.award.services import eligibility, guards, issues, people, records, stage_summary, state

OPINION, DECISION, NOTICES, WAITING, SENT, CLOSED = "Opinion", "Decision", "Notices", "Waiting to proceed", "Sent to Contracting", "Closed"
RETURN = "Return for correction"
HOLD = "Review/order"


def facts_for(*, user: str, tender_names: list[str], at: datetime) -> dict[str, dict[str, Any]]:
	"""Award facts keyed by Tender name; a Tender with no Award case is omitted."""
	names = list(dict.fromkeys(name for name in tender_names or [] if name))
	if not names:
		return {}
	visible = _amount_visible(user, at)
	out: dict[str, dict[str, Any]] = {}
	for case in frappe.get_all(records.CASE, filters={"tender": ("in", names)}, pluck="name", order_by="creation asc"):
		doc = frappe.get_doc(records.CASE, case)
		out.setdefault(doc.tender, _facts(doc, visible=visible))
	return out


def _amount_visible(user: str, at: datetime) -> bool:
	"""Whether the actor's owner read carries the amount: a full reader or a technical reader, not a department head."""
	return bool(is_technical_reader(user, at) or guards.can_read(user))


def _facts(doc, *, visible: bool) -> dict[str, Any]:
	first = _first_decision(doc)
	return {
		"stage": cstr(doc.stage), "received_at": _instant(doc.received_at),
		"decision_at": _instant(first.decided_at) if first else None, "decision_outcome": first.outcome if first else None,
		"decision_events": _events(doc), "award_amount": _amount(doc) if visible else None, "award_amount_visible": visible,
		"sent_to_contracting": _sent(doc), "closed": doc.stage == CLOSED, "cancelled": bool(doc.cancelled), "outstanding": _outstanding(doc),
		"position": _position(doc),
	}


def _instant(value: Any) -> datetime | None:
	return get_datetime(value) if value else None


def _committed(doc, number: int | None = None) -> list:
	return [d for d in state.decisions(doc, number) if d.committed and d.outcome in state.COMMITTED]


def _first_decision(doc):
	"""The first committed decision of decision cycle 1, whatever decided later."""
	rows = _committed(doc, 1)
	return rows[0] if rows else None


def _events(doc) -> list[datetime]:
	events = []
	for d in _committed(doc):
		if not d.decided_at:
			raise ValueError(f"committed decision {d.name} has no decided_at")
		events.append(get_datetime(d.decided_at))
	return sorted(events)


def _current(doc):
	"""The committed decision of the case's CURRENT cycle. `state.committed_decision(doc)` with no number is the latest of the whole case,
	which would carry a superseded decision into a cycle that has none yet."""
	return state.committed_decision(doc, cint(doc.current_cycle) or 1)


def _amount(doc) -> Decimal | None:
	"""`submitted_amount` of the current cycle's committed Award decision (docstring); blank is no amount, an unreadable value raises."""
	decision = _current(doc)
	if not decision or decision.outcome != "Award" or not cstr(decision.submitted_amount).strip():
		return None
	return contract.money(decision.submitted_amount)


def _sent(doc) -> bool:
	if doc.delivered_at:
		return True
	package = eligibility.current_package(doc)
	return bool(package and package.status == "Delivered")


POSITIONS = {OPINION: "professional opinion outstanding", DECISION: "award decision outstanding", NOTICES: "required bidder notices awaiting delivery",
	WAITING: "waiting period running", SENT: "sent to Contract Management"}


def _position(doc) -> str:
	if doc.cancelled:
		return "tender cancelled; award ended"
	if doc.stage == CLOSED:
		decision = _current(doc)
		return "no award was made" if decision and decision.outcome == "No award" else ""
	if doc.stage != SENT and any(i.holds for i in issues.open_issues(doc, issue_type=HOLD)):
		return "on hold"  # a durable delivery to Contracting stays "sent"
	return POSITIONS.get(doc.stage, "")


# --------------------------------------------------------------------------
# the outstanding matter
# --------------------------------------------------------------------------


def _holder(role: str, who: str) -> str:
	return who or role


def _outstanding(doc) -> dict[str, Any] | None:
	if doc.cancelled or doc.stage == SENT:
		return None
	if doc.stage == CLOSED:
		return _next_action(doc)
	hold = next((i for i in issues.open_issues(doc, issue_type=HOLD) if i.holds), None)  # a review or order; a failed notice is its own matter
	if hold:
		return _matter("This award is on hold.", people.full_name(issues.hop_for(doc)), hold.received_at)
	if doc.stage == OPINION:
		return _opinion(doc)
	if doc.stage == DECISION:
		return _decision(doc)
	if doc.stage == NOTICES:
		return _notices(doc)
	return None


def _matter(text: str, holder: str, since: Any) -> dict[str, Any] | None:
	"""None when the real instant is not recorded."""
	return contract.outstanding(text, holder, get_datetime(since)) if since else None


def _who(doc) -> str:
	"""The person the stage is with, named only when exactly one person holds the responsibility (`stage_summary.outstanding`)."""
	return cstr((stage_summary.outstanding(doc) or {}).get("holder"))


def _opinion(doc) -> dict[str, Any] | None:
	cycle = state.cycle(doc)
	if cycle and cint(cycle.awaiting_report):
		return _matter("Awaiting a corrected evaluation report.", "Evaluation chair", cycle.started_at)
	report = state.current_report(doc)
	received = (report.received_at if report else None) or doc.received_at
	since = get_datetime(received) if received else None
	returned = [d for d in state.decisions(doc, cycle.number if cycle else None) if d.outcome == RETURN and d.decided_at]
	if returned and since and get_datetime(returned[-1].decided_at) > since:
		since = get_datetime(returned[-1].decided_at)  # back with the Head of Procurement Function since the return
	who = _who(doc)
	return _matter(f"Awaiting professional opinion by {who or 'the Head of Procurement Function'}.", _holder(people.HEAD_OF_PROCUREMENT, who), since)


def _decision(doc) -> dict[str, Any] | None:
	signed = state.signed_opinion(doc)
	correction = cint(state.cycle(doc).number) > 1 or bool(state.latest_committed(doc))
	who = _who(doc)
	kind = "correction decision" if correction else "award decision"
	return _matter(f"Awaiting {kind} by {who or 'the Accounting Officer'}.", _holder(people.ACCOUNTING_OFFICER, who), signed.signed_at if signed else None)


def _notices(doc) -> dict[str, Any] | None:
	decision = _current(doc)
	hop = issues.hop_for(doc)
	return _matter("Award decision recorded. Required bidder notices are awaiting delivery.", people.full_name(hop) if hop else people.HEAD_OF_PROCUREMENT,
		decision.decided_at if decision else None)


def _next_action(doc) -> dict[str, Any] | None:
	"""A No award decision's open next action, in the words the Accounting Officer recorded."""
	decision = _current(doc)
	if not decision or decision.outcome != "No award" or decision.next_action_state != "Open" or not cstr(decision.next_action).strip():
		return None
	owner = people.full_name(decision.next_action_owner) if decision.next_action_owner else ""
	return _matter(cstr(decision.next_action).strip().rstrip(".") + ".", owner, decision.decided_at)
