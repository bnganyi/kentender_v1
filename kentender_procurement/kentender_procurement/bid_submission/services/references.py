# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Server-minted Bid Submission references (BDS-CHG-001 v0.8 §4.3, §4.5 and
§10.1: `ARR-MOH-2027-033-001`, `BID-MOH-2027-033-001`). A Tender's bids are
numbered in start order under a lock on the Tender row, so two concurrent
Start bid commands never mint the same number. The per-Tender sequence reveals
a count; that residual is recorded for the production gate (FU-V08-16)."""

from __future__ import annotations

import frappe
from frappe.utils import cstr


def _suffix(tender_reference: str) -> str:
	reference = cstr(tender_reference).strip()
	return reference[4:] if reference.startswith("TND-") else reference


def next_number(tender_name: str) -> int:
	frappe.db.sql("select name from `tabTender` where name=%s for update", tender_name)
	return frappe.db.count("Bidder Arrangement", {"tender": tender_name}) + 1


def arrangement_id(tender_reference: str, number: int) -> str:
	return f"ARR-{_suffix(tender_reference)}-{number:03d}"


def bid_reference(tender_reference: str, number: int) -> str:
	return f"BID-{_suffix(tender_reference)}-{number:03d}"
