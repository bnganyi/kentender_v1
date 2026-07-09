# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Transactional STD package commit importer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frappe

from kentender_procurement.std_engine.package_import.commit_persister import (
	CommitStats,
	_persist_import_run,
	persist_package_commit,
)
from kentender_procurement.std_engine.package_import.dry_run_importer import DryRunImporter
from kentender_procurement.std_engine.package_import.hash_utils import (
	compute_file_sha256,
	compute_manifest_hash,
)
from kentender_procurement.std_engine.package_import.package_reader import PackageReader, PackageReaderError
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path


class CommitImporterError(Exception):
	pass


class CommitImporter:
	def __init__(
		self,
		zip_path: str | Path | None = None,
		pdf_path: str | Path | None = None,
	) -> None:
		self.zip_path = Path(zip_path or default_seed_zip_path())
		self.pdf_path = Path(pdf_path or default_official_pdf_path())

	def run(self) -> dict[str, Any]:
		if not self.pdf_path.is_file():
			raise CommitImporterError(f"Official source PDF not found: {self.pdf_path}")

		dry_report = DryRunImporter(self.zip_path, self.pdf_path).run()
		if dry_report["import_readiness"] == "BLOCKED":
			raise CommitImporterError(
				"Package import is blocked: " + "; ".join(dry_report.get("validation_blockers") or ["unknown blocker"])
			)

		package_id = dry_report["package_id"]
		package_sha256 = dry_report["package_sha256"]
		self._guard_active_version(package_id)

		if self._is_idempotent(package_id, package_sha256):
			return self._build_idempotent_report(dry_report)

		try:
			inspection = PackageReader(self.zip_path).inspect()
		except PackageReaderError as exc:
			raise CommitImporterError(str(exc)) from exc

		manifest_hash = compute_manifest_hash(inspection.manifest)
		source_document_hash = compute_file_sha256(self.pdf_path)

		try:
			stats = persist_package_commit(
				inspection=inspection,
				zip_path=self.zip_path,
				pdf_path=self.pdf_path,
				package_sha256=package_sha256,
				manifest_hash=manifest_hash,
				source_document_hash=source_document_hash,
				dry_report=dry_report,
			)
			frappe.db.commit()
		except Exception as exc:
			frappe.db.rollback()
			raise CommitImporterError(str(exc)) from exc

		report = dict(dry_report)
		report.update(
			{
				"commit_status": "COMMITTED",
				"import_run_key": stats.import_run_key,
				"records_committed": stats.records_committed,
				"run_mode": "COMMIT",
			}
		)
		return report

	def _guard_active_version(self, package_id: str) -> None:
		if not frappe.db.exists("STD Version", package_id):
			return
		lifecycle_state = frappe.db.get_value("STD Version", package_id, "lifecycle_state")
		if lifecycle_state == "ACTIVE":
			raise CommitImporterError(f"Cannot import over ACTIVE STD Version: {package_id}")

	def _is_idempotent(self, package_id: str, package_sha256: str) -> bool:
		if not frappe.db.exists("STD Version", package_id):
			return False
		existing_hash = frappe.db.get_value("STD Version", package_id, "package_sha256") or ""
		return existing_hash == package_sha256

	def _build_idempotent_report(self, dry_report: dict[str, Any]) -> dict[str, Any]:
		stats = CommitStats(records_committed={key: 0 for key in dry_report.get("record_counts", {})})
		import_run_key = _persist_import_run(
			dry_report["package_id"],
			dry_report=dry_report,
			stats=stats,
			commit_status="IDEMPOTENT_SKIP",
		)
		frappe.db.commit()
		report = dict(dry_report)
		report.update(
			{
				"commit_status": "IDEMPOTENT_SKIP",
				"import_run_key": import_run_key,
				"records_committed": stats.records_committed,
				"run_mode": "COMMIT",
			}
		)
		return report
