# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bench execute entry point for STD validation engine."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.validation.validation_engine import ValidationEngine


@frappe.whitelist()
def run(package_id: str) -> dict[str, Any]:
	"""Re-run validation for an imported STD package."""
	frappe.only_for(("System Manager", "Administrator"))

	dry_report = None
	inspection = None
	version = frappe.db.get_value("STD Version", package_id, ["package_sha256"], as_dict=True)
	if version and version.get("package_sha256"):
		try:
			from kentender_procurement.std_engine.package_import.dry_run_importer import DryRunImporter
			from kentender_procurement.std_engine.package_import.package_reader import PackageReader
			from kentender_procurement.std_engine.package_import.hash_utils import compute_file_sha256
			from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path

			zip_path = default_seed_zip_path()
			if compute_file_sha256(zip_path) == version.package_sha256:
				dry_report = DryRunImporter(zip_path, default_official_pdf_path()).run()
				inspection = PackageReader(zip_path).inspect()
		except Exception:
			pass

	result = ValidationEngine().run_for_package(
		package_id,
		dry_report=dry_report,
		inspection=inspection,
		run_type="MANUAL_REVALIDATION",
	)
	frappe.db.commit()
	return {
		"package_id": result.package_id,
		"run_key": result.run_key,
		"status": result.status,
		"summary": result.summary,
		"finding_count": len(result.findings),
	}
