# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Removing Bid Evaluation records (EVL-CHG-001 v0.4 plan D17, D18): test
worlds, fixture resets and a removed Tender. Only the given Tenders' cases,
their Proceedings and support issues, or rows stamped with the given fixture
namespace, are touched; nothing site-wide."""

from __future__ import annotations

import frappe

CASE = "Evaluation Case"
BY_CASE = (
	"Evaluation Appointment", "Evaluation Secretary Appointment", "Evaluation Declaration", "Evaluation Member Unavailability", "Evaluation Source Intake",
	"Evaluation Bid", "Evaluation Check Run", "Evaluation Check Result", "Evaluation Finding", "Evaluation Discussion Item", "Evaluation Conclusion",
	"Evaluation Disagreement", "Evaluation Clarification", "Evaluation Clarification Reply", "Evaluation Verification Plan", "Evaluation Verification Observation",
	"Evaluation Report Version", "Evaluation Report Delivery", "Evaluation Source Event", "Evaluation Correction Notice",
)
PRC_CHILDREN = ("Proceeding Attendance", "Proceeding Event", "Proceeding Attestation", "Proceeding Supplement", "Proceeding Session")


def wipe(*, tenders=None, namespace: str = "") -> int:
	from kentender_core.utils.raw_delete import delete_rows

	filters = []
	if tenders:
		filters.append({"tender": ("in", list(tenders))})
	if namespace:
		filters.append({"fixture_namespace": namespace})
	cases: set[str] = set()
	for f in filters:
		cases |= set(frappe.get_all(CASE, filters=f, pluck="name"))
	if cases:
		names = list(cases)
		for doctype in BY_CASE:
			if doctype == "Evaluation Appointment":
				parents = frappe.get_all(doctype, filters={"evaluation_case": ("in", names)}, pluck="name")
				if parents:
					frappe.db.delete("Evaluation Committee Member", {"parent": ("in", parents)})
			frappe.db.delete(doctype, {"evaluation_case": ("in", names)})
		proceedings = frappe.get_all("Proceeding", filters={"owner_type": "Evaluation Case", "owner_id": ("in", names)}, pluck="name")
		if proceedings:
			for doctype in PRC_CHILDREN:
				frappe.db.delete(doctype, {"proceeding": ("in", proceedings)})
			frappe.db.delete("Proceeding Member", {"parent": ("in", proceedings)})
			versions = frappe.get_all("Proceeding Minutes Version", filters={"proceeding": ("in", proceedings)}, pluck="name")
			if versions:
				frappe.db.delete("Proceeding Minutes Target", {"parent": ("in", versions)})
			delete_rows("Proceeding Minutes Version", {"proceeding": ("in", proceedings)})
			frappe.db.delete("Proceeding Command Journal", {"proceeding": ("in", proceedings)})
			delete_rows("Proceeding", {"name": ("in", proceedings)})
		frappe.db.delete("Evaluation Command Journal", {"evaluation_case": ("in", names)})
		frappe.db.delete("Support Issue", {"module": "Bid Evaluation", "reference_name": ("in", names)})
		frappe.db.delete("Notification Log", {"document_type": CASE, "document_name": ("in", names)})
		delete_rows(CASE, {"name": ("in", names)})
	if namespace:
		for doctype in (*BY_CASE, "Evaluation Command Journal", "Support Issue"):
			frappe.db.delete(doctype, {"fixture_namespace": namespace})
	return len(cases)


def on_tenders_removed(tenders: list[str]) -> None:
	"""`kt_tender_removal_consumers`: an evaluation goes with its Tender."""
	wipe(tenders=tenders)
