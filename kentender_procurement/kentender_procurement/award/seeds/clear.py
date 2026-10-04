# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Removing Award records (AWD-CHG-001 v0.4 plan D1): test worlds, fixture
resets and an Award whose Evaluation or Tender was removed. Only the given
tenders' cases, or rows stamped with the given fixture namespace, are
touched; nothing site-wide. Direct deletes: no queued jobs (AGENTS.md §8.1)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import records


def wipe(*, tenders=None, namespace: str = "") -> int:
	cases: set[str] = set()
	if tenders:
		cases |= set(frappe.get_all(records.CASE, filters={"tender": ("in", list(tenders))}, pluck="name"))
	if namespace:
		cases |= set(frappe.get_all(records.CASE, filters={"fixture_namespace": namespace}, pluck="name"))
	if cases:
		names = list(cases)
		for doctype in records.DOCTYPES:
			if doctype == records.CASE:
				continue
			field = "award_case"
			if frappe.get_meta(doctype).has_field(field):
				frappe.db.delete(doctype, {field: ("in", names)})
		issues = frappe.get_all("Support Issue", filters={"module": "Award", "reference_name": ("in", names)}, pluck="issue_id")
		if issues:
			frappe.db.delete("Notification Log", {"document_type": "Support Issue", "document_name": ("in", issues)})
		frappe.db.delete("Support Issue", {"module": "Award", "reference_name": ("in", names)})
		frappe.db.delete("Notification Log", {"document_type": records.CASE, "document_name": ("in", names)})
		frappe.db.delete(records.CASE, {"name": ("in", names)})
	if namespace:
		records.wipe(namespace)
		frappe.db.delete("Support Issue", {"module": "Award", "fixture_namespace": namespace})
	return len(cases)


def on_evaluations_removed(*, tenders=None, namespace: str = "") -> None:
	"""`kt_evaluation_removal_consumers`: an award goes with its evaluation."""
	wipe(tenders=tenders or [], namespace=namespace)


def on_tenders_removed(tenders: list[str]) -> None:
	"""`kt_tender_removal_consumers`: an award goes with its Tender."""
	wipe(tenders=tenders)
