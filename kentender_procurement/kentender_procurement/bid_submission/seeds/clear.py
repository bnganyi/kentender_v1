# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Removing Bid Submission rows — the one place that knows this module's
tables. The Tenders clear removes Tenders with `force`, which skips link
checks, so the Bid Submission rows of a removed Tender are removed here
first, by the caller that owns the Tender world (tests, seeds)."""

from __future__ import annotations

import frappe

from kentender_core.utils.raw_delete import delete_rows

DOCTYPES = ("Bid Submission Event", "Bid Workspace", "Bid Organisation Snapshot", "Bidder Arrangement", "Bid Command Journal")


def on_tenders_removed(*, tenders: list[str]) -> dict[str, int]:
	"""`kt_tender_removal_consumers`: the Tenders clean-up is removing these."""
	return wipe(tenders=tenders)


def wipe(*, tenders: list[str] | None = None, namespace: str = "") -> dict[str, int]:
	"""Delete the Bid Submission rows of `tenders` and the command-journal
	entries stamped `namespace`; with `tenders=None`, every row."""
	deleted: dict[str, int] = {}
	if tenders is None:
		for doctype in DOCTYPES:
			delete_rows(doctype, None, deleted=deleted)
		return deleted
	if tenders:
		within = {"tender": ("in", list(tenders))}
		arrangements = frappe.get_all("Bidder Arrangement", filters=within, pluck="name")
		delete_rows("Bid Submission Event", within, deleted=deleted)
		delete_rows("Bid Workspace", within, deleted=deleted)
		if arrangements:
			delete_rows("Bid Organisation Snapshot", {"bidder_arrangement": ("in", arrangements)}, deleted=deleted)
		delete_rows("Bidder Arrangement", within, deleted=deleted)
	for tender in tenders or []:
		# the seeded Start bid's request key names its Tender (seeds.canonical)
		delete_rows("Bid Command Journal", {"idempotency_key": ("like", f"seed-start-bid-{tender}-%")}, deleted=deleted)
	if namespace:
		delete_rows("Bid Command Journal", {"fixture_namespace": namespace}, deleted=deleted)
	return deleted
