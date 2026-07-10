"""Canonical identity for KE-PPRA-IT-2022-04 extraction packages."""

from __future__ import annotations

from pathlib import Path

PACKAGE_CODE = "KE-PPRA-IT-2022-04"
FAMILY_CODE = "KE-PPRA-IT"
VERSION_CODE = "KE-PPRA-IT-2022-04"
SOURCE_DOCUMENT_KEY = "DOC-10-IT-STD-2022-04"
PDF_FILENAME = "DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf"

# v1_0 (historical register-synthesized package)
PACKAGE_ROOT_NAME = "KE-PPRA-IT-2022-04_seed_package_v1_0"
ZIP_FILENAME = "KE-PPRA-IT-2022-04_Seed_Package_v1_0.zip"
SCHEMA_VERSION = "1.0.0"
PACKAGE_QUALITY = "FULL_EXTRACTION_CANDIDATE"

# v1_1 (PDF verbatim extraction package)
PACKAGE_ROOT_NAME_V1_1 = "KE-PPRA-IT-2022-04_seed_package_v1_1"
ZIP_FILENAME_V1_1 = "KE-PPRA-IT-2022-04_Seed_Package_v1_1.zip"
SCHEMA_VERSION_V1_1 = "1.1.0"
PACKAGE_QUALITY_V1_1 = "VERBATIM_EXTRACTION_CANDIDATE"
LAYOUT_FILENAME = "it_std_layout.txt"

KENTENDER_V1_ROOT = Path(__file__).resolve().parents[2]
DOCS_STD_PROD = KENTENDER_V1_ROOT / "docs" / "std-prod"
DATA_DIR = KENTENDER_V1_ROOT / "docs" / "std-prod-impl" / "data"
WORK_DIR = DATA_DIR / PACKAGE_ROOT_NAME
WORK_DIR_V1_1 = DATA_DIR / PACKAGE_ROOT_NAME_V1_1
