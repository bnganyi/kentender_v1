# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0120 — summary counts for Official STD Library cards."""

from __future__ import annotations

from collections.abc import Iterable

import frappe
from frappe import _

from kentender_procurement.tender_management.services import std_template_governance as gov


def _count_by_lifecycle(statuses: Iterable[str]) -> int:
	seen: set[str] = set()
	for status in statuses:
		names = frappe.get_all(
			"STD Template",
			filters={"lifecycle_status": status},
			pluck="name",
			limit_page_length=0,
		)
		seen.update(names or [])
	return len(seen)


def _count_by_validation(statuses: Iterable[str]) -> int:
	seen: set[str] = set()
	for status in statuses:
		names = frappe.get_all(
			"STD Template",
			filters={"latest_validation_status": status},
			pluck="name",
			limit_page_length=0,
		)
		seen.update(names or [])
	return len(seen)


def _count_needs_attention() -> int:
	lifecycle_names = set()
	validation_names = set()

	for status in (gov.STATUS_IMPORTED, gov.STATUS_VALIDATION_FAILED, gov.STATUS_RETURNED):
		lifecycle_names.update(
			frappe.get_all(
				"STD Template",
				filters={"lifecycle_status": status},
				pluck="name",
				limit_page_length=0,
			)
			or []
		)

	for status in (gov.VALIDATION_PASS_WARNINGS, gov.VALIDATION_BLOCKED, gov.VALIDATION_FAILED):
		validation_names.update(
			frappe.get_all(
				"STD Template",
				filters={"latest_validation_status": status},
				pluck="name",
				limit_page_length=0,
			)
			or []
		)

	return len(lifecycle_names.union(validation_names))


@frappe.whitelist()
def get_std_library_summary_counts() -> dict:
	"""Return STD-LIB-0120 summary-card counts and library health panel metrics."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	total = frappe.db.count("STD Template")
	active_count = _count_by_lifecycle((gov.STATUS_ACTIVE,))
	needs_attention_count = _count_needs_attention()
	ready_for_review_count = _count_by_lifecycle(
		(gov.STATUS_VALIDATED, gov.STATUS_SUBMITTED, gov.STATUS_APPROVED)
	)
	pending_approval_count = _count_by_lifecycle((gov.STATUS_SUBMITTED,))
	superseded_count = _count_by_lifecycle((gov.STATUS_SUPERSEDED,))

	return {
		"total_count": total,
		"active_count": active_count,
		"needs_attention_count": needs_attention_count,
		"ready_for_review_count": ready_for_review_count,
		"pending_approval_count": pending_approval_count,
		"superseded_count": superseded_count,
		"package_import_count": _count_by_lifecycle((gov.STATUS_IMPORTED,)),
		"bundle_issue_count": _count_by_validation((gov.VALIDATION_BLOCKED, gov.VALIDATION_FAILED)),
		"health": {
			"unauthorized_active_setup_count": 0,
			"pending_approval_count": pending_approval_count,
			"due_for_review_count": ready_for_review_count,
			"retired_referenced_count": superseded_count,
		},
	}
