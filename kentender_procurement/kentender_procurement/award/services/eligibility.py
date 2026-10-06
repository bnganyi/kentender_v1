# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RefreshAwardEligibility and DeliverAwardPackage (AWD-CHG-001 v0.4 §5.5,
§5.8, §5.9 tracker mapping; AWD-AC-012–014, AC-019–021, AC-028).

The seven §5.8 conditions are evaluated together and every unmet one is
returned. They are rechecked on every event, by the scheduled sweep and
before every delivery attempt; unknown stays unknown. When conditions 1–6
hold, the system prepares one frozen package of exact versions and delivers
it; the receiver's durable receipt, and only that, makes the case "Sent to
Contracting". A receiver outage leaves the package waiting, retried
automatically after rechecking conditions 1–6 — never an approval request.
A missed reply date is recorded as a missed deadline, never as a refusal,
and nobody is substituted and no security is forfeited."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.award.services import checks, clock, clocks, contracting, issues, notices, notify, people, profile, records, state

PACKAGE = state.PACKAGE
RESPONSE_SUBTYPE_DECLINED = "Declined"
RESPONSE_SUBTYPE_OVERDUE = "No response"
RESPONSE_SUBTYPE_LATE = "Late response"


def conditions(doc) -> dict[str, Any]:
	"""{"1".."7": {met, reason}} plus the facts behind them."""
	out: dict[str, Any] = {}
	d = state.committed_decision(doc)
	c = state.cycle(doc)
	opinion = state.signed_opinion(doc)
	out["1"] = {"met": bool(d and d.outcome == "Award" and opinion and c and c.decision == d.name), "reason": "A current supported award decision is required."}
	batch = state.current_batch(doc)
	out["2"] = {"met": notices.all_given(batch), "reason": "A required notice is not yet confirmed."}
	notice = state.successful_notice(batch)
	response = state.operative_response(notice)
	out["3"] = {"met": bool(response and response.response == "Accept" and not response.late), "reason": "The supplier must reply by the date in the notice.",
		"response": response.response if response else "", "late": bool(response and response.late)}
	wait = clocks.earliest_permitted(doc, batch) if batch else {"known": False}
	out["4"] = {"met": bool(wait.get("known") and wait.get("passed")), "reason": "The required waiting period is still running.", "earliest": wait.get("at")}
	v = checks.validity(doc)
	out["5"] = {"met": bool(v["known"] and not v["expired"]), "reason": "Tender validity has expired. No award can proceed." if v["expired"] else
		"The current tender status could not be confirmed.", "valid_until": v.get("end")}
	holds = issues.holding(doc)
	status = checks.tender_status(doc)
	out["6"] = {"met": not holds and status["known"] and not status["cancelled"] and profile.verified(), "reason": "This award is on hold. Review the reason and responsible officer.",
		"issues": [i.name for i in holds]}
	pkg = current_package(doc)
	out["7"] = {"met": bool(pkg and pkg.status == "Delivered"), "reason": "Contracting has not yet received the award.", "package": pkg.name if pkg else "",
		"failing": bool(pkg and pkg.status in ("Failed", "Held"))}
	out["ready"] = all(out[str(n)]["met"] for n in range(1, 7))
	return out


def current_package(doc):
	name = frappe.db.get_value(PACKAGE, {"award_case": doc.name, "cycle": doc.current_cycle}, "name", order_by="version desc")
	return frappe.get_doc(PACKAGE, name) if name else None


def _content(doc) -> dict[str, Any]:
	d = state.committed_decision(doc)
	opinion = state.signed_opinion(doc)
	rep = state.current_report(doc)
	snap = state.snapshot(rep)
	batch = state.current_batch(doc)
	notice = state.successful_notice(batch)
	response = state.operative_response(notice)
	rec = snap.get("recommended") or {}
	return {
		"award_case": doc.name, "tender": doc.tender, "tender_reference": doc.tender_reference, "lot": doc.lot, "cycle": doc.current_cycle,
		"report": {"id": rep.name, "version": rep.version_number, "digest": rep.content_digest, "source": rep.source_version},
		"opinion": {"id": opinion.name, "version": opinion.version, "digest": opinion.frozen_digest, "proof": opinion.proof_reference},
		"decision": {"id": d.name, "version": d.version, "outcome": d.outcome, "supplier": d.supplier_name, "organisation": d.supplier_organisation,
			"bid": d.bid_reference, "submitted_amount": d.submitted_amount, "evaluated_amount": d.evaluated_amount, "currency": d.currency},
		"notice_batch": {"id": batch.name, "version": batch.version, "notices": [{"id": n.name, "digest": n.content_digest, "given_at": str(n.given_at),
			"evidence": records.loads(n.evidence_json, [])} for n in state.notices(batch)]},
		"response": {"id": response.name, "response": response.response, "by": people.full_name(response.responder), "received_at": str(response.received_at),
			"authority": response.authority_evidence},
		"contract_terms": {"quantity": rec.get("quantity", ""), "warranty": rec.get("warranty", ""), "delivery_and_warranty": "As issued in the tender and the supplier's response",
			"reservation_treatment": "As recorded in the tender's reservation lineage", "performance_security": "As published in the tender (Contracting verifies before signature)",
			"tender_security": "As recorded at submission"},
		"restrictions": [{"id": i.name, "type": i.issue_type, "state": i.state, "disposition": i.disposition} for i in
			(frappe.get_doc(state.ISSUE, n) for n in frappe.get_all(state.ISSUE, filters={"award_case": doc.name}, pluck="name", order_by="creation asc"))],
		"legal_profile": profile.current().get("profile_version"), "fixture_namespace": doc.fixture_namespace,
	}


def _prepare_package(doc):
	pkg = current_package(doc)
	if pkg:
		return pkg
	content = _content(doc)
	version = records.next_number(PACKAGE, {"award_case": doc.name})
	return records.new(PACKAGE, package_id=f"{doc.name}-PKG-{version:02d}", award_case=doc.name, cycle=doc.current_cycle, decision=content["decision"]["id"],
		version=version, content_json=records.dumps(content), digest=records.digest(content), status="Prepared", attempts_json="[]", updates_json="[]",
		fixture_namespace=doc.fixture_namespace)


def deliver(doc) -> dict[str, Any]:
	"""DeliverAwardPackage: recheck 1–6, then deliver the same frozen package."""
	cond = conditions(doc)
	if not cond["ready"]:
		pkg = current_package(doc)
		if pkg and pkg.status != "Delivered":
			records.update(pkg, status="Held")
		return {"status": "Waiting", "conditions": cond}
	pkg = _prepare_package(doc)
	if pkg.status == "Delivered":
		return {"status": "Delivered", "package": pkg.name}
	stop = checks.funding_stop(doc)
	if stop:  # funding is rechecked at delivery (§5.5); unreadable is not "not restricted"
		records.update(pkg, status="Held")
		return {"status": "Waiting", "conditions": cond, "funding": stop}
	payload = {**records.loads(pkg.content_json), "reference": pkg.name, "package_digest": pkg.digest}
	attempt = {"at": str(clock.now())}
	try:
		result = contracting.deliver_package(payload)
	except contracting.ReceiverUnavailable as exc:
		attempt.update(outcome="Failed", detail=cstr(exc))
		records.append_json(pkg, "attempts_json", attempt)
		records.update(pkg, status="Failed")
		checks.open_support_issue(doc, "DeliverAwardPackage", f"package:{pkg.name}", "Restore Contracting delivery",
			"Operation: Award package delivery. Result: Contracting is unavailable. Delivery is retried after the conditions are checked again.")
		records.bump(doc)
		return {"status": "Failed", "package": pkg.name}
	attempt.update(outcome="Delivered", receipt=result["receipt"])
	records.append_json(pkg, "attempts_json", attempt)
	records.update(pkg, status="Delivered", receipt_reference=result["receipt"], received_at=result.get("received_at") or clock.now(),
		recipient_user=result.get("task_user") or None)
	checks.support_resolved(f"package:{pkg.name}")
	state.set_stage(doc, "Sent to Contracting", delivered_at=clock.now(), current_package=pkg.name)
	records.update(state.cycle(state.reload(doc)), outcome="Award")
	records.audit(doc.name, "DeliverAwardPackage", "system", package=pkg.name, receipt=result["receipt"])
	notify.tell(doc, [issues.hop_for(doc)], subject=f"Contracting has received the award for {doc.tender_reference}", key=f"delivered:{pkg.name}")
	return {"status": "Delivered", "package": pkg.name}


def _reply_state(doc) -> None:
	"""The reply deadline passed with no response: close the supplier's task
	and open one HOP issue (never a refusal)."""
	batch = state.current_batch(doc)
	notice = state.successful_notice(batch)
	if not notice or notice.status != "Given" or state.responses(notice):
		return
	deadline = clocks.reply_deadline_for(notice)
	if deadline and clock.now() > deadline:
		issues.open_issue(doc, source_event=f"no-response:{notice.name}", issue_type="Supplier response", subtype=RESPONSE_SUBTYPE_OVERDUE,
			title="The supplier has not replied by the deadline.", reason=f"Reply deadline: {clock.when(deadline)}", effective_at=deadline,
			detail={"notice": notice.name, "deadline": str(deadline)})


def refresh(doc) -> dict[str, Any]:
	"""RefreshAwardEligibility for one case (after every event and from the sweep)."""
	if doc.stage in ("Closed", "Sent to Contracting") or doc.cancelled:
		return {"status": doc.stage}
	checks.sync(doc)
	doc = state.reload(doc)
	if doc.stage == "Waiting to proceed":
		_reply_state(doc)
		doc = state.reload(doc)
		return deliver(doc)
	if doc.stage == "Notices":
		batch = state.current_batch(doc)
		if batch:
			notices.refresh_given(doc, batch)
	return {"status": state.reload(doc).stage}


def refresh_case(award: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		out = refresh(doc)
		return records.summary(state.reload(doc), **out)

	return records.command("RefreshAwardEligibility", case=award, idempotency_key=f"refresh:{award}:{frappe.generate_hash(length=10)}", actor="system",
		payload={}, body=body)


def sweep() -> int:
	count = 0
	for name in frappe.get_all(records.CASE, filters={"stage": ("in", ("Opinion", "Decision", "Notices", "Waiting to proceed"))}, pluck="name"):
		try:
			refresh_case(name)
			count += 1
		except Exception:
			frappe.log_error(title=f"Award eligibility refresh failed for {name}")
	return count
