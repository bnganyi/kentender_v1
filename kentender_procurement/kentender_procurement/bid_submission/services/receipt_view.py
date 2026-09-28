# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-13 shows (BDS-CHG-001 v0.8 §10.14; plan Phase 11, slice
11.13), and the receipt composition BDS-DES-14-REPLACED reuses (§10.15):

- the heading (Bid submitted, or Replacement bid submitted when the receipt
  replaced an earlier one) and the status badge;
- the header actions this viewer may take on this receipt: Prepare
  replacement and Withdraw bid for the Authorised Signatory while this is the
  current receipt and the Tender is open before its deadline (the same rules
  as `PrepareReplacementBid` and `WithdrawBid`); Print receipt for everyone;
- the receipt facts and the submission summary recorded at acceptance —
  nothing technical;
- the lineage (the Version this one superseded, with its receipt);
- the one factual sentence: the current bid stays valid until a replacement
  or withdrawal, or submission changes closed at the deadline.

Nothing here changes anything."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import labels, receipts, tenders_gateway

TITLE = "Bid submitted"
REPLACEMENT_TITLE = "Replacement bid submitted"
DESCRIPTION = "Your bid was accepted into the electronic tender box."
REPLACEMENT_DESCRIPTION = "Your replacement bid was accepted into the electronic tender box."
STILL_VALID = "The current submitted bid remains valid until a replacement is accepted or a withdrawal is acknowledged."
STATUS_TONES = {"Submitted": "live", "Superseded": "draft", "Withdrawn": "critical"}
# The receipt's own header actions stand in for these guidance fixes.
PAGE_FIXES = ("prepare_replacement", "withdraw_bid", "view_receipt")
API = "/api/method/kentender_procurement.bid_submission.api."


def _version_number(receipt) -> int:
	return int(receipt.version_number or 0)


def view(receipt, ctx, guided: dict[str, Any], *, actor: str, at) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import reads

	ws = ctx.workspace
	facts = receipts.facts(receipt)
	base = f"/tenders/{ws.tender_reference}/bid"
	root = tenders_gateway.tender_root(ws.tender_reference)
	closed = bool(root and root.submission_deadline and get_datetime(at) >= get_datetime(root.submission_deadline))
	current = ws.status == "Submitted" and cstr(frappe.db.get_value("Bid Submission Version", ws.current_submission_version, "receipt")) == receipt.receipt_reference
	may_change = current and not closed and reads._may_start_replacement(actor, ws.lead_organisation, ws.tender_reference, at)
	from kentender_procurement.bid_submission.services import definition_runtime

	# §4.4.4: on a Withdrawn or failed release the bid may still be withdrawn,
	# but no replacement is prepared against it
	may_replace = may_change and definition_runtime.bid_condition(ctx)["ok"]
	reference = quote(receipt.receipt_reference)
	status = facts["status"]

	actions = []
	if may_replace:
		actions.append({"key": "prepare_replacement", "label": "Prepare replacement", "href": f"{base}/replace", "tone": "secondary"})
	if may_change:
		actions.append({"key": "withdraw_bid", "label": "Withdraw bid", "href": "", "tone": "danger"})
	actions.append({"key": "print", "label": "Print receipt", "href": f"{API}download_bid_receipt?receipt_reference={reference}&inline=1", "tone": "primary"})

	predecessor = cstr(receipt.predecessor_receipt)
	lineage = None
	if predecessor:
		earlier = frappe.db.get_value("Bid Receipt", {"receipt_reference": predecessor}, "version_number")
		number = int(earlier or 0)
		lineage = {"status": {"label": f"Version {number} superseded", "tone": "pending"}, "link": {"label": f"View Version {number} receipt · {predecessor}", "href": f"{base}/receipt/{quote(predecessor)}"}}

	if closed and current:
		sentence = f"Submission changes closed on {facts['deadline']}."
	elif may_change:
		sentence = STILL_VALID
	else:
		sentence = ""

	next_step = dict(guided["next_step"])
	moved = [f for f in next_step.get("fixes") or [] if f.get("fix_id") in PAGE_FIXES]
	next_step["fixes"] = [f for f in next_step.get("fixes") or [] if f.get("fix_id") not in PAGE_FIXES]
	if moved and not next_step.get("primary_action"):
		next_step["primary_action"] = moved[0]["fix_id"]  # the page's own button performs it (KT-STD-001 §3B: never a your-turn without a way to act)
	summary = facts["summary"]
	return {
		"kind": "receipt",
		"bid": {"reference": ws.name, "tender_reference": ws.tender_reference, "record_version": int(ws.record_version or 0)},
		"page": {"title": REPLACEMENT_TITLE if predecessor else TITLE, "description": REPLACEMENT_DESCRIPTION if predecessor else DESCRIPTION, "badge": {"label": status, "tone": STATUS_TONES.get(status, "draft")}},
		"actions": actions, "next_step": next_step, "journey": guided["journey"],
		"receipt": [
			{"label": "Receipt reference", "value": receipt.receipt_reference, "strong": True},
			{"label": "Tender", "value": receipt.tender_reference},
			{"label": "Bidder", "value": facts["bidder"]},
			{"label": "Bid", "value": facts["bid_reference"]},
			{"label": "Submitted bid Version", "value": str(_version_number(receipt))},
			{"label": "Submitted by", "value": facts["submitted_by"]},
			{"label": "Received by tender-box service", "value": facts["received_at"]},
			{"label": "Accepted into tender box", "value": facts["accepted_at"]},
			{"label": "Status", "value": status, "status": {"label": status, "tone": STATUS_TONES.get(status, "draft")}},
		],
		"lineage": lineage,
		"summary": [
			{"label": "Bid total", "value": summary["bid_total"] or "—", "strong": True},
			{"label": "Offered item", "value": summary["offered_item"] or "—"},
			{"label": "Quantity", "value": summary["quantity"] or "—"},
			{"label": "Delivery date", "value": summary["delivery_date"] or "—"},
			{"label": "Current deadline", "value": facts["deadline"]},
		],
		"notice": facts["notice"], "sentence": sentence,
		"withdrawal": {"receipt_reference": receipt.receipt_reference, "deadline": facts["deadline"]} if may_change else None,
		"footer": {"back_href": "/my-bids", "download_href": f"{API}download_bid_receipt?receipt_reference={reference}"},
	}


def get_receipt_page(*, tender_reference: str, receipt_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""BDS-DES-13 for a receipt of the acting organisation's own bid on this
	Tender; a receipt of another Tender (or organisation) is Not found."""
	from kentender_procurement.bid_submission.services import bid_context, clock, guidance

	actor, at = cstr(user or frappe.session.user), clock.now()
	receipt = receipts._load(receipt_reference, actor=actor, organisation=organisation)
	if receipt.tender_reference != cstr(tender_reference):
		raise frappe.DoesNotExistError("This receipt is unavailable or you do not have permission to view it.")
	ctx = bid_context.load(receipt.bid_workspace, actor=actor, organisation=organisation, at=at)
	return view(receipt, ctx, guidance.for_bid(ctx, actor=actor, at=at), actor=actor, at=at)
