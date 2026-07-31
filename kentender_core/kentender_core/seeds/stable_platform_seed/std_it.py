# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Import KE-PPRA-IT-2022-04 v1_1 verbatim seed package into STD Engine."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.stable_platform_seed.constants import IT_STD_FAMILY_CODE, IT_STD_VERSION_CODE
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1


def import_it_std_v1_1(*, replace_draft: bool = True) -> dict[str, Any]:
	"""Commit the v1_1 IT STD seed package as DRAFT.

	Idempotent when ``KE-PPRA-IT-2022-04`` is already ACTIVE (do not re-import).
	"""
	frappe.only_for(("System Manager", "Administrator"))
	if frappe.db.exists("STD Version", IT_STD_VERSION_CODE):
		lifecycle = (
			frappe.db.get_value("STD Version", IT_STD_VERSION_CODE, "lifecycle_state") or ""
		).strip().upper()
		if lifecycle == "ACTIVE":
			return {
				"ok": True,
				"package_id": IT_STD_VERSION_CODE,
				"family_code": IT_STD_FAMILY_CODE,
				"lifecycle_state": "ACTIVE",
				"idempotent": True,
				"skipped_import": True,
			}
	importer = CommitImporter(
		zip_path=str(default_seed_zip_path_v1_1()),
		pdf_path=str(default_official_pdf_path()),
		replace_draft=replace_draft,
	)
	try:
		result = importer.run()
	except Exception as exc:
		msg = str(exc)
		# Race / already-ACTIVE: treat as success for seed orchestrators.
		if "ACTIVE" in msg.upper() and IT_STD_VERSION_CODE in msg:
			return {
				"ok": True,
				"package_id": IT_STD_VERSION_CODE,
				"family_code": IT_STD_FAMILY_CODE,
				"lifecycle_state": "ACTIVE",
				"idempotent": True,
				"skipped_import": True,
				"message": msg,
			}
		return {
			"ok": False,
			"error_code": "STD_IMPORT_FAILED",
			"message": msg,
		}
	return {
		"ok": True,
		"package_id": IT_STD_VERSION_CODE,
		"family_code": IT_STD_FAMILY_CODE,
		"lifecycle_state": result.get("lifecycle_state") or "DRAFT",
		"import_run": result.get("import_run"),
		"stats": result.get("stats"),
		"idempotent": bool(result.get("idempotent")),
	}
