# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-11 — governance placeholder Desk wiring tests."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

_GOV_PAGES = (
	"std-review-and-approval",
	"std-usage-and-tender-bindings",
	"std-import-package-review",
	"std-version-diff-and-supersession",
)

_ENGINE_PATH = os.path.join(
	frappe.get_app_path("kentender_procurement"),
	"public",
	"js",
	"std_prod_engine.js",
)


class TestBe11StdProdGovernanceDeskWiring(UnitTestCase):
	def test_engine_exposes_governance_read_methods(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		for method in (
			"get_std_version_usage_bindings",
			"get_std_version_import_runs",
			"get_std_import_run",
			"get_std_version_diff",
		):
			with self.subTest(method=method):
				self.assertIn(method, source)

	def test_engine_registers_governance_screen_keys(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		for screen in ("usage", "importReview", "versionDiff", "review"):
			with self.subTest(screen=screen):
				self.assertIn('"' + screen + '"', source)
		self.assertIn("hydrate_usage_kpis", source)
		self.assertIn("usageKpis", source)
		self.assertIn("hydrate_page_header", source)
		self.assertIn("normalize_page_layout", source)

	def test_governance_pages_js_uses_guarded_registration(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"std_prod_governance_pages.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("PAGE_CONFIGS", source)
		self.assertIn("if (!frappe.pages[page_name])", source)
		for page in _GOV_PAGES:
			with self.subTest(page=page):
				self.assertIn(f'"{page}"', source)

	def test_governance_page_hooks(self) -> None:
		from kentender_procurement.hooks import page_js

		for page in _GOV_PAGES:
			with self.subTest(page=page):
				self.assertEqual(
					page_js.get(page),
					"public/js/std_prod_governance_pages.js",
				)


class TestBe11StdProdGovernanceSite(IntegrationTestCase):
	def test_governance_pages_exist_on_site(self) -> None:
		for page in _GOV_PAGES:
			with self.subTest(page=page):
				self.assertTrue(frappe.db.exists("Page", page))

	def test_governance_read_api_available(self) -> None:
		from kentender_procurement.std_engine.api.read import (
			get_std_version_diff,
			get_std_version_usage_bindings,
		)
		from kentender_procurement.std_engine.services.governance_read_service import (
			VERSION_DIFF_STUB_REASON,
		)

		frappe.set_user("Administrator")
		package_id = "KE-PPRA-IT-2022-04"
		if not frappe.db.exists("STD Version", package_id):
			self.skipTest("Canonical STD package not imported")

		usage = get_std_version_usage_bindings(package_id)
		self.assertGreaterEqual(usage["data"]["count"], 1)

		diff = get_std_version_diff(package_id)
		self.assertFalse(diff["data"]["compareAvailable"])
		self.assertEqual(diff["data"]["reason"], VERSION_DIFF_STUB_REASON)
