# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Package integrity findings from dry-run/import inspection."""

from __future__ import annotations

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class PackageIntegrityValidator:
	validator_code = "package_integrity"

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		inspection = context.inspection
		dry_report = context.dry_report or {}
		findings: list[ValidationFindingSpec] = []

		if inspection:
			for index, error in enumerate(inspection.manifest_errors or [], start=1):
				findings.append(
					ValidationFindingSpec(
						finding_code=f"MANIFEST_ERROR_{index:03d}",
						severity="BLOCKER",
						object_type="STD Version",
						object_id=context.package_id,
						description=error,
						lifecycle_gate="IMPORT",
					)
				)
			if inspection.missing_required_files:
				findings.append(
					ValidationFindingSpec(
						finding_code="MISSING_REQUIRED_FILES",
						severity="BLOCKER",
						object_type="STD Version",
						object_id=context.package_id,
						description="Missing required package files: "
						+ ", ".join(inspection.missing_required_files),
						lifecycle_gate="IMPORT",
					)
				)
			if inspection.checksum_status == "FAILED":
				findings.append(
					ValidationFindingSpec(
						finding_code="CHECKSUM_FAILED",
						severity="BLOCKER",
						object_type="STD Version",
						object_id=context.package_id,
						description="Package checksum verification failed",
						lifecycle_gate="IMPORT",
					)
				)

		for index, warning in enumerate(dry_report.get("validation_warnings") or [], start=1):
			findings.append(
				ValidationFindingSpec(
					finding_code=f"IMPORT_WARNING_{index:03d}",
					severity="WARNING",
					object_type="STD Version",
					object_id=context.package_id,
					description=warning,
					lifecycle_gate="IMPORT",
				)
			)
		return findings
