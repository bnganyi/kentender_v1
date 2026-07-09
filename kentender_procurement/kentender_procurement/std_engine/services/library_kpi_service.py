# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Aggregate KPI and health metrics for the STD Library screen."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import frappe

from kentender_procurement.std_engine.constants import FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION

REVIEW_LIFECYCLE_STATES = (
	"STRUCTURING",
	"INTERNAL_REVIEW",
	"LEGAL_REVIEW",
	"PROCUREMENT_REVIEW",
)
DUE_OVERDUE_LIFECYCLE_STATES = (
	"INTERNAL_REVIEW",
	"LEGAL_REVIEW",
	"PROCUREMENT_REVIEW",
)
PENDING_APPROVAL_STATES = ("PROCUREMENT_REVIEW", "APPROVED")


def count_distinct_real_tender_bindings(
	*,
	family_code: str | None = None,
	package_ids: list[str] | None = None,
) -> int:
	"""Count distinct tenders bound to STD packages — excludes smoke-test fixture rows."""
	conditions = [
		"IFNULL(tender_ref, '') != ''",
		"(fixture_source IS NULL OR fixture_source != %s)",
	]
	values: list[Any] = [FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION]
	if family_code:
		conditions.append("family_code = %s")
		values.append(family_code)
	if package_ids:
		placeholders = ", ".join(["%s"] * len(package_ids))
		conditions.append(f"package_id IN ({placeholders})")
		values.extend(package_ids)
	where_clause = " AND ".join(conditions)
	row = frappe.db.sql(
		f"SELECT COUNT(DISTINCT tender_ref) AS cnt FROM `tabSTD Usage Binding` WHERE {where_clause}",
		tuple(values),
		as_dict=True,
	)
	return int((row or [{}])[0].get("cnt") or 0)


def _distinct_blocked_package_ids() -> set[str]:
	rows = frappe.get_all(
		"STD Validation Finding",
		filters={"severity": "BLOCKER"},
		pluck="package_id",
		distinct=True,
	)
	return {row for row in (rows or []) if row}


def _count_blocked_drafts(blocked_packages: set[str]) -> int:
	if not blocked_packages:
		return 0
	return frappe.db.count(
		"STD Version",
		{
			"lifecycle_state": "DRAFT",
			"package_id": ("in", list(blocked_packages)),
		},
	)


def _count_due_overdue(blocked_packages: set[str]) -> int:
	if not blocked_packages:
		return 0
	return frappe.db.count(
		"STD Version",
		{
			"lifecycle_state": ("in", DUE_OVERDUE_LIFECYCLE_STATES),
			"package_id": ("in", list(blocked_packages)),
		},
	)


def _count_superseded_in_active_tenders() -> int:
	superseded_packages = frappe.get_all(
		"STD Version",
		filters={"lifecycle_state": "SUPERSEDED"},
		pluck="package_id",
	)
	if not superseded_packages:
		return 0
	return count_distinct_real_tender_bindings(package_ids=superseded_packages)


def build_library_kpi_summary() -> dict[str, Any]:
	"""Return library KPI cards and health panel counts from persisted STD Engine state."""
	blocked_packages = _distinct_blocked_package_ids()
	cutoff = datetime.now() - timedelta(days=30)

	return {
		"kpis": {
			"stdFamilies": frappe.db.count("STD Family"),
			"newFamilies": frappe.db.count("STD Family", {"creation": (">=", cutoff)}),
			"activeVersions": frappe.db.count("STD Version", {"lifecycle_state": "ACTIVE"}),
			"inReview": frappe.db.count(
				"STD Version",
				{"lifecycle_state": ("in", REVIEW_LIFECYCLE_STATES)},
			),
			"dueOverdue": _count_due_overdue(blocked_packages),
			"blockers": len(blocked_packages),
		},
		"health": {
			"unauthorizedActiveVersions": frappe.db.count(
				"STD Version",
				{"lifecycle_state": "ACTIVE", "activation_allowed": 0},
			),
			"pendingApprovals": frappe.db.count(
				"STD Version",
				{"lifecycle_state": ("in", PENDING_APPROVAL_STATES)},
			),
			"dueForReview30d": frappe.db.count(
				"STD Version",
				{"lifecycle_state": ("in", REVIEW_LIFECYCLE_STATES)},
			),
			"supersededInActiveTenders": _count_superseded_in_active_tenders(),
			"blockedDrafts": _count_blocked_drafts(blocked_packages),
		},
	}
