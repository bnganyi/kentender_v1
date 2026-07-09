# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-09 — vertical slice Desk wiring tests."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

_SLICE_PAGES = (
	"std-source-doc",
	"std-section-clauses",
	"std-clause-detail",
	"std-validation-report",
	"std-audit-log",
)

_ENGINE_PATH = os.path.join(
	frappe.get_app_path("kentender_procurement"),
	"public",
	"js",
	"std_prod_engine.js",
)


class TestBe09StdProdEngine(UnitTestCase):
	def test_engine_exposes_read_client_and_defaults(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		self.assertIn("kentender.std_prod.DEFAULT_PACKAGE_ID", source)
		self.assertGreaterEqual(source.count("KE-PPRA-IT-2022-04"), 1)
		self.assertIn("get_std_families", source)
		self.assertIn("get_std_version_validation_report", source)
		self.assertIn("get_std_version_audit_log", source)
		self.assertIn("button_contains_label", source)
		self.assertIn("std-source-doc", source)
		self.assertIn("__stdProdSectionsState", source)
		self.assertIn("std-prod-clause-title", source)
		self.assertIn("should_refresh_on_show", source)
		self.assertIn('type: "GET"', source)
		self.assertIn("data-std-package-id", source)

	def test_library_page_uses_shared_engine(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"std_prod_std_library_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("kentender.std_prod.mount_page", source)
		self.assertIn('screen: "library"', source)

	def test_vertical_slice_pages_register_all_routes(self) -> None:
		from kentender_procurement.hooks import page_js

		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"std_prod_vertical_slice_pages.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("PAGE_CONFIGS", source)
		self.assertIn("if (!frappe.pages[page_name])", source)
		for page in _SLICE_PAGES:
			with self.subTest(page=page):
				self.assertEqual(
					page_js.get(page),
					"public/js/std_prod_vertical_slice_pages.js",
				)
				self.assertIn(f'"{page}"', source)


class TestBe09StdProdVerticalSliceSite(IntegrationTestCase):
	def test_vertical_slice_pages_exist_on_site(self) -> None:
		for page in _SLICE_PAGES:
			with self.subTest(page=page):
				self.assertTrue(frappe.db.exists("Page", page))

	def test_read_api_available_for_slice(self) -> None:
		from kentender_procurement.std_engine.api.read import (
			get_std_families,
			get_std_version_audit_log,
			get_std_version_validation_report,
		)

		frappe.set_user("Administrator")
		families = get_std_families()
		self.assertIn("packageContext", families)
		self.assertIn("data", families)

		package_id = "KE-PPRA-IT-2022-04"
		if frappe.db.exists("STD Version", package_id):
			report = get_std_version_validation_report(package_id)
			audit = get_std_version_audit_log(package_id)
			self.assertEqual(report["packageContext"]["packageId"], package_id)
			self.assertFalse(report["packageContext"]["canEdit"])
			self.assertEqual(report["packageContext"]["uiMode"], "READ_ONLY_INSPECTION")
			self.assertGreaterEqual(audit["data"]["count"], 0)
