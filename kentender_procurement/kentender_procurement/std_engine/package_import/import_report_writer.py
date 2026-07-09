# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic dry-run report builder for STD package import."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kentender_procurement.std_engine.constants import COMMIT_TARGET_STATE_M1
from kentender_procurement.std_engine.package_import.import_planner import InsertPlan
from kentender_procurement.std_engine.package_import.package_reader import PackageInspectionResult


def build_dry_run_id(package_id: str, package_sha256: str) -> str:
	suffix = (package_sha256 or "")[:8].upper()
	return f"DRY-{package_id}-{suffix}"


def build_dry_run_report(
	*,
	inspection: PackageInspectionResult,
	plan: InsertPlan,
	package_sha256: str,
	manifest_hash: str,
	source_document_hash: str,
) -> dict[str, Any]:
	validation_blockers = list(plan.validation_blockers)
	validation_warnings = list(plan.validation_warnings)

	if inspection.manifest_errors:
		validation_blockers.extend(inspection.manifest_errors)
	if inspection.missing_required_files:
		validation_blockers.append(
			"Missing required package files: " + ", ".join(inspection.missing_required_files)
		)
	if inspection.checksum_status == "FAILED":
		validation_blockers.append("Package checksum verification failed")
	for blocker in inspection.activation_blockers:
		if blocker not in validation_blockers:
			validation_blockers.append(blocker)

	import_readiness = _resolve_import_readiness(
		inspection=inspection,
		plan=plan,
		validation_blockers=validation_blockers,
	)

	return {
		"package_id": inspection.package_id,
		"family_code": inspection.family_code,
		"version_code": inspection.version_code,
		"package_sha256": package_sha256,
		"manifest_hash": manifest_hash,
		"source_document_hash": source_document_hash,
		"record_counts": plan.record_counts,
		"missing_required_files": inspection.missing_required_files,
		"validation_blockers": validation_blockers,
		"validation_warnings": validation_warnings,
		"import_readiness": import_readiness,
		"checksum_status": inspection.checksum_status,
		"target_state": COMMIT_TARGET_STATE_M1,
		"dry_run_id": build_dry_run_id(inspection.package_id, package_sha256),
		"dry_run_timestamp": datetime.now(timezone.utc).isoformat(),
		"records_planned_insert": plan.records_planned_insert,
		"records_planned_skip": plan.records_planned_skip,
		"records_planned_fail": plan.records_planned_fail,
		"entity_actions": plan.entity_actions,
		"activation_allowed": inspection.activation_allowed,
		"skipped_paths": inspection.skipped_paths,
	}


def _resolve_import_readiness(
	*,
	inspection: PackageInspectionResult,
	plan: InsertPlan,
	validation_blockers: list[str],
) -> str:
	if inspection.missing_required_files:
		return "BLOCKED"
	if inspection.checksum_status == "FAILED":
		return "BLOCKED"
	if inspection.manifest_errors:
		return "BLOCKED"
	if plan.records_planned_fail > 0:
		return "BLOCKED"
	if validation_blockers and not inspection.activation_blockers:
		return "BLOCKED"
	if inspection.activation_blockers or plan.validation_warnings or inspection.missing_optional_files:
		return "READY_WITH_WARNINGS"
	return "READY"
