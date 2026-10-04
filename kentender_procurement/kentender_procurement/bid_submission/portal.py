# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Submission's portal surface (`kt_portal_surfaces`; BDS-CHG-001 v0.8
plan OD-B). `resolve` answers every path the surface owns with the verdict
and the first payload the screen paints from (KT-STD-001 §3A.1). Screens are
added slice by slice (plan Phase 11); a path with no screen yet is
NOT_FOUND, never a guess. The surface also answers `/my-bids` and
`/account/receipts` (a longer prefix than Supplier Accounts' `/account`)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_submission.services import reads

FILTER_KEYS = ("search", "method", "reservation", "closing")
# The task pages built so far (plan Phase 11 slices); any other task key is Not found.
TASK_SCREENS = {
	"documents": ("documents-task", "Tender documents, clarifications and addenda"),
	"company": ("company-task", "Company, declarations and tender security"),
	"requirements": ("requirements-task", "Requirements and supporting evidence"),
	"price": ("price-task", "Price"),
	"review": ("review-task", "Review bid"),
}


def resolve(*, path: str, query: dict[str, Any], user: str) -> dict[str, Any]:
	segments = [s for s in path.split("/") if s]
	if segments == ["tenders"]:
		filters = {k: str(query.get(k) or "") for k in FILTER_KEYS if query.get(k)}
		return {"verdict": "OK", "title": "Available Tenders", "payload": {"screen": "available-tenders", "data": reads.get_available_tenders(**filters)}}
	if len(segments) == 2 and segments[0] == "tenders":
		from kentender_procurement.bid_submission.services import overview

		try:
			data = overview.get_tender_overview(tender_reference=segments[1], user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Tender not found", "payload": {"screen": "tender-not-found"}}
		title = data["tender"]["reference"] if data["tender"]["availability"] == "cancelled" else data["tender"]["title"]
		return {"verdict": "OK", "title": title, "payload": {"screen": "tender-overview", "data": data}}
	if len(segments) == 3 and segments[0] == "tenders" and segments[2] == "opening":
		# BOP-CHG-001 v0.10 plan D10 (tracker BDS8-B04): Bid Opening's public page,
		# answered by its own resolver; Bid Submission never reads the opening.
		for path in frappe.get_hooks("kt_tender_opening_portal") or []:
			return frappe.get_attr(path)(tender_reference=segments[1], user=user)
		return {"verdict": "NOT_FOUND", "title": "Tender not found", "payload": {"screen": "tender-not-found"}}
	if len(segments) == 5 and segments[0] == "tenders" and segments[2] == "bid" and segments[3] == "evaluation-clarifications":
		# EVL-CHG-001 v0.4 plan D14 (tracker BDS8-B07): the evaluation committee's
		# question to this organisation, answered by Bid Evaluation's own resolver.
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		for path in frappe.get_hooks("kt_tender_evaluation_portal") or []:
			return frappe.get_attr(path)(tender_reference=segments[1], clarification=segments[4], organisation=str(query.get("organisation") or ""), user=user)
		return {"verdict": "NOT_FOUND", "title": "Not found", "payload": {"screen": "not-found"}}
	if len(segments) == 3 and segments[0] == "tenders" and segments[2] == "bid":
		# BDS-DES-06: the signed-in organisation's own bid for this Tender
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		try:
			data = reads.get_bid_workspace(tender_reference=segments[1], organisation=str(query.get("organisation") or ""), user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Bid not found", "payload": {"screen": "not-found"}}
		return {"verdict": "OK", "title": "Your bid", "payload": {"screen": "workspace", "data": {"outcome": "OK", **data}}}
	if len(segments) == 5 and segments[0] == "tenders" and segments[2] == "bid" and segments[3] == "receipt":
		# BDS-DES-13: a receipt of the organisation's own bid on this Tender
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		from kentender_procurement.bid_submission.services import changes_view, receipt_view

		organisation = str(query.get("organisation") or "")
		try:
			if segments[4].startswith("WD-"):  # BDS-DES-14-WITHDRAWN: the withdrawal acknowledgement
				data = changes_view.get_acknowledgement_page(tender_reference=segments[1], acknowledgement_reference=segments[4], organisation=organisation, user=user)
				return {"verdict": "OK", "title": data["page"]["title"], "payload": {"screen": "receipt", "data": {"outcome": "OK", **data}}}
			data = receipt_view.get_receipt_page(tender_reference=segments[1], receipt_reference=segments[4], organisation=organisation, user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Receipt not found", "payload": {"screen": "receipt-not-found"}}
		return {"verdict": "OK", "title": data["page"]["title"], "payload": {"screen": "receipt", "data": {"outcome": "OK", **data}}}
	if len(segments) == 4 and segments[0] == "tenders" and segments[2] == "bid" and segments[3] == "status":
		# §11.5 View status: one §10.17 common state, or straight to the receipt
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		from kentender_procurement.bid_submission.services import status_view

		try:
			data = status_view.get_status_page(tender_reference=segments[1], organisation=str(query.get("organisation") or ""), user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Bid not found", "payload": {"screen": "not-found"}}
		if data["redirect"]:
			return {"verdict": "OK", "title": "Submission status", "redirect": data["redirect"]}
		return {"verdict": "OK", "title": "Submission status", "payload": {"screen": "status", "data": {"outcome": "OK", **data}}}
	if len(segments) == 4 and segments[0] == "tenders" and segments[2] == "bid" and segments[3] == "replace":
		# BDS-DES-14: Prepare replacement for the organisation's own submitted bid
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		from kentender_procurement.bid_submission.services import changes_view

		try:
			data = changes_view.get_replacement_page(tender_reference=segments[1], organisation=str(query.get("organisation") or ""), user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Bid not found", "payload": {"screen": "not-found"}}
		return {"verdict": "OK", "title": "Prepare replacement bid", "payload": {"screen": "replace", "data": {"outcome": "OK", **data}}}
	if len(segments) == 4 and segments[0] == "tenders" and segments[2] == "bid" and segments[3] == "submit":
		# BDS-DES-12: the final act for the organisation's own bid
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		try:
			data = reads.get_submit_page(tender_reference=segments[1], organisation=str(query.get("organisation") or ""), user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Bid not found", "payload": {"screen": "not-found"}}
		return {"verdict": "OK", "title": "Submit bid", "payload": {"screen": "submit", "data": {"outcome": "OK", **data}}}
	if len(segments) == 4 and segments[0] == "tenders" and segments[2] == "bid" and segments[3] in TASK_SCREENS:
		# BDS-DES-07/08: a task of the organisation's own bid
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		screen, title = TASK_SCREENS[segments[3]]
		try:
			data = reads.get_bid_task(tender_reference=segments[1], task=segments[3], organisation=str(query.get("organisation") or ""), user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Bid not found", "payload": {"screen": "not-found"}}
		return {"verdict": "OK", "title": title, "payload": {"screen": screen, "data": {"outcome": "OK", **data}}}
	if segments in (["my-bids"], ["account", "receipts"]):
		# BDS-DES-05 / BDS-DES-17: the signed-in organisation's own records
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		organisation = str(query.get("organisation") or "")
		if segments == ["my-bids"]:
			data = reads.get_my_bids(organisation=organisation, search=str(query.get("search") or ""), status=str(query.get("status") or ""), user=user)
			return {"verdict": "OK", "title": "My bids", "payload": {"screen": "my-bids", "data": data}}
		try:
			data = reads.get_receipt_history(organisation=organisation, user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Page not found", "payload": {"screen": "not-found"}}
		return {"verdict": "OK", "title": "Receipts", "payload": {"screen": "receipts", "data": data}}
	return {"verdict": "NOT_FOUND", "title": "Page not found", "payload": {"screen": "not-found"}}
