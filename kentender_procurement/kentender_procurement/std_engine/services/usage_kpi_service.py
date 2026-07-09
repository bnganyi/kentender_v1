# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Aggregate KPI metrics for the Usage and Tender Bindings screen."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.constants import FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION
from kentender_procurement.std_engine.services.library_kpi_service import (
	count_distinct_real_tender_bindings,
)

_STABILITY_BADGE_BY_STATE = {
	"ACTIVE": "Stable",
	"APPROVED": "Approved",
	"DRAFT": "Draft",
	"STRUCTURING": "Draft",
	"INTERNAL_REVIEW": "In Review",
	"LEGAL_REVIEW": "In Review",
	"PROCUREMENT_REVIEW": "In Review",
	"SUPERSEDED": "Superseded",
	"ARCHIVED": "Archived",
}

_OPEN_ADDENDUM_STATUSES = ("ADDENDUM", "ADDENDUM_PENDING", "PENDING_ADDENDUM")


def _count_open_addenda(*, family_code: str, package_id: str) -> int:
	rows = frappe.get_all(
		"STD Usage Binding",
		filters={
			"family_code": family_code,
			"package_id": package_id,
			"binding_status": ("in", list(_OPEN_ADDENDUM_STATUSES)),
		},
		fields=["tender_ref", "fixture_source"],
	)
	real_rows = [
		row
		for row in rows
		if (row.tender_ref or "").strip()
		and (row.fixture_source or "") != FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION
	]
	return len({row.tender_ref for row in real_rows})


def build_usage_kpi_summary(version: Any) -> dict[str, Any]:
	"""Return usage bindings KPI cards from persisted real tender binding state."""
	family_code = str(getattr(version, "family_code", "") or "").strip()
	package_id = str(getattr(version, "package_id", "") or "").strip()
	lifecycle_state = str(getattr(version, "lifecycle_state", "") or "DRAFT")

	total_all_versions = count_distinct_real_tender_bindings(family_code=family_code)
	active_this_version = (
		count_distinct_real_tender_bindings(package_ids=[package_id]) if package_id else 0
	)
	historical_records = max(total_all_versions - active_this_version, 0)
	open_addenda = _count_open_addenda(family_code=family_code, package_id=package_id) if package_id else 0

	return {
		"totalTendersBoundAllVersions": total_all_versions,
		"trendPercent": None,
		"activeTendersThisVersion": active_this_version,
		"activeStabilityBadge": _STABILITY_BADGE_BY_STATE.get(lifecycle_state, lifecycle_state),
		"historicalRecords": historical_records,
		"openAddenda": open_addenda,
		"openAddendaActionRequired": open_addenda > 0,
	}
