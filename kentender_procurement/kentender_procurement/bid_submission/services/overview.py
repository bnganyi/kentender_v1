# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-DES-02 Published Tender overview (BDS-CHG-001 v0.8 §10.3, §11.2).

The public Tender facts from the Tenders projection — title, reference,
Procuring Entity, method, reservation, dates, what is being procured,
documents, addenda and anonymous clarification answers — and, for a
signed-in supplier, only their own organisation's bid state and the one
action that fits: Sign in to start bid (signed out), Set up account (no
Active Account), Start bid with the "Who is bidding?" choices, Continue bid,
View receipt, or none (closed without a bid, or cancelled with its notice).
A person from another organisation sees exactly what a new supplier sees; no
other supplier's bid fact is ever read here. The production-gate and outage
notices say what §5.10 says and promise nothing. A read creates nothing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import availability, clock, labels, supplier_gateway, tenders_gateway
from kentender_procurement.bid_submission.services import bid_authorization as authz

BEFORE_YOU_START = (
	"Sign in to start or continue a bid.",
	"Bid as one supplier organisation, or as a joint venture where this Tender permits it.",
	"An Authorised Signatory and a valid digital certificate are needed only when submitting.",
)
QUESTION_HELPER = "Start a bid to ask a question about this Tender. Starting does not submit a bid."
NOTICE_CONTACT_HELP = "Mandatory Tender notices will be sent here. You can change this later to another verified Account email."


DOCUMENT_METHOD = "/api/method/kentender_procurement.bid_submission.api.download_tender_document"


def document_href(reference: str, key: str, *, inline: bool) -> str:
	from urllib.parse import urlencode

	return f"{DOCUMENT_METHOD}?{urlencode({'tender_reference': reference, 'key': key, **({'inline': 1} if inline else {})})}"


def _date(value) -> str:
	return labels.date_label(value) if value else ""


def _facts(published: dict[str, Any]) -> dict[str, Any]:
	quantity = published.get("total_quantity") or {}
	return {
		"quantity": f"{quantity.get('quantity')} {quantity.get('unit')}".strip() if quantity else "",
		"delivery_location": cstr(published.get("delivery_location")), "latest_delivery": _date(published.get("latest_delivery")),
		"currency": cstr(published.get("currency")),
		"tender_security": labels.money_label(published.get("tender_security_amount"), cstr(published.get("currency"))) if published.get("tender_security_amount") else "Not required",
		"bid_validity": f"{int(published.get('validity_days') or 0)} days" if published.get("validity_days") else "",
	}


def _bid_state(reference: str, organisation: str, at) -> dict[str, Any] | None:
	from kentender_procurement.bid_submission.services import bid_context, readiness, reads

	name = frappe.db.get_value("Bid Workspace", {"tender_reference": reference, "lead_organisation": organisation}, "name", order_by="creation desc")
	if not name:
		return None
	ws = frappe.get_doc("Bid Workspace", name)
	out: dict[str, Any] = {"bid_reference": ws.name, "status": ws.status, "draft_version": int(ws.current_draft_version or 0), "href": f"/tenders/{reference}/bid"}
	if ws.current_submission_version:
		version = frappe.db.get_value("Bid Submission Version", ws.current_submission_version, ["version_number", "accepted_at", "receipt"], as_dict=True)
		out.update({"receipt_reference": version.receipt, "status_text": f"Submitted {labels.datetime_label(version.accepted_at)}", "receipt_href": f"/tenders/{reference}/bid/receipt/{version.receipt}"})
	if ws.status in ("Draft", "Needs attention", "Ready to submit"):
		tasks = [t for t in frappe.get_all("Bid Section Response", filters={"bid_workspace": ws.name}, fields=["section_key", "status"])]
		complete = sum(1 for t in tasks if t.status == "Complete")
		total = 5
		out["status_text"] = f"Draft · {complete} of {total} tasks complete" if ws.status != "Ready to submit" else "Ready to submit"
	_ = (bid_context, readiness, reads)
	return out


def _start_options(assignment: dict[str, Any], published: dict[str, Any], at) -> dict[str, Any]:
	organisation = assignment["organisation_id"]
	org = supplier_gateway.organisation(organisation_id=organisation) or {}
	current = tenders_gateway.current_definition(tenders_gateway.tender_root(published["reference"]).name) or {}
	from kentender_procurement.bid_submission.services import definition_runtime

	options = definition_runtime.arrangement_options(current.get("definition") or {}) if current else ["Single organisation"]
	return {
		"organisation": {"id": organisation, "legal_name": cstr(org.get("legal_name"))},
		"arrangements": options, "joint_venture_permitted": "Joint venture" in options,
		"notice_contacts": [{"contact_id": c["contact_id"], "value": c["value"]} for c in supplier_gateway.verified_contacts(organisation_id=organisation) if c.get("channel", "Email") == "Email"],
		"notice_contact_help": NOTICE_CONTACT_HELP,
		"signatories": [{"assignment_id": a["assignment_id"], "name": labels.person_name(a["user"])} for a in supplier_gateway.organisation_signatories(organisation_id=organisation, at=at)],
		"agreements": [{"evidence_id": e["evidence_id"], "title": cstr(e.get("file_name") or e.get("title"))} for e in supplier_gateway.account_evidence(organisation_id=organisation) if e.get("status") == "Available"],
	}


def get_tender_overview(*, tender_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	at = clock.now()
	reference = cstr(tender_reference).strip()
	published = tenders_gateway.published_tender(reference, at=at)
	if not published:
		raise frappe.DoesNotExistError("Tender not found.")
	actor = cstr(user or frappe.session.user)
	signed_in = bool(actor) and actor != "Guest"
	assignment = None
	if signed_in:
		try:
			assignment = authz.acting_assignment(actor, organisation, at=at)
		except frappe.ValidationError:
			assignment = None
	bid = _bid_state(reference, assignment["organisation_id"], at) if assignment else None
	state = published["availability"]  # open, closed or cancelled
	href = f"/tenders/{reference}"
	action: dict[str, Any] | None = None
	start = None
	if state == "cancelled":
		notice_key = (published.get("cancellation") or {}).get("notice_key")
		action = {"kind": "view_notice", "label": "View notice", "href": document_href(reference, notice_key, inline=True)} if notice_key else None
	elif bid and bid.get("receipt_reference") and bid["status"] == "Submitted":
		action = {"kind": "view_receipt", "label": "View receipt", "href": bid["receipt_href"]}
	elif bid and state == "open":
		action = {"kind": "continue_bid", "label": "Continue bid", "href": bid["href"]}
	elif bid:
		action = {"kind": "view_bid", "label": "View bid", "href": bid["href"]}
	elif state == "open" and not signed_in:
		action = {"kind": "sign_in", "label": "Sign in to start bid", "href": f"/login?redirect-to={href}"}
	elif state == "open" and not assignment:
		action = {"kind": "set_up_account", "label": "Set up your supplier account", "href": "/account"}
	elif state == "open":
		account = supplier_gateway.organisation(organisation_id=assignment["organisation_id"]) or {}
		if account.get("account_status") == "Active":
			action = {"kind": "start_bid", "label": "Start bid"}
			start = _start_options(assignment, published, at)
		else:
			action = {"kind": "set_up_account", "label": "Finish setting up your supplier account", "href": "/account"}
	notice = None
	if state == "open":
		gate = availability.get_submission_availability()
		if gate["code"] == "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED":
			notice = {"kind": "not_enabled", "title": "Electronic bid submission is not available yet", "text": "Preparation can be saved but cannot be submitted in this state. Check the deadline and use Supplier support for help."}
		elif gate["code"] in ("BDS_SIGNATURE_UNAVAILABLE", "BDS_SUBMISSION_SERVICE_UNAVAILABLE"):
			notice = {"kind": "outage", "title": "Electronic submission is temporarily unavailable", "text": "Your saved work is kept. Check the deadline and use Supplier support for help."}
	candidate = bool(bid) and frappe.db.get_value("Bidder Arrangement", frappe.db.get_value("Bid Workspace", bid["bid_reference"], "bidder_arrangement"), "status") == "Active"
	clarification_deadline = labels.datetime_label(published.get("clarification_deadline"))
	return {
		"tender": {
			"reference": reference, "title": published["title"], "description": " · ".join(x for x in (published["procuring_entity"], published["method"], published["reservation"] and f"{published['reservation']} reservation") if x) + ".",
			"availability": state, "status_label": {"open": "", "closed": "Closed", "cancelled": "Cancelled"}[state],
			"deadline": labels.datetime_label(published["submission_deadline"]), "published": labels.datetime_label(published["published_at"]),
			"clarification_deadline": clarification_deadline, "clarifications_open": bool(published.get("clarifications_open")),
			"clarification_label": "Clarification deadline" if published.get("clarifications_open") else "Clarifications closed",
		},
		"organisation": {"id": assignment["organisation_id"], "legal_name": cstr((supplier_gateway.organisation(organisation_id=assignment["organisation_id"]) or {}).get("legal_name"))} if assignment else None,
		"facts": _facts(published),
		"documents": [
			{"key": d["key"], "label": d["label"], "published": _date(d["published_at"]), "view_href": document_href(reference, d["key"], inline=True), "download_href": document_href(reference, d["key"], inline=False)}
			for d in published.get("documents") or []
		],
		"addenda": [
			{"reference": a["reference"], "summary": a["summary"], "issued": labels.datetime_label(a["issued_at"]), "current_deadline": labels.datetime_label(published["submission_deadline"]),
			 "view_href": document_href(reference, a["document_key"], inline=True) if a.get("document_key") else ""}
			for a in published.get("addenda") or []
		],
		"answers": [
			{"question": cstr(q.get("question")), "answer": cstr(q.get("answer")), "answered": labels.datetime_label(q.get("answered_at"))}
			for q in published.get("answers") or []
		],
		"clarification": {
			"can_ask": bool(candidate and published.get("clarifications_open")),
			"helper": QUESTION_HELPER if (state == "open" and published.get("clarifications_open") and not bid) else "",
			"closed_text": "" if published.get("clarifications_open") else (f"Clarifications closed {clarification_deadline}." if clarification_deadline else ""),
		},
		"notice": notice, "bid": bid, "action": action, "start": start, "before_you_start": list(BEFORE_YOU_START),
		"cancellation": {"cancelled": labels.datetime_label((published.get("cancellation") or {}).get("cancelled_at"))} if state == "cancelled" else None,
		"signed_in": signed_in,
	}
