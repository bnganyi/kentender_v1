# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening's answer for /tenders/{ref}/opening inside Bid Submission's
public portal (BOP-CHG-001 v0.10 §10.5; plan D10). Bid Submission owns the
/tenders prefix and asks this resolver through `kt_tender_opening_portal`;
the page's Vue screen is Bid Opening's `portal/PublicOpeningScreen.vue`."""

from __future__ import annotations

from typing import Any

import frappe


def resolve(*, tender_reference: str, user: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import public

	try:
		data = public.get_public_opening(tender_reference=tender_reference, user=user)
	except frappe.DoesNotExistError:
		return {"verdict": "NOT_FOUND", "title": "Tender not found", "payload": {"screen": "tender-not-found"}}
	return {"verdict": "OK", "title": f"Bid opening · {data['tender']['title']}", "payload": {"screen": "public-opening", "data": data}}
