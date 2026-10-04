# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-14 shows (BDS-CHG-001 v0.8 §10.15; plan Phase 11, slice
11.14): the Prepare replacement page and the withdrawal acknowledgement.

- Prepare replacement: the current submitted Version and its receipt stay
  current until a replacement is accepted; the Version, when it was
  submitted, the deadline and the addenda the current definition includes;
  Create replacement Draft only for the Authorised Signatory while the Tender
  is open before its deadline (`PrepareReplacementBid`'s own rules). Once a
  replacement Draft is open the page says so and leads to it.
- The acknowledgement: the withdrawal's own facts, Download acknowledgement,
  and Start replacement for the signatory before the deadline.

Nothing here changes anything."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import labels, tenders_gateway, withdrawal

REPLACE_TITLE = "Prepare replacement bid"
REPLACE_DESCRIPTION = "Create a new Draft while the submitted bid remains valid."
REPLACE_TEXT = "The new Draft copies your organisation's working responses and current published requirements. Review every changed value before submitting."
OPEN_DRAFT_TEXT = "Your replacement Draft is open. Version {number} remains submitted until the replacement is accepted."
WITHDRAWN_TITLE = "Bid withdrawn"
WITHDRAWN_DESCRIPTION = "Your withdrawal was acknowledged. The submitted history is retained."
# Guidance fixes these pages carry as their own actions.
PAGE_FIXES = ("prepare_replacement", "withdraw_bid", "start_replacement", "view_receipt")
API = "/api/method/kentender_procurement.bid_submission.api."


def _next_step(guided: dict[str, Any]) -> dict[str, Any]:
	answer = dict(guided["next_step"])
	moved = [f for f in answer.get("fixes") or [] if f.get("fix_id") in PAGE_FIXES]
	answer["fixes"] = [f for f in answer.get("fixes") or [] if f.get("fix_id") not in PAGE_FIXES]
	if moved and not answer.get("primary_action"):
		answer["primary_action"] = moved[0]["fix_id"]  # the page's own button performs it (KT-STD-001 §3B)
	return answer


def _addenda(ctx) -> str:
	ids = [cstr(g.published_facts.get("addendum_id")) for g in ctx.model.groups_of("documents") if (g.published_facts or {}).get("addendum_id")]
	return ", ".join(tenders_gateway.addendum_reference(ctx.workspace.tender, i) for i in ids) or "No addenda"


def replacement_page(ctx, guided: dict[str, Any], *, actor: str, at) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import reads

	ws = ctx.workspace
	base = f"/tenders/{ws.tender_reference}/bid"
	if not ws.current_submission_version:
		raise frappe.DoesNotExistError("This bid has no submitted Version to replace.")
	version = frappe.db.get_value("Bid Submission Version", ws.current_submission_version, ["version_number", "receipt"], as_dict=True)
	receipt = frappe.db.get_value("Bid Receipt", {"receipt_reference": version.receipt}, ["accepted_at"], as_dict=True) or {}
	root = tenders_gateway.tender_root(ws.tender_reference)
	number = int(version.version_number)
	receipt_href = f"{base}/receipt/{quote(version.receipt)}"
	open_draft = ws.status != "Submitted"
	from kentender_procurement.bid_submission.services import definition_runtime

	may_create = not open_draft and reads._may_start_replacement(actor, ws.lead_organisation, ws.tender_reference, at) and definition_runtime.bid_condition(ctx)["ok"]
	return {
		"bid": {"reference": ws.name, "tender_reference": ws.tender_reference, "record_version": int(ws.record_version or 0)},
		"page": {"title": REPLACE_TITLE, "description": REPLACE_DESCRIPTION, "badge": {"label": f"Version {number} submitted", "tone": "live"}},
		"next_step": _next_step(guided), "journey": guided["journey"],
		"notice": {"text": f"Receipt {version.receipt} remains current until the replacement is accepted.", "link": {"label": "View receipt", "href": receipt_href}},
		"facts": [
			{"label": "Current submitted bid Version", "value": str(number)},
			{"label": "Submitted", "value": labels.datetime_label(receipt.get("accepted_at")) if receipt else ""},
			{"label": "Deadline", "value": labels.datetime_label(root.submission_deadline) if root else ""},
			{"label": "Current definition includes", "value": _addenda(ctx)},
		],
		"text": OPEN_DRAFT_TEXT.format(number=number) if open_draft else REPLACE_TEXT,
		"decision": {"cancel_href": receipt_href, "create_label": "Create replacement Draft", "next_href": base} if may_create else None,
		"continue": {"label": "Continue replacement Draft", "href": base} if open_draft else None,
	}


def acknowledgement_page(change_facts: dict[str, Any], ctx, guided: dict[str, Any], *, actor: str, at) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import reads

	ws = ctx.workspace
	base = f"/tenders/{ws.tender_reference}/bid"
	title = cstr((tenders_gateway.published_tender(ws.tender_reference, at=at) or {}).get("title"))
	from kentender_procurement.bid_submission.services import definition_runtime

	may_restart = ws.status == "Withdrawn" and reads._may_start_replacement(actor, ws.lead_organisation, ws.tender_reference, at) and definition_runtime.bid_condition(ctx)["ok"]
	reference = change_facts["acknowledgement_reference"]
	return {
		"kind": "acknowledgement",
		"bid": {"reference": ws.name, "tender_reference": ws.tender_reference, "record_version": int(ws.record_version or 0)},
		"page": {"title": WITHDRAWN_TITLE, "description": WITHDRAWN_DESCRIPTION, "badge": {"label": "Withdrawn", "tone": "critical"}},
		"next_step": _next_step(guided), "journey": guided["journey"],
		"acknowledgement": [
			{"label": "Acknowledgement reference", "value": reference, "strong": True},
			{"label": "Tender", "value": f"{title} · {ws.tender_reference}" if title else ws.tender_reference},
			{"label": "Bidder", "value": change_facts["bidder"]},
			{"label": "Bid", "value": change_facts["bid_reference"]},
			{"label": "Withdrawn by", "value": change_facts["withdrawn_by"]},
			{"label": "Withdrawn at", "value": change_facts["withdrawn_at"]},
			{"label": "Status", "value": "Withdrawn", "status": {"label": "Withdrawn", "tone": "critical"}},
		],
		"footer": {
			"back_href": "/my-bids", "download_href": f"{API}download_withdrawal_acknowledgement?acknowledgement_reference={quote(reference)}",
			"start": {"label": "Start replacement", "next_href": base} if may_restart else None,
		},
	}


def get_replacement_page(*, tender_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import bid_context, clock, guidance, reads

	actor, at = cstr(user or frappe.session.user), clock.now()
	bid = reads.bid_for_tender(tender_reference=tender_reference, actor=actor, organisation=organisation, at=at)
	ctx = bid_context.load(bid, actor=actor, organisation=organisation, at=at)
	return replacement_page(ctx, guidance.for_bid(ctx, actor=actor, at=at), actor=actor, at=at)


def get_acknowledgement_page(*, tender_reference: str, acknowledgement_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import bid_context, clock, guidance

	actor, at = cstr(user or frappe.session.user), clock.now()
	facts = withdrawal.get_withdrawal_acknowledgement(acknowledgement_reference=acknowledgement_reference, organisation=organisation, user=actor)
	if facts["tender_reference"] != cstr(tender_reference):
		raise frappe.DoesNotExistError("This acknowledgement is unavailable or you do not have permission to view it.")
	ctx = bid_context.load(facts["bid_reference"], actor=actor, organisation=organisation, at=at)
	return acknowledgement_page(facts, ctx, guidance.for_bid(ctx, actor=actor, at=at), actor=actor, at=at)


def acknowledgement_html(facts: dict[str, Any]) -> str:
	"""The withdrawal acknowledgement's print/PDF view: plain HTML, no scripts."""
	from frappe.utils import escape_html

	rows = (("Acknowledgement reference", "acknowledgement_reference"), ("Tender", "tender_reference"), ("Bidder", "bidder"), ("Bid", "bid_reference"), ("Withdrawn Version", "withdrawn_version"),
		("Withdrawn receipt", "withdrawn_receipt"), ("Withdrawn by", "withdrawn_by"), ("Withdrawn at", "withdrawn_at"), ("Status", "status"))
	body = "".join(f"<dt>{escape_html(label)}</dt><dd>{escape_html(cstr(facts.get(key)))}</dd>" for label, key in rows if cstr(facts.get(key)))
	return (
		"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Withdrawal acknowledgement " + escape_html(facts["acknowledgement_reference"]) + "</title>"
		"<style>body{font-family:sans-serif;margin:32px;color:#1d2433}h1{font-size:22px}dl{display:grid;grid-template-columns:260px 1fr;gap:6px 16px}dt{color:#4a5468}dd{margin:0;font-weight:600}</style></head><body>"
		f"<h1>Bid withdrawn</h1><p>{escape_html(WITHDRAWN_DESCRIPTION)}</p><dl>{body}</dl><p>{escape_html(facts.get('notice') or '')}</p></body></html>"
	)
