# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Submission endpoints (BDS-CHG-001 v0.8 §7). Thin: each forwards to
one service; authority and every rule live in the services."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_submission.services import reads


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_available_tenders(search: str = "", method: str = "", reservation: str = "", closing: str = "open") -> dict[str, Any]:
	"""BDS §7.1 `GetAvailableTenders` — public; no identity is needed."""
	return reads.get_available_tenders(search=search, method=method, reservation=reservation, closing=closing)
