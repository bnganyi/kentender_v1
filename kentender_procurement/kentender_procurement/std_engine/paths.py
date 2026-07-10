# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Repository paths for STD Engine seed artifacts."""

from __future__ import annotations

from pathlib import Path

import frappe

SEED_ZIP_FILENAME = "KE-PPRA-IT-2022-04_Seed_Package_v1_0.zip"
SEED_ZIP_FILENAME_V1_1 = "KE-PPRA-IT-2022-04_Seed_Package_v1_1.zip"
SEED_ZIP_FILENAME_V0_2 = "KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip"
OFFICIAL_PDF_FILENAME = "DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf"


def seed_zip_path(version: str = "v1_0") -> Path:
	if version == "v1_1":
		return std_prod_data_dir() / SEED_ZIP_FILENAME_V1_1
	if version == "v0_2":
		return std_prod_data_dir() / SEED_ZIP_FILENAME_V0_2
	return std_prod_data_dir() / SEED_ZIP_FILENAME


def default_seed_zip_path_v1_1() -> Path:
	return std_prod_data_dir() / SEED_ZIP_FILENAME_V1_1


def kentender_v1_root() -> Path:
	"""Resolve ``apps/kentender_v1`` from the installed procurement app path."""
	return Path(frappe.get_app_path("kentender_procurement")).resolve().parents[1]


def std_prod_data_dir() -> Path:
	return kentender_v1_root() / "docs" / "std-prod-impl" / "data"


def default_seed_zip_path() -> Path:
	return std_prod_data_dir() / SEED_ZIP_FILENAME


def default_official_pdf_path() -> Path:
	return std_prod_data_dir() / OFFICIAL_PDF_FILENAME
