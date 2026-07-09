# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HTTP import scaffold — dry-run, commit, import-run retrieval."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.package_import.commit_importer import (
	CommitImporter,
	CommitImporterError,
)
from kentender_procurement.std_engine.package_import.dry_run_importer import DryRunImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path
from kentender_procurement.std_engine.services.import_run_service import (
	get_import_run_payload,
	persist_dry_run_report,
)

IMPORT_WRITE_ROLES = ("System Manager", "Administrator")
IMPORT_READ_ROLES = ("System Manager", "Administrator", "Auditor")


def _success(*, report: dict[str, Any], import_run_key: str, route: str) -> dict[str, Any]:
	return {
		"ok": True,
		"route": route,
		"import_run_key": import_run_key,
		"report": report,
	}


def _error(error_code: str, message: str, *, route: str) -> dict[str, Any]:
	return {
		"ok": False,
		"route": route,
		"error_code": error_code,
		"message": message,
	}


@frappe.whitelist(methods=["POST"])
def dry_run(zip_path: str | None = None, pdf_path: str | None = None) -> dict[str, Any]:
	"""POST /std-engine/import/dry-run — non-destructive package inspection."""
	route = "POST /std-engine/import/dry-run"
	frappe.only_for(IMPORT_WRITE_ROLES)
	try:
		report = DryRunImporter(
			zip_path=zip_path or str(default_seed_zip_path()),
			pdf_path=pdf_path or str(default_official_pdf_path()),
		).run()
	except Exception as exc:
		return _error("STD_IMPORT_DRY_RUN_FAILED", str(exc), route=route)

	import_run_key = persist_dry_run_report(report)
	frappe.db.commit()
	return _success(report=report, import_run_key=import_run_key, route=route)


@frappe.whitelist(methods=["POST"])
def commit(
	zip_path: str | None = None,
	pdf_path: str | None = None,
	package_id: str | None = None,
) -> dict[str, Any]:
	"""POST /std-engine/import/commit — transactional DRAFT import."""
	route = "POST /std-engine/import/commit"
	frappe.only_for(IMPORT_WRITE_ROLES)
	_ = package_id  # reserved for explicit package targeting in future replace-draft flows
	try:
		report = CommitImporter(
			zip_path=zip_path or str(default_seed_zip_path()),
			pdf_path=pdf_path or str(default_official_pdf_path()),
		).run()
	except CommitImporterError as exc:
		frappe.db.rollback()
		return _error("STD_IMPORT_COMMIT_FAILED", str(exc), route=route)
	except Exception as exc:
		frappe.db.rollback()
		return _error("STD_IMPORT_COMMIT_FAILED", str(exc), route=route)

	return _success(report=report, import_run_key=report.get("import_run_key") or "", route=route)


@frappe.whitelist(methods=["GET"])
def get_import_run(import_run_id: str) -> dict[str, Any]:
	"""GET /std-engine/import-runs/:id — retrieve a dry-run or commit report."""
	route = "GET /std-engine/import-runs/:id"
	frappe.only_for(IMPORT_READ_ROLES)
	key = (import_run_id or "").strip()
	if not key:
		return _error("STD_IMPORT_RUN_NOT_FOUND", "import_run_id is required", route=route)

	payload = get_import_run_payload(key)
	if not payload:
		return _error("STD_IMPORT_RUN_NOT_FOUND", f"Import run not found: {key}", route=route)

	return {
		"ok": True,
		"route": route,
		"import_run": payload,
	}
