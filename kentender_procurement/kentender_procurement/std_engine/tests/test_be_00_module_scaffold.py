# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-00 — STD Engine module scaffold and repo-convention audit gates."""

from __future__ import annotations

import importlib
import os
from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _std_engine_root() -> Path:
	return Path(frappe.get_app_path("kentender_procurement")) / "std_engine"


class TestBe00StdEngineModuleScaffold(UnitTestCase):
	def test_std_engine_package_is_importable(self) -> None:
		mod = importlib.import_module("kentender_procurement.std_engine")
		self.assertEqual(mod.MODULE_NAME, "STD Engine")

	def test_std_engine_not_under_tender_management(self) -> None:
		root = _std_engine_root()
		self.assertTrue(root.is_dir())
		tm_root = Path(frappe.get_app_path("kentender_procurement")) / "tender_management"
		self.assertNotEqual(root.parent.name, "tender_management")
		self.assertFalse(str(root).startswith(str(tm_root / "std_engine")))

	def test_required_subpackages_exist(self) -> None:
		root = _std_engine_root()
		for name in ("api", "package_import", "validation", "audit", "services", "tests"):
			self.assertTrue((root / name).is_dir(), f"missing std_engine/{name}/")

	def test_modules_txt_registers_std_engine(self) -> None:
		path = Path(frappe.get_app_path("kentender_procurement")) / "modules.txt"
		lines = path.read_text(encoding="utf-8").splitlines()
		self.assertIn("STD Engine", lines)

	def test_lifecycle_enum_matches_milestone_contract(self) -> None:
		from kentender_procurement.std_engine.constants import (
			COMMIT_TARGET_STATE_M1,
			LIFECYCLE_STATES,
			UI_MODE_READ_ONLY_INSPECTION,
		)

		self.assertEqual(
			list(LIFECYCLE_STATES),
			[
				"DRAFT",
				"STRUCTURING",
				"INTERNAL_REVIEW",
				"LEGAL_REVIEW",
				"PROCUREMENT_REVIEW",
				"APPROVED",
				"ACTIVE",
				"SUPERSEDED",
				"ARCHIVED",
			],
		)
		self.assertEqual(COMMIT_TARGET_STATE_M1, "DRAFT")
		self.assertEqual(UI_MODE_READ_ONLY_INSPECTION, "READ_ONLY_INSPECTION")

	def test_canonical_seed_paths_resolve(self) -> None:
		from kentender_procurement.std_engine.paths import (
			default_official_pdf_path,
			default_seed_zip_path,
		)

		zip_path = default_seed_zip_path()
		pdf_path = default_official_pdf_path()
		self.assertTrue(zip_path.is_file(), str(zip_path))
		self.assertTrue(pdf_path.is_file(), str(pdf_path))
		self.assertIn("KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip", zip_path.name)
		self.assertIn("DOC 10", pdf_path.name)

	def test_import_surface_modules_are_scaffolded(self) -> None:
		importlib.import_module("kentender_procurement.std_engine.api")
		importlib.import_module("kentender_procurement.std_engine.package_import")
		importlib.import_module("kentender_procurement.std_engine.validation")
		importlib.import_module("kentender_procurement.std_engine.audit")
		importlib.import_module("kentender_procurement.std_engine.services")

	def test_readme_documents_module_boundary(self) -> None:
		readme = (_std_engine_root() / "README.md").read_text(encoding="utf-8")
		self.assertIn("tender_management", readme)
		self.assertIn("must not", readme.lower())

	def test_tender_management_has_no_std_engine_importer(self) -> None:
		tm_root = Path(frappe.get_app_path("kentender_procurement")) / "tender_management"
		forbidden = tm_root / "std_engine"
		self.assertFalse(forbidden.exists())
