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


# -- submission references (BDS-CHG-001 v0.8 §10.1, §13.4) ------------------


def _year_sequence(tender_reference: str) -> str:
	"""`TND-MOH-2027-033` → `2027-033` (the correlation and support pattern)."""
	parts = cstr(tender_reference).strip().split("-")
	return "-".join(parts[-2:]) if len(parts) >= 2 else cstr(tender_reference)


def lock_tender(tender_name: str) -> None:
	frappe.db.sql("select name from `tabTender` where name=%s for update", tender_name)


def correlation_id(tender_name: str, tender_reference: str) -> str:
	"""`COR-BDS-2027-033-01`: one per submission attempt, in attempt order."""
	lock_tender(tender_name)
	return f"COR-BDS-{_year_sequence(tender_reference)}-{frappe.db.count('Bid Submission Attempt', {'tender': tender_name}) + 1:02d}"


def support_reference(tender_name: str, tender_reference: str) -> str:
	"""`SUP-BDS-2027-033-01`: the reference a supplier quotes to support for a pending attempt."""
	lock_tender(tender_name)
	used = frappe.db.count("Bid Submission Attempt", {"tender": tender_name, "support_reference": ("is", "set")})
	return f"SUP-BDS-{_year_sequence(tender_reference)}-{used + 1:02d}"


def receipt_reference(tender_name: str, tender_reference: str) -> str:
	"""`RCPT-MOH-2027-033-001`: receipts of a Tender in acceptance order."""
	lock_tender(tender_name)
	return f"RCPT-{_suffix(tender_reference)}-{frappe.db.count('Bid Receipt', {'tender': tender_name}) + 1:03d}"


def submission_version_id(bid_reference: str, number: int) -> str:
	return f"SUBV-{cstr(bid_reference).removeprefix('BID-')}-{number:02d}"
