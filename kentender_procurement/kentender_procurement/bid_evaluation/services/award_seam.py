# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Evaluation side of the Award contract (AWD-CHG-001 v0.4 §3 entry
contract, AWD-IF-01; Award plan D5).

Award reads the exact delivered report here — never Evaluation's doctypes —
and takes the Head of Procurement's "Review evaluation report" task up as its
own "Prepare professional opinion" (one work item, no second
acknowledgement). Returns keep Evaluation's own correction route: a return
before a decision is the ordinary `ReturnEvaluationReport`; after a committed
decision only the Accounting Officer's recorded correction instruction can
send the report back (EVL v0.4 §5.6). Post-delivery correction notices and
opening updates are handed to Award as its review items. Evaluation findings,
rankings and amounts stay read-only."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import records, roster

DELIVERY = "Evaluation Report Delivery"
VERSION = "Evaluation Report Version"
WITH_AWARD = "With Award"


def notify_consumers(hook: str, **kwargs) -> None:
	"""Call every consumer of `hook`; a consumer's failure is rolled back to its
	own savepoint and left for its owner's retry, never failing Evaluation."""
	for path in frappe.get_hooks(hook) or []:
		savepoint = f"evl_award_{frappe.generate_hash(length=8)}"
		frappe.db.savepoint(savepoint)
		try:
			frappe.get_attr(path)(**kwargs)
		except Exception:
			frappe.db.rollback(save_point=savepoint)
			frappe.log_error(title=f"Evaluation consumer {path} failed")
			failed = frappe.get_hooks(f"{hook}_failed") or []
			for fallback in failed:
				try:
					frappe.get_attr(fallback)(**kwargs)
				except Exception:
					frappe.log_error(title=f"Evaluation consumer fallback {fallback} failed")
		else:
			frappe.db.release_savepoint(savepoint)


def _amount(value) -> str:
	return cstr(value or "")


def _warranty(findings: list[dict[str, Any]], bid: str) -> str:
	for row in findings:
		if row.get("bid") != bid:
			continue
		for group in ("eligibility", "technical", "responsiveness"):
			for r in row.get(group) or []:
				if cstr(r.get("requirement_key")).endswith("WS-MINIMUM-WARRANTY"):
					parts = [p.strip() for p in cstr(r.get("evidence")).split(";") if p.strip()]
					value = next((p for p in reversed(parts) if p[:1].isdigit()), "")
					return value
	return ""


def delivered_report(delivery: str) -> dict[str, Any] | None:
	"""The exact delivered report version, its signatures and the facts Award
	shows, with the content digest verified by recomputation."""
	from kentender_procurement.bid_evaluation.services import signing

	row = frappe.db.get_value(DELIVERY, delivery, ["name", "evaluation_case", "report_version", "recipient_user", "status", "delivered_at", "review_state",
		"fixture_namespace"], as_dict=True)
	if not row or row.status != "Delivered":
		return None
	case = frappe.db.get_value(records.CASE, row.evaluation_case, ["name", "tender", "tender_reference", "state", "fixture_namespace"], as_dict=True)
	version = frappe.get_doc(VERSION, row.report_version)
	content = json.loads(version.content_json or "{}")
	# the digest is Evaluation's own: over the frozen JSON text itself (signing.send_for_signing)
	verified = records.digest(version.content_json or "") == version.content_digest
	sigs = signing.signatures(version)
	bids = {b.name: b for b in frappe.get_all("Evaluation Bid", filters={"evaluation_case": case.name}, fields=["name", "bid_reference", "organisation_id",
		"tenderer_name", "submitted_total", "currency", "submission_version"])}
	comparison = []
	for r in (content.get("financial_comparison") or {}).get("rows") or []:
		bid = bids.get(r.get("bid")) or frappe._dict()
		comparison.append({"bid": r.get("bid"), "bid_reference": cstr(bid.bid_reference), "organisation": cstr(bid.organisation_id), "bidder": r.get("bidder"),
			"submitted_total": _amount(r.get("submitted_total")), "evaluated_total": _amount(r.get("evaluated_total")), "position": r.get("position"),
			"responsiveness": r.get("responsiveness"), "currency": r.get("currency") or "KES", "submission_version": cstr(bid.submission_version)})
	recommendation = content.get("recommendation") or {}
	recommended = None
	if recommendation.get("recommended") and version.outcome == "Recommendation":
		r = recommendation["recommended"]
		bid = bids.get(r.get("bid")) or frappe._dict()
		recommended = {"bid": r.get("bid"), "bid_reference": cstr(bid.bid_reference), "organisation": cstr(bid.organisation_id), "bidder": r.get("bidder"),
			"submitted_total": _amount(r.get("submitted_total")), "evaluated_total": _amount(r.get("evaluated_total")), "currency": r.get("currency") or "KES",
			"position": r.get("position"), "responsiveness": r.get("responsiveness"), "submission_version": cstr(bid.submission_version),
			"warranty": _warranty(content.get("bid_findings") or [], r.get("bid"))}
		prices = [p for p in ((content.get("financial_comparison") or {}).get("prices") or []) if p.get("bid") == r.get("bid")]
		lines = prices[0].get("lines") if prices else []
		if lines:
			recommended["quantity"] = f"{cstr(lines[0].get('quantity'))} {cstr(lines[0].get('unit'))}".strip()
	members = ((content.get("tender_and_committee") or {}).get("members")) or []
	# everyone who sat on the panel under any appointment of this evaluation (a replaced member evaluated too), and every secretary
	appointments = frappe.get_all(roster.APPOINTMENT, filters={"evaluation_case": case.name}, pluck="name")
	seated = frappe.get_all("Evaluation Committee Member", filters={"parent": ("in", appointments or [""])}, fields=["member_user", "capacity"])
	secretaries = frappe.get_all("Evaluation Secretary Appointment", filters={"evaluation_case": case.name}, pluck="secretary_user")
	panel = {"members": [{"user": m.member_user, "capacity": m.capacity} for m in seated], "chair": cstr(roster.chair(case.name)),
		"secretary": cstr(roster.secretary(case.name)), "secretaries": sorted({u for u in secretaries if u})}
	return {
		"source_kind": "Evaluation", "delivery": row.name, "source_case": case.name, "report": version.name, "version": version.version_number,
		"content_digest": version.content_digest, "digest_verified": verified, "delivered_at": row.delivered_at, "recipient": row.recipient_user,
		"fixture_namespace": cstr(case.fixture_namespace), "tender": case.tender, "tender_reference": case.tender_reference,
		"panel": panel,
		"signatures": {"required": len(sigs), "signed": len([s for s in sigs if s.get("signed_at")]),
			"members": [{"user": s["member"], "name": s["name"], "signed_at": s["signed_at"]} for s in sigs]},
		"sections": content.get("sections") or [], "annexes": [{"name": s, "available": True} for s in (content.get("sections") or [])],
		"outcome": version.outcome, "reason": recommendation.get("reason") or (content.get("summary") or {}).get("reason") or "",
		"qualifications": json.loads(version.qualifications_json or "[]"), "funding": recommendation.get("funding") or {},
		"recommended": recommended, "comparison": comparison, "committee": [m.get("name") for m in members],
		"dissent": [d for d in ((content.get("clarifications_and_record") or {}).get("disagreements") or [])],
		"narrative": content.get("narrative") or "",
	}


def pending_deliveries() -> list[str]:
	"""Delivered reports still waiting for Award to receive them (the retry of
	a failed receipt keeps the delivery's own identity)."""
	return frappe.get_all(DELIVERY, filters={"status": "Delivered", "review_state": "Open"}, pluck="name", order_by="delivered_at asc")


def take_up(delivery: str) -> None:
	"""Award received the report: the recipient's Evaluation review task
	becomes Award's "Prepare professional opinion" (AWD §3)."""
	row = frappe.get_doc(DELIVERY, delivery)
	if row.review_state == "Open":
		records.save(row.update({"review_state": WITH_AWARD}))


def return_report(*, delivery: str, comment: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""ReturnEvaluationReport before a committed decision (EVL's own command)."""
	from kentender_procurement.bid_evaluation.services import correction

	case = frappe.db.get_value(DELIVERY, delivery, "evaluation_case")
	tender = frappe.db.get_value(records.CASE, case, "tender")
	return correction.return_report(tender=tender, comment=comment, idempotency_key=idempotency_key, user=user)


def return_for_correction(*, delivery: str, comment: str, instruction: str, authorised_by: str, idempotency_key: str) -> dict[str, Any]:
	"""After a committed decision: the AO's recorded correction instruction."""
	from kentender_procurement.bid_evaluation.services import correction

	case = frappe.db.get_value(DELIVERY, delivery, "evaluation_case")
	tender = frappe.db.get_value(records.CASE, case, "tender")
	return correction.return_for_authorised_correction(tender=tender, comment=comment, instruction=instruction, authorised_by=authorised_by,
		idempotency_key=idempotency_key)


def corrections_after(tender: str) -> list[dict[str, Any]]:
	"""Correction notices and post-delivery opening updates not yet taken up by
	Award, oldest first, each with a stable source identity."""
	case = records.case_for(tender)
	if not case:
		return []
	out = []
	for n in frappe.get_all("Evaluation Correction Notice", filters={"evaluation_case": case, "head_review_state": "Open"},
			fields=["name", "reason", "correction", "recorded_at", "recorded_by", "report_version"], order_by="recorded_at asc"):
		out.append({"source_event": f"EVL-CN:{n.name}", "kind": "Report correction", "reference": n.name, "reason": cstr(n.reason),
			"detail": cstr(n.correction), "effective_at": n.recorded_at, "authority": cstr(n.recorded_by), "report": n.report_version})
	for e in frappe.get_all("Evaluation Source Event", filters={"evaluation_case": case, "kind": "Opening supplement", "delivered_context": "After delivery",
			"head_review_state": "Open"}, fields=["name", "reason", "detail_json", "effective_at", "authority"], order_by="received_at asc"):
		detail = json.loads(e.detail_json or "{}")
		out.append({"source_event": f"EVL-SE:{e.name}", "kind": "Opening update", "reference": e.name, "reason": cstr(e.reason),
			"detail": cstr(detail.get("text")), "effective_at": e.effective_at, "authority": cstr(e.authority), "report": ""})
	return out


def take_up_correction(reference: str) -> None:
	"""Award took the correction up as its own review item."""
	for doctype in ("Evaluation Correction Notice", "Evaluation Source Event"):
		if frappe.db.exists(doctype, reference):
			doc = frappe.get_doc(doctype, reference)
			if doc.head_review_state == "Open":
				records.save(doc.update({"head_review_state": WITH_AWARD}))
			return
