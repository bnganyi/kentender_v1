# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bench execute entry point for STD package commit import."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path


@frappe.whitelist()
def run(zip_path: str | None = None, pdf_path: str | None = None) -> dict[str, Any]:
	"""Commit an STD seed package import as DRAFT."""
	frappe.only_for(("System Manager", "Administrator"))
	importer = CommitImporter(
		zip_path=zip_path or str(default_seed_zip_path()),
		pdf_path=pdf_path or str(default_official_pdf_path()),
	)
	return importer.run()
