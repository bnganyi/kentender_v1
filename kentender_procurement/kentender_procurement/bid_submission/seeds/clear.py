# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Removing Bid Submission rows — the one place that knows this module's
tables. The Tenders clear removes Tenders with `force`, which skips link
checks, so the Bid Submission rows of a removed Tender are removed here
first, by the caller that owns the Tender world (tests, seeds)."""

from __future__ import annotations

import frappe

from kentender_core.utils.raw_delete import delete_rows

SUBMISSION = ("Bid Hand-off", "Bid Opening Handoff", "Bid Submission Close", "Bid Submission Change", "Bid Submission Version", "Bid Receipt", "Tender Box Envelope", "Bid Submission Attempt")
SIMULATION = ("Test Trust Signature", "Test Trust Certificate", "Bid Submission Incident")
DOCTYPES = SUBMISSION + ("Tender Security Intake Match", "Tender Security Intake", "Bid Submission Event", "Bid Draft Change", "Bid Section Response", "Bid Evidence", "Bid Workspace", "Bid Organisation Snapshot", "Bidder Arrangement", "Bid Command Journal")


def _delete_evidence_files(evidence: list[str], deleted: dict[str, int]) -> None:
	"""A bid file is a private File attached to its Bid Evidence row."""
	for name in evidence:
		for file_name in frappe.get_all("File", filters={"attached_to_doctype": "Bid Evidence", "attached_to_name": name}, pluck="name"):
			frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)
			deleted["File"] = deleted.get("File", 0) + 1


def _delete_box_files(tenders: list[str] | None, deleted: dict[str, int]) -> None:
	"""The Test Tender Box keeps package files outside the database, by correlation."""
	from kentender_procurement.bid_submission.test_services import tender_box

	filters = {"tender": ("in", list(tenders))} if tenders is not None else {}
	correlations = frappe.get_all("Bid Submission Attempt", filters=filters, pluck="correlation_id")
	closed = list(tenders) if tenders is not None else frappe.get_all("Bid Submission Close", pluck="tender")
	removed = tender_box.remove(correlations, tenders=closed)
	if removed:
		deleted["Test Tender Box file"] = deleted.get("Test Tender Box file", 0) + removed


def on_tenders_removed(*, tenders: list[str]) -> dict[str, int]:
	"""`kt_tender_removal_consumers`: the Tenders clean-up is removing these."""
	return wipe(tenders=tenders)


def wipe(*, tenders: list[str] | None = None, namespace: str = "") -> dict[str, int]:
	"""Delete the Bid Submission rows of `tenders` and the command-journal
	entries stamped `namespace`; with `tenders=None`, every row."""
	deleted: dict[str, int] = {}
	if tenders is None:
		_delete_box_files(None, deleted)
		_delete_evidence_files(frappe.get_all("Bid Evidence", pluck="name"), deleted)
		for doctype in DOCTYPES + SIMULATION:
			delete_rows(doctype, None, deleted=deleted)
		return deleted
	if tenders:
		within = {"tender": ("in", list(tenders))}
		_delete_box_files(tenders, deleted)
		for doctype in SUBMISSION:
			delete_rows(doctype, within, deleted=deleted)
		arrangements = frappe.get_all("Bidder Arrangement", filters=within, pluck="name")
		workspaces = frappe.get_all("Bid Workspace", filters=within, pluck="name")
		delete_rows("Tender Security Intake Match", within, deleted=deleted)
		delete_rows("Tender Security Intake", within, deleted=deleted)
		delete_rows("Bid Submission Event", within, deleted=deleted)
		if workspaces:
			of_bids = {"bid_workspace": ("in", workspaces)}
			_delete_evidence_files(frappe.get_all("Bid Evidence", filters=of_bids, pluck="name"), deleted)
			for doctype in ("Bid Draft Change", "Bid Section Response", "Bid Evidence"):
				delete_rows(doctype, of_bids, deleted=deleted)
		delete_rows("Bid Workspace", within, deleted=deleted)
		if arrangements:
			delete_rows("Bid Organisation Snapshot", {"bidder_arrangement": ("in", arrangements)}, deleted=deleted)
		delete_rows("Bidder Arrangement", within, deleted=deleted)
	for tender in tenders or []:
		# the seeded Start bid's request key names its Tender (seeds.canonical)
		delete_rows("Bid Command Journal", {"idempotency_key": ("like", f"seed-start-bid-{tender}-%")}, deleted=deleted)
	if namespace:
		delete_rows("Bid Command Journal", {"fixture_namespace": namespace}, deleted=deleted)
		for doctype in SIMULATION:
			delete_rows(doctype, {"fixture_namespace": namespace}, deleted=deleted)
	return deleted
