# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Aggregate KPI and usage metrics for the STD Family Detail screen."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.services.library_kpi_service import (
	REVIEW_LIFECYCLE_STATES,
	count_distinct_real_tender_bindings,
)

_ACTIVE_BADGE_BY_STATE = {
	"ACTIVE": "STABLE",
	"APPROVED": "APPROVED",
	"DRAFT": "DRAFT",
	"STRUCTURING": "DRAFT",
	"INTERNAL_REVIEW": "IN REVIEW",
	"LEGAL_REVIEW": "IN REVIEW",
	"PROCUREMENT_REVIEW": "IN REVIEW",
	"SUPERSEDED": "SUPERSEDED",
	"ARCHIVED": "ARCHIVED",
}


def _release_cycle_count(versions: list[Any]) -> int:
	cycles: set[str] = set()
	for row in versions:
		code = getattr(row, "version_code", None) or (row.get("versionCode") if isinstance(row, dict) else "") or ""
		parts = str(code).split("-")
		if len(parts) >= 2:
			cycles.add(parts[-2])
		elif code:
			cycles.add(code)
	return len(cycles)


def _resolve_active_version(versions: list[Any]) -> Any | None:
	for row in versions:
		state = getattr(row, "lifecycle_state", None) or (
			row.get("lifecycleState") if isinstance(row, dict) else ""
		)
		if state == "ACTIVE":
			return row
	return versions[0] if versions else None


def _version_label(version: Any | None) -> str:
	if not version:
		return "—"
	label = getattr(version, "version_label", None) or (
		version.get("versionLabel") if isinstance(version, dict) else ""
	)
	code = getattr(version, "version_code", None) or (
		version.get("versionCode") if isinstance(version, dict) else ""
	)
	package_id = getattr(version, "package_id", None) or (
		version.get("packageId") if isinstance(version, dict) else ""
	)
	return str(label or code or package_id or "—")


def _version_state(version: Any | None) -> str:
	if not version:
		return "DRAFT"
	return str(
		getattr(version, "lifecycle_state", None)
		or (version.get("lifecycleState") if isinstance(version, dict) else "")
		or "DRAFT"
	)


def build_family_kpi_summary(family_code: str, versions: list[Any]) -> dict[str, Any]:
	"""Return family KPI cards and usage insight metrics from persisted STD Engine state."""
	code = (family_code or "").strip()
	active_version = _resolve_active_version(versions)
	active_state = _version_state(active_version)
	package_ids = [
		getattr(row, "package_id", None) or (row.get("packageId") if isinstance(row, dict) else "")
		for row in versions
	]
	package_ids = [package_id for package_id in package_ids if package_id]

	tenders_using_family = count_distinct_real_tender_bindings(family_code=code)
	active_tenders = (
		count_distinct_real_tender_bindings(package_ids=package_ids) if package_ids else 0
	)

	pending_review = frappe.db.count(
		"STD Version",
		{
			"family_code": code,
			"lifecycle_state": ("in", REVIEW_LIFECYCLE_STATES),
		},
	)
	total_versions = len(versions)
	binding_rate_percent = round((active_tenders / tenders_using_family) * 100, 1) if tenders_using_family else 0.0

	return {
		"kpis": {
			"activeVersionLabel": _version_label(active_version),
			"activeVersionBadge": _ACTIVE_BADGE_BY_STATE.get(active_state, active_state),
			"totalVersions": total_versions,
			"releaseCycles": _release_cycle_count(versions),
			"tendersUsingFamily": tenders_using_family,
			"trendPercent": None,
			"pendingReview": pending_review,
		},
		"usage": {
			"activeTenders": active_tenders,
			"bindingRatePercent": binding_rate_percent,
			"avgCycleDays": None,
		},
	}
