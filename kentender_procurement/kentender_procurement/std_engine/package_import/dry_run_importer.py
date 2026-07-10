# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Non-destructive STD package dry-run importer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kentender_procurement.std_engine.package_import.hash_utils import (
	compute_file_sha256,
	compute_manifest_hash,
)
from kentender_procurement.std_engine.package_import.import_planner import (
	build_insert_plan,
	load_optional_payloads,
)
from kentender_procurement.std_engine.package_import.import_report_writer import build_dry_run_report
from kentender_procurement.std_engine.package_import.package_reader import (
	PackageInspectionResult,
	PackageReader,
	PackageReaderError,
)
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path


class DryRunImporterError(Exception):
	pass


class DryRunImporter:
	def __init__(
		self,
		zip_path: str | Path | None = None,
		pdf_path: str | Path | None = None,
		*,
		replace_draft: bool = True,
	) -> None:
		self.zip_path = Path(zip_path or default_seed_zip_path())
		self.pdf_path = Path(pdf_path or default_official_pdf_path())
		self.replace_draft = replace_draft

	def run(self) -> dict[str, Any]:
		self._validate_pdf_path()
		inspection = self._inspect()
		package_sha256 = compute_file_sha256(self.zip_path)
		manifest_hash = compute_manifest_hash(inspection.manifest)
		source_document_hash = compute_file_sha256(self.pdf_path)
		optional_payloads = load_optional_payloads(
			self.zip_path,
			inspection.package_root,
			inspection.files_listed,
		)
		plan = build_insert_plan(
			inspection,
			package_sha256=package_sha256,
			optional_payloads=optional_payloads,
			replace_draft=self.replace_draft,
		)
		return build_dry_run_report(
			inspection=inspection,
			plan=plan,
			package_sha256=package_sha256,
			manifest_hash=manifest_hash,
			source_document_hash=source_document_hash,
		)

	def _inspect(self) -> PackageInspectionResult:
		try:
			return PackageReader(self.zip_path).inspect()
		except PackageReaderError as exc:
			raise DryRunImporterError(str(exc)) from exc

	def _validate_pdf_path(self) -> None:
		if not self.pdf_path.is_file():
			raise DryRunImporterError(f"Official source PDF not found: {self.pdf_path}")
