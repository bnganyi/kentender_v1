# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-12 shows (BDS-CHG-001 v0.8 §10.13; plan Phase 11, slice
11.12), decided here from `GetSubmitBid` (the same checks `SubmitBid` runs),
the guidance and the latest attempt:

- the consequence and the final confirmation only when this person can
  submit now; the pending state (no new Submit, View status) while an
  attempt is being checked;
- one notice for each operating state — the production switch, a signing
  outage, a custody outage — with the support route, and the one way back
  (Back to bid; Continue saved bid while portal information is restored);
- the trusted server time and the deadline, the submission summary, and the
  Authorised Signatory with the certificate as the trust service reports it;
- the confirmation dialog's four facts.

Nothing here saves, signs or submits anything."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import availability, common_states, company_view, labels, readiness, submission, tender_security, tenders_gateway, workspace_view

TITLE = "Submit bid"
DESCRIPTION = "Digitally sign and place this bid in the electronic tender box."
DIALOG_TITLE = "Submit this bid?"
PENDING_TEXT = "We are checking this submission attempt. You may leave and return through View status. Do not submit again while this attempt is pending."
CFG_SENTENCE = "Saved work and receipts remain available while required supplier portal information is restored."
# §10.13 GATE, SIGNATURE and SERVICE results: (title, text, offers View status).
NOTICES = {
	"BDS_PRODUCTION_SUBMISSION_NOT_ENABLED": ("Electronic bid submission is not available yet", "Your bid remains saved and has not been submitted.", False),
	"BDS_SIGNATURE_UNAVAILABLE": ("Digital signing is temporarily unavailable", "Your bid remains saved and has not been submitted. The signing service is being restored.", False),
	"BDS_SUBMISSION_SERVICE_UNAVAILABLE": ("Electronic submission is temporarily unavailable", "Your bid remains saved and no receipt exists.", True),
}
CERTIFICATE = {"Ready": ("Ready", "live"), "Required": ("Not available", "critical")}
# Guidance fixes that would lead back to review or repeat this page's own action.
PAGE_FIXES = ("review_bid", "continue_bid")


def _support_links() -> list[dict[str, str]]:
	from kentender_core.services import public_portal

	email = cstr((public_portal.get_public_portal_information().get("support") or {}).get("email"))
	return [{"label": "Supplier support", "href": f"mailto:{email}"}] if email else []


def acknowledgements(ctx) -> str:
	"""Each effective addendum this Draft acknowledged, as "{reference} ·
	{when}"; what is still due otherwise."""
	parts, due = [], False
	for group in ctx.model.groups_of("documents"):
		addendum_id = cstr((group.published_facts or {}).get("addendum_id"))
		keys = [f.key for f in group.fields if f.kind == "confirmation"]
		if not addendum_id or not keys:
			continue
		if not all(ctx.values.get(k) for k in keys):
			due = True
			continue
		when = frappe.db.get_value("Bid Draft Change", {"bid_workspace": ctx.workspace.name, "response_key": ("in", keys), "new_value": "true"}, "changed_at", order_by="changed_at desc")
		reference = tenders_gateway.addendum_reference(ctx.workspace.tender, addendum_id)
		parts.append(f"{reference} · {labels.datetime_label(when)}" if when else reference)
	if due:
		return "Not yet acknowledged"
	return "; ".join(parts) or "No addendum to acknowledge"


def _security_receipt(ctx) -> str:
	security = tender_security.response(ctx)
	if not security.get("required"):
		return "Not required"
	if security["physical_receipt_status"] == tender_security.NOT_RECORDED:
		return "Not yet recorded"
	return f"{security['physical_receipt_reference']} · {security['physical_received_at']}"


def _signatory(ctx, *, at) -> list[dict[str, Any]]:
	person = company_view.signatory(ctx, at=at) or {}
	label, tone = CERTIFICATE.get((person.get("certificate") or {}).get("status"), ("Not checked", "draft"))
	return [
		{"label": "Signatory", "value": person.get("name") or "—"},
		{"label": "Job title", "value": person.get("job_title") or "—"},
		{"label": "Authority evidence", "value": "Available" if person.get("authority_available") else "Not available"},
		{"label": "Digital certificate", "value": label, "status": {"label": label, "tone": tone}},
	]


def view(ctx, read: dict[str, Any], *, at) -> dict[str, Any]:
	ws = ctx.workspace
	base = f"/tenders/{ws.tender_reference}/bid"
	root = tenders_gateway.tender_root(ws.tender_reference)
	deadline = labels.datetime_label(root.submission_deadline) if root else ""
	codes = {b["reason_code"] for b in (read.get("submit_guard") or {}).get("blockers") or []}
	summary = read["summary"]
	attempt = frappe.get_all("Bid Submission Attempt", filters={"bid_workspace": ws.name}, fields=["status"], order_by="creation desc", limit_page_length=1)
	rejected = bool(attempt) and attempt[0].status == "Rejected"
	pending = "BDS_SUBMISSION_UNCERTAIN" in codes

	confirm = {"kind": "confirm", "confirmation": read["confirmation_label"], "submit_label": "Submit bid", "cancel_href": f"{base}/review"} if read["can_submit"] else None
	if pending:
		decision = {"kind": "pending", "text": PENDING_TEXT, "status_href": f"{base}/status", "submit_label": "Submitting bid…"}
	else:
		# after a definite rejection the confirmation returns only when the
		# signatory chooses Try confirmation again (`retry`)
		decision = None if rejected else confirm

	notice = None
	gate = availability.get_submission_availability()["code"] if ws.status not in workspace_view.CLOSED_STATES else ""
	if gate in NOTICES:
		title, text, status = NOTICES[gate]
		notice = {"tone": "critical", "title": title, "text": text, "links": ([{"label": "View status", "href": f"{base}/status"}] if status else []) + _support_links()}

	action = None
	if gate == "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED":
		action = {"label": "Back to bid", "href": base, "tone": "secondary"}
	elif "BDS_PORTAL_INFORMATION_UNAVAILABLE" in codes:
		nav = readiness.evaluate(ctx)
		first_open = next((key for key, state in nav.items() if key != readiness.REVIEW_TASK and state.status != "Complete"), "")
		action = {"label": "Continue saved bid", "href": f"{base}/{first_open}" if first_open else base, "tone": "secondary"}

	# §10.17 Deadline passed replaces the page for a bid that was not submitted
	from frappe.utils import get_datetime

	closed = bool(root and root.submission_deadline and get_datetime(at) >= get_datetime(root.submission_deadline))
	state = common_states.state("deadline-passed", href="/my-bids", deadline=deadline, current_time=labels.datetime_seconds_label(at)) if closed and ws.status != "Submitted" else None

	next_step = dict(read["next_step"])
	next_step["fixes"] = [f for f in next_step.get("fixes") or [] if f.get("fix_id") not in PAGE_FIXES]
	if "BDS_PORTAL_INFORMATION_UNAVAILABLE" in codes and next_step.get("kind") == "waiting":
		next_step["sentence"] = CFG_SENTENCE

	return {
		"bid": {"reference": ws.name, "tender_reference": ws.tender_reference, "record_version": int(ws.record_version or 0)},
		# a replacement names the receipt the signatory saw as current (`SubmitReplacementBid`)
		"replaces": cstr(frappe.db.get_value("Bid Submission Version", ws.current_submission_version, "receipt")) if ws.current_submission_version else "",
		"page": {"title": TITLE, "description": DESCRIPTION, "back_href": f"{base}/review", "back_label": "Back to review"},
		"next_step": next_step, "journey": read["journey"],
		"consequence": {"tone": "warning", "text": read["consequence"]} if decision else None,
		"notice": notice, "action": action,
		"meta": [{"label": "Current server time", "value": read["current_time"]}, {"label": "Submission deadline", "value": deadline}],
		"summary": [
			{"label": "Tender", "value": f"{summary['tender_title']} · {summary['tender']}"},
			{"label": "Bidder", "value": summary["bidder"]},
			{"label": "Bid", "value": f"{ws.name} · Draft Version {int(ws.current_draft_version or 0)}"},
			{"label": "Bid total", "value": summary["bid_total"] or "—", "strong": True},
			{"label": "Current deadline", "value": deadline},
			{"label": "Addendum acknowledged", "value": acknowledgements(ctx)},
			{"label": "Tender-security physical receipt", "value": _security_receipt(ctx)},
		],
		"signatory": _signatory(ctx, at=at),
		"decision": decision,
		"dialog": {
			"title": DIALOG_TITLE, "text": read["dialog_text"],
			"facts": [{"label": "Tender", "value": summary["tender"]}, {"label": "Bidder", "value": summary["bidder"]}, {"label": "Bid total", "value": summary["bid_total"]}, {"label": "Deadline", "value": deadline}],
		},
		"support_href": (_support_links() or [{"href": ""}])[0]["href"],
		"state": state,
		"retry": confirm if rejected else None,
	}


def get_submit_page(*, tender_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""The Submit page for the acting organisation's own bid on this Tender."""
	from kentender_procurement.bid_submission.services import bid_context, clock, reads

	actor, at = cstr(user or frappe.session.user), clock.now()
	bid = reads.bid_for_tender(tender_reference=tender_reference, actor=actor, organisation=organisation, at=at)
	read = submission.get_submit_bid(bid_reference=bid, organisation=organisation, user=actor)
	ctx = bid_context.load(bid, actor=actor, organisation=organisation, at=at)
	return view(ctx, read, at=at)
