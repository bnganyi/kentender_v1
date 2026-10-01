# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""GetAwardWorkspace and GetAwardRecord (AWD-CHG-001 v0.4 §6, §7, §9;
AWD-AC-022, AC-024).

Scoped projections, with the current next step, journey, every outstanding
issue and the actions this viewer may take — decided here, never inferred in
the browser. The Head of Procurement and the Accounting Officer read the
record; the auditor reads it without any action; a technical reader sees
safe operation identifiers and service outcomes only (no tender, supplier,
price, opinion or decision); anyone else gets exactly the answer a missing
record gets."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import (
	checks, clock, clocks, corrections, eligibility, guards, issues, letters, next_steps, notices, people, profile, records, restrictions, simulation, state, tasks,
)


def _money(value, currency: str = "KES") -> str:
	return letters.money(value, currency) if value not in (None, "") else ""


def workspace(*, user: str) -> dict[str, Any]:
	if people.technical(user):
		return {"ok": True, "tasks": [], "technical": True}
	if not guards.can_read(user):
		return {"ok": True, "tasks": [], "forbidden": True}
	rows = [{"award": t["award"], "tender_title": t["tender_title"], "tender_reference": t["tender_reference"], "task": t["task"], "holder": t["holder"]}
		for t in tasks.all_for_user(user)]
	return {"ok": True, "tasks": rows, "test_environment": simulation.TEST_LABEL if simulation.enabled() else ""}


def _report(doc) -> dict[str, Any]:
	rep = state.current_report(doc)
	snap = state.snapshot(rep)
	sig = snap.get("signatures") or {}
	v = checks.validity(doc)
	rec = snap.get("recommended") or {}
	return {
		"id": rep.name, "label": f"Evaluation report {rep.version_number}", "version": rep.version_number, "received_at": clock.when(rep.received_at),
		"signatures": f"{sig.get('signed', 0)} of {sig.get('required', 0)}", "valid_until": clock.when(v["end"]) if v["end"] else "Not confirmed",
		"outcome": snap.get("outcome"), "reason": snap.get("reason"), "state": rep.state, "source_problem": rep.source_problem,
		"recommendation": f"Award to {rec.get('bidder')}" if rec else "No current recommendation",
		"recommended": {"supplier": rec.get("bidder", ""), "bid": rec.get("bid_reference", ""), "bid_version": "Submitted version 1" if rec else "",
			"quantity": rec.get("quantity", ""), "submitted": _money(rec.get("submitted_total"), rec.get("currency") or "KES"),
			"evaluated": _money(rec.get("evaluated_total"), rec.get("currency") or "KES"), "warranty": rec.get("warranty", "")} if rec else None,
		"comparison": [{"tenderer": r.get("bidder"), "amount": _money(r.get("evaluated_total"), r.get("currency") or "KES"),
			"submitted": _money(r.get("submitted_total"), r.get("currency") or "KES"), "position": cstr(r.get("position"))} for r in snap.get("comparison") or []],
		"tie": bool(checks.recommendation(doc).get("tie")), "committee": snap.get("committee") or [], "dissent": snap.get("dissent") or [],
		"qualifications": snap.get("qualifications") or [], "funding": snap.get("funding") or {},
		"versions": [{"label": f"Evaluation report {r.version_number}", "state": r.state, "received_at": clock.when(r.received_at)}
			for r in (frappe.get_doc(state.REPORT, n) for n in frappe.get_all(state.REPORT, filters={"award_case": doc.name}, pluck="name", order_by="creation asc"))],
	}


def _opinion(o) -> dict[str, Any] | None:
	if not o:
		return None
	return {"id": o.name, "label": f"Professional opinion {o.version}", "version": o.version, "state": o.state, "conclusion": o.conclusion, "reason": o.reason,
		"author": people.full_name(o.author), "signed": f"Signed by {people.full_name(o.author)}, {clock.when(o.signed_at)}" if o.signed_at else "",
		"proof_label": o.proof_label if simulation.enabled() else "", "signing_outcome": o.signing_outcome, "cycle": o.cycle}


def _decision(d) -> dict[str, Any] | None:
	if not d:
		return None
	label = {"Award": "Award decision", "No award": "No award decision"}.get(d.outcome, d.outcome)
	if d.kind == "Correction" and d.outcome == "Award":
		label = f"Corrected award decision {d.version}"
	return {"id": d.name, "label": label, "version": d.version, "outcome": d.outcome, "kind": d.kind, "reason": d.reason, "by": people.full_name(d.decided_by),
		"at": clock.when(d.decided_at), "supplier": d.supplier_name, "amount": _money(d.submitted_amount, d.currency or "KES"),
		"evaluated": _money(d.evaluated_amount, d.currency or "KES"), "next_action": d.next_action, "next_owner": people.full_name(d.next_action_owner) if d.next_action_owner else "",
		"committed": bool(d.committed), "cycle": d.cycle, "notices_authorised": bool(d.notices_authorised)}


def _notices(doc) -> dict[str, Any]:
	batch = state.current_batch(doc)
	if not batch:
		return {"batch": None, "recipients": [], "preview": notices.preview(doc) if doc.stage in ("Decision", "Opinion") else []}
	rows = []
	for n in state.notices(batch):
		attempts = records.loads(n.attempts_json, [])
		last = attempts[-1] if attempts else {}
		owner = ""
		if n.status == "Failed":
			owner = people.full_name(checks._technical()) if n.failure_reason == "Service unavailable" else people.full_name(issues.hop_for(doc))
		rows.append({"notice": n.name, "recipient": n.organisation_name, "result": n.result, "channel": "Email", "status": n.status,
			"delivery": {"Given": "Given", "Failed": "Delivery failed" if n.failure_reason != "Service unavailable" else "Service unavailable"}.get(n.status, n.status),
			"reason": n.failure_reason, "owner": owner, "contact": n.contact_email, "given_at": clock.when(n.given_at), "attempts": len(attempts),
			"last_attempt": last.get("outcome", ""), "label": records.loads(n.content_json).get("notice")})
	notice = state.successful_notice(batch)
	response = state.operative_response(notice)
	late = [r for r in state.responses(notice) if r.late] if notice else []
	wait = clocks.earliest_permitted(doc, batch)
	deadline = clocks.reply_deadline_for(notice) if notice else None
	return {"batch": {"id": batch.name, "label": rows[0]["label"] if rows else "", "status": batch.status, "issued_at": clock.when(batch.issued_at), "kind": batch.kind,
		"all_given": notices.all_given(batch), "reply_deadline": clock.when(deadline) if deadline else ""}, "recipients": rows,
		"response": {"response": response.response, "by": people.full_name(response.responder), "at": clock.when(response.received_at), "reason": response.reason,
			"wording": response.wording} if response else None,
		"late": [{"by": people.full_name(r.responder), "at": clock.when(r.received_at), "response": r.response} for r in late],
		"earliest": clock.when(wait.get("at")) if wait.get("known") else "", "preview": []}


def _package(doc) -> dict[str, Any] | None:
	pkg = eligibility.current_package(doc)
	if not pkg:
		return None
	return {"id": pkg.name, "status": pkg.status, "received_at": clock.when(pkg.received_at), "next": "Prepare contract" if pkg.status == "Delivered" else "",
		"owner": people.full_name(pkg.recipient_user) if pkg.recipient_user else "", "updates": len(records.loads(pkg.updates_json, [])),
		"attempts": len(records.loads(pkg.attempts_json, []))}


def _history(doc) -> list[dict[str, Any]]:
	out = []
	for c in state.cycles(doc):
		out.append({"cycle": c.number, "stage": c.stage, "outcome": c.outcome, "opinions": [_opinion(o) for o in state.opinions(doc, c.number)],
			"decisions": [_decision(d) for d in state.decisions(doc, c.number)]})
	return out


def _actions(doc, v: dict[str, Any]) -> dict[str, Any]:
	hop, ao = v["hop"] and not v["technical"], v["ao"] and not v["technical"]
	c = state.cycle(doc)
	open_ = not doc.cancelled and doc.stage != "Closed"
	opinion_stage = open_ and doc.stage == "Opinion" and not cint(c.awaiting_report)
	committed = state.committed_decision(doc, c.number)
	w = state.working_opinion(doc)
	return {
		"save_opinion": hop and opinion_stage,
		"sign_opinion": hop and opinion_stage and not any(i.subtype in (checks.SOURCE_INCOMPLETE, checks.RULES_UNVERIFIED, checks.STATUS_UNAVAILABLE) for i in issues.holding(doc))
			and not (w and w.state == "Signing" and w.signing_outcome and w.signing_outcome != "Accepted/Verified" and simulation.flag("signing_outcome")),
		"return_report": hop and open_ and doc.stage in ("Opinion", "Decision") and not cint(c.awaiting_report) and not state.committed_decision(doc),
		"decide": ao and open_ and doc.stage == "Decision" and not committed and cint(c.number) == 1 and not state.latest_committed(doc),
		"decide_correction": ao and open_ and doc.stage == "Decision" and not committed and (cint(c.number) > 1 or bool(state.latest_committed(doc))),
		"award_supported": not next_steps_positive_blocked(doc),
		"correction_proposals": ao and bool(restrictions.proposals(doc)) and bool(state.latest_committed(doc)) and doc.stage != "Decision",
		"authorise_revised": ao and doc.stage == "Notices" and bool(committed and committed.kind == "Correction" and committed.outcome == "Award" and
			not committed.notices_authorised and profile.revised_treatment_verified()),
		"record_restriction": hop and not doc.cancelled,
		"record_outcome": hop and not doc.cancelled,
		"respond_request": hop,
		"correct_contact": hop and doc.stage in ("Notices", "Waiting to proceed"),
		"retry_operation": v["technical"] and v["user"] in people.technical_operators(),
	}


def next_steps_positive_blocked(doc) -> bool:
	opinion = state.signed_opinion(doc)
	from kentender_procurement.award.services import decision

	return bool(decision.positive_guards(doc, opinion)) if opinion else True


def technical_view(doc) -> dict[str, Any]:
	"""Safe operation identifiers and outcomes only (§6)."""
	from kentender_core.services import support_issues

	ops = []
	for name in frappe.get_all("Support Issue", filters={"module": "Award", "reference_name": doc.name}, pluck="name", order_by="opened_at asc"):
		i = frappe.get_doc("Support Issue", name)
		ops.append({"issue": i.issue_id, "operation": i.operation, "subject": i.subject, "status": i.status, "opened_at": clock.when(i.opened_at),
			"detail": i.safe_detail})
	holder = cstr(profile.current().get("technical_operator")) or next(iter(support_issues.holders("Technical Operator")), "")
	return {"ok": True, "technical": True, "award": doc.name, "stage": doc.stage, "record_version": doc.record_version, "operations": ops,
		"holder_name": people.full_name(holder) if holder else ""}


def record(*, award: str, user: str) -> dict[str, Any]:
	if not award or not frappe.db.exists(records.CASE, award):
		raise frappe.DoesNotExistError("Not found")
	doc = frappe.get_doc(records.CASE, award)
	if people.technical(user):
		return technical_view(doc)
	guards.require_reader(user)
	v = next_steps.viewer(user)
	c = state.cycle(doc)
	working = state.working_opinion(doc)
	signed = state.signed_opinion(doc)
	decisions = state.decisions(doc, c.number)
	returned = [d for d in decisions if d.outcome == "Return for correction"]
	d = state.committed_decision(doc, c.number) or state.latest_committed(doc)
	out = {
		"ok": True, "award": doc.name, "tender_reference": doc.tender_reference, "tender_title": doc.tender_title, "procuring_entity": doc.procuring_entity,
		"stage": doc.stage, "outcome": doc.outcome, "cancelled": bool(doc.cancelled), "closed_reason": doc.closed_reason, "record_version": cint(doc.record_version),
		"cycle": {"number": c.number, "awaiting_report": bool(c.awaiting_report), "stage": c.stage, "outcome": c.outcome, "predecessor": c.predecessor,
			"authorising": _decision(frappe.get_doc(state.DECISION, c.authorising_decision)) if c.authorising_decision else None},
		"decision_status": doc.decision_status, "notification_status": doc.notification_status, "source_kind": doc.source_kind,
		"test_environment": simulation.TEST_LABEL if simulation.enabled() else "",
		"guidance": {"answer": next_steps.answer(doc, user), "journey": next_steps.journey(doc)},
		"outstanding": next_steps.outstanding(doc), "report": _report(doc),
		"opinion": {"working": _opinion(working), "signed": _opinion(signed), "all": [_opinion(o) for o in state.opinions(doc)]},
		"decision": _decision(d), "returned": {"comment": returned[-1].reason, "by": people.full_name(returned[-1].decided_by), "at": clock.when(returned[-1].decided_at)}
			if returned and not (signed and signed.signed_at and signed.signed_at > returned[-1].decided_at) else None,
		"notices": _notices(doc), "package": _package(doc), "history": _history(doc),
		"correspondence": [{"request": r.name, "from": people.full_name(r.requested_by), "organisation": r.organisation_name, "text": r.request_text,
			"requested_at": clock.when(r.requested_at), "state": r.state, "draft": r.reply_draft if r.reply_state in ("", "Draft") else "", "reply": r.reply_text,
			"reply_state": r.reply_state, "closed_at": clock.when(r.closed_at)} for r in (frappe.get_doc(state.CORRESPONDENCE, n) for n in
			frappe.get_all(state.CORRESPONDENCE, filters={"award_case": doc.name}, pluck="name", order_by="requested_at asc"))],
		"viewer": {k: v[k] for k in ("hop", "ao", "auditor", "technical")},
		"actions": _actions(doc, v),
		"revised": corrections.revised_preview(doc) if (doc.stage in ("Decision", "Notices") and (cint(c.number) > 1)) else None,
		"eligibility": {k: {"met": x["met"]} for k, x in eligibility.conditions(doc).items() if k != "ready"} if doc.stage == "Waiting to proceed" else None,
		"validity_rule": (checks.validity(doc).get("rule") or {}).get("counting", ""),
	}
	return out
