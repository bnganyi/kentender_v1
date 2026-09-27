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
	if len(segments) == 3 and segments[0] == "tenders" and segments[2] == "bid":
		# BDS-DES-06: the signed-in organisation's own bid for this Tender
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		try:
			data = reads.get_bid_workspace(tender_reference=segments[1], organisation=str(query.get("organisation") or ""), user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Bid not found", "payload": {"screen": "not-found"}}
		return {"verdict": "OK", "title": "Your bid", "payload": {"screen": "workspace", "data": {"outcome": "OK", **data}}}
	if len(segments) == 4 and segments[0] == "tenders" and segments[2] == "bid" and segments[3] == "documents":
		# BDS-DES-07: the documents task of the organisation's own bid
		if not user or user == "Guest":
			return {"verdict": "SIGN_IN", "title": "Sign in"}
		try:
			data = reads.get_bid_task(tender_reference=segments[1], task="documents", organisation=str(query.get("organisation") or ""), user=user)
		except frappe.DoesNotExistError:
			return {"verdict": "NOT_FOUND", "title": "Bid not found", "payload": {"screen": "not-found"}}
		return {"verdict": "OK", "title": "Tender documents, clarifications and addenda", "payload": {"screen": "documents-task", "data": {"outcome": "OK", **data}}}
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
