# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The next step and the Award journey for each viewer (AWD-CHG-001 v0.4
§5.9; KT-STD-001 §3B; plan D11; AWD-AC-022, AC-028).

Journey: **Opinion / Decision / Notices / Acceptance and wait / Send to
Contracting**, each Done, Current, Blocked or Not started, from the stored
stage and the §5.8 conditions — Waiting to proceed shows Acceptance and wait
until conditions 1–6 hold, then Send to Contracting; a hold marks the
affected step Blocked; Closed keeps the performed steps and never marks an
unperformed one Done; a cancellation marks the interrupted step Blocked.

Next step: the §5.9 wording, verbatim. A cancellation or a restriction that
stops the actor's next action leads; otherwise the actor's own work, then
the next scheduled event. Every outstanding issue is returned with its owner
alongside, so a hold never hides unrelated permitted work (the debrief
request D07 shows beside the running wait). Viewing never completes a task.
A technical reader never gets a turn (KT-STD §3B.6)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, flt

from kentender_core.services import next_step as ns
from kentender_procurement.award.services import checks, clock, eligibility, explanation, issues, notices, people, profile, records, restrictions, state

STAGES = (("opinion", "Opinion"), ("decision", "Decision"), ("notices", "Notices"), ("wait", "Acceptance and wait"), ("send", "Send to Contracting"))
STAGE_INDEX = {"Opinion": 0, "Decision": 1, "Notices": 2, "Waiting to proceed": 3, "Sent to Contracting": 4}
LABELS = {"D": ns.MARKER_DONE, "C": ns.MARKER_CURRENT, "B": ns.MARKER_BLOCKED, "N": ns.MARKER_NOT_STARTED}


def viewer(user: str) -> dict[str, Any]:
	return {"user": user, "technical": people.technical(user), "hop": people.holds(user, people.HEAD_OF_PROCUREMENT),
		"ao": people.holds(user, people.ACCOUNTING_OFFICER), "auditor": people.holds(user, people.AUDITOR)}


def _opinion_blocked(doc) -> bool:
	c = state.cycle(doc)
	if c and cint(c.awaiting_report):
		return True
	if any(i.subtype in (checks.SOURCE_INCOMPLETE, checks.RULES_UNVERIFIED, checks.STATUS_UNAVAILABLE) for i in issues.holding(doc)):
		return True
	w = state.working_opinion(doc)
	return bool(w and w.state == "Signing" and w.signing_outcome and w.signing_outcome != "Accepted/Verified")


def _restricted(doc) -> bool:
	return any(i.issue_type in ("Review/order", "Source correction", "Supplier response", "Validity", "Funding", "Rules and notice audience")
		for i in issues.holding(doc))


def markers(doc) -> str:
	if doc.cancelled:
		c = state.cycle(doc)
		k = STAGE_INDEX.get(cstr(c.interrupted_stage), 0)
		return "D" * k + "B" + "N" * (4 - k)
	if doc.stage == "Closed":
		return "DDNNN"
	if doc.stage == "Opinion":
		return ("B" if _opinion_blocked(doc) else "C") + "NNNN"
	if doc.stage == "Decision":
		return "DCNNN"
	if doc.stage == "Notices":
		blocked = bool(issues.open_issues(doc, subtype=notices.DELIVERY_SUBTYPE) or issues.open_issues(doc, subtype="Revised notice treatment")
			or issues.open_issues(doc, subtype=notices.SERVICE_SUBTYPE))
		return "DD" + ("B" if blocked else "C") + "NN"
	if doc.stage == "Waiting to proceed":
		cond = eligibility.conditions(doc)
		if not cond["ready"]:
			return "DDD" + ("B" if _restricted(doc) else "C") + "N"
		return "DDDD" + ("B" if cond["7"].get("failing") else "C")
	return "DDDDD"


def journey(doc) -> dict[str, Any] | None:
	code = markers(doc)
	holder = ""
	if code[0] == "C":
		holder = people.full_name(issues.hop_for(doc))
	elif code[1] == "C":
		holder = people.full_name(issues.ao_for(doc))
	elif code[2] == "C" and _revised_ready(doc):
		holder = people.full_name(issues.ao_for(doc))
	rows = []
	for (stage_code, label), m in zip(STAGES, code):
		marker = LABELS[m]
		rows.append({"code": stage_code, "label": label, "marker": marker, "marker_label": ns.MARKER_LABELS[marker], "holder": holder if m == "C" else ""})
	current = next((r for r in rows if r["marker"] in (ns.MARKER_CURRENT, ns.MARKER_BLOCKED)), None)
	index = rows.index(current) if current else len(rows) - 1
	shown = current or rows[-1]
	qualifier = " (blocked)" if shown["marker"] == ns.MARKER_BLOCKED else ""
	parts = {"prefix": "", "label": shown["label"] + qualifier, "suffix": f" · {index + 1} of {len(rows)}" + (f" · {shown['holder']}" if shown["holder"] else "")}
	return {"stages": rows, "current": current["code"] if current else "", "reduced_style": ns.REDUCED_POSITION, "reduced": False,
		"reduced_text": parts["prefix"] + parts["label"] + parts["suffix"], "reduced_parts": parts, "upstream": None, "downstream": None, "code": code}


def _revised_ready(doc) -> bool:
	d = state.committed_decision(doc)
	return bool(doc.stage == "Notices" and d and d.kind == "Correction" and d.outcome == "Award" and not d.notices_authorised and profile.revised_treatment_verified())


def _fix(label: str, fix_id: str, kind: str = ns.FIX_COMMAND, responsibility: str = people.HEAD_OF_PROCUREMENT, primary: bool = False, target=None):
	return ns.fix(label, responsibility=responsibility, kind=kind, fix_id=fix_id, primary=primary, target=target)


def _blocked(headline: str, code: str, *, sentence: str = "", fixes=(), facts=()) -> dict[str, Any]:
	g = ns.guard(False, reason_code=code, message=headline, headline=headline, fixes=list(fixes), facts=facts)
	return ns.answer(ns.KIND_BLOCKED, headline=headline, sentence=sentence, blockers=[ns.blocker(g)], fixes=list(fixes))


def _turn(headline: str, action: str, sentence: str = "") -> dict[str, Any]:
	return ns.answer(ns.KIND_YOUR_TURN, headline=headline, sentence=sentence, primary_action=action)


def _wait(headline: str, role: str, people_=(), sentence: str = "", since=None) -> dict[str, Any]:
	return ns.answer(ns.KIND_WAITING, headline=headline, sentence=sentence, holder=ns.holder(role, [p for p in people_ if p]), since=since)


def _technical_name(doc) -> str:
	return people.full_name(checks._technical())


def _hop_answers(doc, v) -> list[dict[str, Any]]:
	out = []
	c = state.cycle(doc)
	hold = [i for i in issues.open_issues(doc, issue_type="Review/order") if i.holds]
	if hold:
		first = hold[0]
		fix = [_fix("Record outcome", f"record_outcome:{first.name}", primary=True)]
		out.append(_blocked("This award is on hold.", "AWD_ON_HOLD", sentence=_hold_sentence(first), fixes=fix))
	if doc.stage == "Closed" and not doc.cancelled:
		review = [i for i in issues.open_issues(doc, issue_type="Source correction")]
		if review:
			out.append(_turn("Review the correction to the closed award record.", f"review_correction:{review[0].name}"))
		d = state.committed_decision(doc)
		if d and d.outcome == "No award":
			sentence = f"Next: {people.full_name(d.next_action_owner)} to {_lower(d.next_action)}." if d.next_action else ""
			out.append(_turn("No award was made.", "view_decision", sentence))
		return out
	if doc.stage == "Opinion":
		if c and cint(c.awaiting_report):
			out.append(_wait("Evaluation is correcting the report.", "Evaluation chair", sentence=""))
			return out
		source = issues.open_issues(doc, subtype=checks.SOURCE_INCOMPLETE)
		if source:
			out.append(_blocked("The evaluation report is incomplete. The Head of Procurement has been notified.", "AWD_SOURCE_INCOMPLETE", sentence=source[0].reason,
				fixes=[_fix("View source issue", f"view_issue:{source[0].name}", kind=ns.FIX_FOCUS, primary=True), _fix("Return report", "return_report")]))
			return out
		rules = issues.open_issues(doc, subtype=checks.RULES_UNVERIFIED)
		if rules:
			out.append(_blocked("The applicable rules have not been confirmed. The award cannot proceed yet.", "AWD_RULE_UNVERIFIED",
				fixes=[_fix("View outstanding issue", f"view_issue:{rules[0].name}", kind=ns.FIX_FOCUS, primary=True)]))
			return out
		status = issues.open_issues(doc, subtype=checks.STATUS_UNAVAILABLE)
		if status:
			out.append(_wait("The current tender status could not be confirmed. The system will check again when service is restored.", people.TECHNICAL_OPERATOR,
				[_technical_name(doc)]))
			return out
		w = state.working_opinion(doc)
		if w and w.state == "Signing" and w.signing_outcome and w.signing_outcome != "Accepted/Verified":
			out.append(_wait("Signing is unavailable. Your draft has been saved.", people.TECHNICAL_OPERATOR, [_technical_name(doc)],
				sentence=f"Technical operator {_technical_name(doc)} is restoring signing."))
			return out
		last = [d for d in state.decisions(doc, c.number) if d.outcome == "Return for correction"]
		signed = state.signed_opinion(doc)
		if last and not (signed and signed.signed_at and signed.signed_at > last[-1].decided_at):
			out.append(_turn("Resolve the Accounting Officer’s comments.", "sign_opinion"))
		elif cint(c.number) > 1 or cint(state.current_report(doc).version_number) > 1:
			out.append(_turn("Prepare the professional opinion on the corrected report.", "sign_opinion"))
		elif checks.validity(doc)["expired"]:
			out.append(_turn("Tender validity has expired. No award can proceed.", "sign_opinion"))
		elif checks.recommendation(doc).get("tie"):
			out.append(_turn("Review the equal-price outcome.", "sign_opinion"))
		else:
			out.append(_turn("Prepare the professional opinion.", "sign_opinion"))
		return out
	if doc.stage == "Decision":
		out.append(_wait("The Accounting Officer is deciding the award.", people.ACCOUNTING_OFFICER, [people.full_name(issues.ao_for(doc))]))
		out += _open_requests(doc)
		return out
	if doc.stage == "Notices":
		treatment = issues.open_issues(doc, subtype="Revised notice treatment")
		if treatment:
			out.append(_blocked("Confirm the required notice treatment before this award proceeds.", "AWD_RULE_UNVERIFIED",
				sentence="The rules for revised notices have not been confirmed.", fixes=[_fix("View outstanding issue", f"view_issue:{treatment[0].name}",
				kind=ns.FIX_FOCUS, primary=True)]))
			return out
		failed = issues.open_issues(doc, subtype=notices.DELIVERY_SUBTYPE)
		if failed:
			out.append(_blocked("A required notice is not yet confirmed.", "AWD_NOTICE_FAILED", sentence=failed[0].reason,
				fixes=[_fix("Correct contact", f"correct_contact:{records.loads(failed[0].detail_json).get('notice')}", primary=True)]))
		service = issues.open_issues(doc, subtype=notices.SERVICE_SUBTYPE)
		if service and not failed:
			out.append(_wait("A required notice is not yet confirmed.", people.TECHNICAL_OPERATOR, [_technical_name(doc)],
				sentence=f"Technical operator {_technical_name(doc)} is restoring notice delivery."))
		if _revised_ready(doc):
			out.append(_wait("The Accounting Officer is authorising the revised notices.", people.ACCOUNTING_OFFICER, [people.full_name(issues.ao_for(doc))]))
		out += _open_requests(doc)
		return out
	# Waiting to proceed / Sent to Contracting
	for i in issues.open_issues(doc):
		if i.issue_type == "Validity" and i.subtype == checks.VALIDITY_EXPIRED:
			out.append(_turn("Tender validity has expired. No award can proceed.", f"record_next_action:{i.name}"))
		elif i.issue_type == "Source correction" and not records.loads(i.detail_json).get("proposal"):
			out.append(_turn(i.title, f"review_correction:{i.name}"))
		elif i.issue_type == "Supplier response" and not records.loads(i.detail_json).get("proposal"):
			headline = "Review the supplier’s response." if i.subtype == eligibility.RESPONSE_SUBTYPE_DECLINED else "The supplier has not replied by the deadline."
			out.append(_turn(headline, f"record_next_action:{i.name}"))
	if restrictions.proposals(doc):
		out.append(_wait("Decide the reported correction.", people.ACCOUNTING_OFFICER, [people.full_name(issues.ao_for(doc))]))
	out += _open_requests(doc)
	if doc.stage == "Sent to Contracting":
		pkg = eligibility.current_package(doc)
		out.append(ns.answer(ns.KIND_DONE, headline="Contracting has received the award."))
		return out
	cond = eligibility.conditions(doc)
	if cond["ready"] and cond["7"].get("failing"):
		out.append(_wait("Contracting is unavailable. KenTender will check that the award can still proceed before sending it.", people.TECHNICAL_OPERATOR,
			[_technical_name(doc)], sentence=f"Technical operator {_technical_name(doc)} is restoring delivery."))
	elif not cond["3"]["met"] and not cond["3"].get("response") and not cond["3"].get("late"):
		out.append(_wait("The supplier must reply by the date in the notice.", "Authorised Signatory", [_signatory_name(doc)]))
	elif not cond["4"]["met"]:
		out.append(_wait("The required waiting period is still running.", "System", sentence="KenTender will send the award to Contracting when all conditions are met."))
	return out


def _lower(text: str) -> str:
	t = cstr(text).strip().rstrip(".")
	return t[:1].lower() + t[1:] if t else t


def _hold_sentence(issue) -> str:
	return f"{cstr(issue.source) or 'Restriction'} received {clock.when(issue.received_at)}"


def _signatory_name(doc) -> str:
	batch = state.current_batch(doc)
	n = state.successful_notice(batch)
	if not n:
		return ""
	from kentender_procurement.award.services import sources

	for p in sources.for_case(doc).organisation_users(n.organisation, at=clock.now()):
		if p.get("responsibility") == "Authorised Signatory":
			return people.full_name(p.get("user"))
	return n.organisation_name


def _open_requests(doc) -> list[dict[str, Any]]:
	reqs = explanation.open_requests(doc)
	return [_turn("Respond to the bidder’s request.", f"respond_request:{reqs[0].name}")] if reqs else []


def _ao_answers(doc) -> list[dict[str, Any]]:
	out = []
	if doc.stage == "Decision":
		correction = cint(state.cycle(doc).number) > 1 or bool(state.latest_committed(doc))
		out.append(_turn("Decide the reported correction." if correction else "Decide the award.", "decide"))
	if _revised_ready(doc):
		out.append(_turn("Authorise the revised notices.", "authorise_revised_notices"))
	if restrictions.proposals(doc):
		if state.latest_committed(doc):
			out.append(_turn("Decide the reported correction.", "decide_correction"))
	if doc.stage == "Opinion" and not doc.cancelled:
		out.append(_wait("The Head of Procurement is preparing the professional opinion.", people.HEAD_OF_PROCUREMENT, [people.full_name(issues.hop_for(doc))]))
	return out


def _reader_answer(doc) -> dict[str, Any]:
	if doc.cancelled:
		return _closed_cancelled()
	if doc.stage == "Sent to Contracting":
		return ns.answer(ns.KIND_DONE, headline="Contracting has received the award.")
	if doc.stage == "Closed":
		return ns.answer(ns.KIND_DONE, headline="No award was made.")
	return ns.not_involved()


def _closed_cancelled() -> dict[str, Any]:
	a = ns.answer(ns.KIND_DONE, headline="This tender was cancelled. Award ended.")
	a["label"] = "Closed"
	return a


def answer(doc, user: str) -> dict[str, Any]:
	v = viewer(user)
	if doc.cancelled:
		return _closed_cancelled()
	candidates: list[dict[str, Any]] = []
	if v["hop"]:
		candidates += _hop_answers(doc, v)
	if v["ao"]:
		candidates += _ao_answers(doc)
	if not candidates:
		return ns.for_viewer(_reader_answer(doc), technical=v["technical"], reader=_reader_answer(doc))
	blocked_hold = [c for c in candidates if c["kind"] == ns.KIND_BLOCKED and c["blockers"] and c["blockers"][0]["reason_code"] == "AWD_ON_HOLD"]
	chosen = blocked_hold[0] if blocked_hold else ns.choose(*candidates)
	return ns.for_viewer(chosen, technical=v["technical"], reader=_reader_answer(doc))


def outstanding(doc) -> list[dict[str, Any]]:
	"""Every outstanding issue and its owner, shown together (§5.9)."""
	out = []
	for i in issues.open_issues(doc):
		owner = people.full_name(i.owner_user) if i.owner_user else cstr(i.owner_role)
		detail = records.loads(i.detail_json)
		out.append({"issue": i.name, "type": i.issue_type, "subtype": i.subtype, "title": i.title, "reason": i.reason, "owner": owner, "holds": bool(i.holds),
			"basis": i.basis, "source": i.source, "received_at": clock.when(i.received_at), "effective_at": clock.when(i.effective_at),
			"proposal": detail.get("proposal"), "outcomes": list(restrictions.applicable(i)), "external_owner": detail.get("owner", "")})
	for r in explanation.open_requests(doc):
		out.append({"request": r.name, "type": "Debrief", "title": "Respond to the bidder’s request.", "owner": people.full_name(issues.hop_for(doc)),
			"holds": False, "reason": r.request_text})
	d = state.committed_decision(doc)
	if d and d.outcome == "No award" and d.next_action_state == "Open":
		out.append({"follow_up": d.name, "type": "Next action", "title": cstr(d.next_action), "owner": people.full_name(d.next_action_owner), "holds": False})
	return out


def problems(doc, user: str) -> list[str]:
	return ns.problems(answer(doc, user))


def summary_amount(value) -> str:
	return f"KES {flt(value):,.0f}" if value not in (None, "") else ""
