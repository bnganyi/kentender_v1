# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Removing Bid Opening rows (the always-remove-test-data rule): an opening
case and everything under it (its committee, arrangements, presence,
register, exceptions, incidents, decisions, register requests, Evaluation
handoff, renders, audit rows and notifications) and its Proceeding. Used by
the Python test world, the browser worlds and the Tenders clean-up
(`kt_tender_removal_consumers`)."""

from __future__ import annotations

import frappe

OPENING_DOCTYPES = ("Opening Arrangement", "Opening Presence", "Opening Custody Participation", "Opening Entry", "Opening Register", "Opening Exception",
	"Opening Access Incident", "Opening Decision Item", "Opening Register Request", "Evaluation Handoff")


def on_tenders_removed(*, tenders: list[str]) -> dict[str, int]:
	"""`kt_tender_removal_consumers`: the Tenders clean-up is removing these."""
	return wipe(tenders=tenders)


def wipe(*, tenders: list[str] | set[str] | None = None, namespace: str = "") -> dict[str, int]:
	"""Delete the openings of `tenders` and those stamped `namespace`, with
	their Proceedings, and the command-journal entries stamped `namespace`."""
	from kentender_core.utils.raw_delete import delete_rows

	from kentender_procurement.bid_opening.services import renders

	tenders = set(tenders or ())
	cases = [r.name for r in frappe.get_all("Bid Opening Case", fields=["name", "tender", "fixture_namespace"])
		if (namespace and r.fixture_namespace == namespace) or r.tender in tenders]
	proceedings = [p for p in frappe.get_all("Bid Opening Case", filters={"name": ("in", cases)}, pluck="proceeding") if p] if cases else []
	if namespace:
		proceedings += [p for p in frappe.get_all("Proceeding", filters={"fixture_namespace": namespace}, pluck="name") if p not in proceedings]
	if cases:
		references = frappe.get_all("Bid Opening Case", filters={"name": ("in", cases)}, pluck="tender_reference")
		frappe.db.delete("Audit Event", {"entity": "Bid Opening", "document_type": "Tender", "document_name": ("in", references)})
		renders.remove(frappe.get_all("Opening Entry", filters={"opening_case": ("in", cases)}, pluck="entry_id"))
		renders.remove(frappe.get_all("Proceeding Minutes Version", filters={"proceeding": ("in", proceedings)}, pluck="minutes_version_id") if proceedings else [])
		requests = frappe.get_all("Opening Register Request", filters={"opening_case": ("in", cases)}, pluck="name")
		if requests:
			frappe.db.delete("Audit Event", {"document_type": "Opening Register Request", "document_name": ("in", requests)})
		for doctype in OPENING_DOCTYPES:
			frappe.db.delete(doctype, {"opening_case": ("in", cases)})
		delete_rows("Opening Committee Appointment", {"opening_case": ("in", cases)})
		frappe.db.delete("Notification Log", {"document_name": ("in", cases)})
		delete_rows("Bid Opening Case", {"name": ("in", cases)})
	if proceedings:
		for doctype in ("Proceeding Attendance", "Proceeding Event", "Proceeding Attestation", "Proceeding Supplement"):
			frappe.db.delete(doctype, {"proceeding": ("in", proceedings)})
		delete_rows("Proceeding Minutes Version", {"proceeding": ("in", proceedings)})
		delete_rows("Proceeding", {"name": ("in", proceedings)})
	if namespace:
		frappe.db.delete("Opening Command Journal", {"fixture_namespace": namespace})
		frappe.db.delete("Proceeding Command Journal", {"fixture_namespace": namespace})
	return {"cases": len(cases), "proceedings": len(proceedings)}
