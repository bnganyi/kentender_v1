# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-10 — schema screen Desk wiring tests."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

_SCHEMA_PAGES = (
	"std-parameter-dictionary",
	"std-parameter-detail",
	"std-rule-dictionary",
	"std-rule-detail",
	"std-form-schema-manager",
	"std-form-detail-field-builder",
	"std-requirement-schema-manager",
	"std-price-schedule-schema",
	"std-evaluation-schema",
	"std-render-blocks",
)

_ENGINE_PATH = os.path.join(
	frappe.get_app_path("kentender_procurement"),
	"public",
	"js",
	"std_prod_engine.js",
)


class TestBe10StdProdSchemaDeskWiring(UnitTestCase):
	def test_engine_exposes_schema_read_methods(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		for method in (
			"get_std_version_parameters",
			"get_std_parameter",
			"get_std_version_rules",
			"get_std_rule",
			"get_std_version_forms",
			"get_std_form",
			"get_std_version_requirements",
			"get_std_version_price_schedules",
			"get_std_version_evaluation_schema",
			"get_std_version_render_blocks",
		):
			with self.subTest(method=method):
				self.assertIn(method, source)

	def test_engine_registers_schema_screen_keys(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		for screen in (
			"parameters",
			"parameter",
			"rules",
			"rule",
			"forms",
			"form",
			"requirements",
			"priceSchedules",
			"evaluation",
			"renderBlocks",
		):
			with self.subTest(screen=screen):
				self.assertIn('"' + screen + '"', source)

	def test_engine_registers_version_workspace_and_module_routes(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		for label in (
			"Form Schema Manager",
			"Evaluation Schema",
			"Render Blocks",
		):
			with self.subTest(label=label):
				self.assertIn('"' + label + '": "std-', source)
		self.assertIn("data-std-workspace-route", source)
		self.assertIn("hydrate_breadcrumb_trail", source)
		self.assertIn("ensure_breadcrumb_nav", source)
		self.assertIn('setAttribute("data-testid", "std-prod-breadcrumb")', source)
		self.assertIn("version_code", source)

	def test_engine_claims_doctype_conflicting_page_routes(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		self.assertIn("install_route_conflict_guard", source)
		self.assertIn("claim_page_routes_over_doctype_conflicts", source)
		self.assertIn("std-price-schedule-schema", source)
		self.assertIn("std-evaluation-schema", source)

	def test_engine_preserves_procurement_sidebar_on_mount(self) -> None:
		source = open(_ENGINE_PATH, encoding="utf-8").read()
		self.assertIn("preserve_procurement_sidebar", source)
		self.assertIn('frappe.app.sidebar.setup(PROCUREMENT_SIDEBAR_KEY)', source)
		self.assertIn("on_page_show", source)

	def test_schema_pages_js_uses_guarded_registration(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"std_prod_schema_pages.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("PAGE_CONFIGS", source)
		self.assertIn("if (!frappe.pages[page_name])", source)
		for page in _SCHEMA_PAGES:
			with self.subTest(page=page):
				self.assertIn(f'"{page}"', source)

	def test_schema_page_hooks(self) -> None:
		from kentender_procurement.hooks import page_js

		for page in _SCHEMA_PAGES:
			with self.subTest(page=page):
				self.assertEqual(
					page_js.get(page),
					"public/js/std_prod_schema_pages.js",
				)


class TestBe10StdProdSchemaSite(IntegrationTestCase):
	def test_schema_pages_exist_on_site(self) -> None:
		for page in _SCHEMA_PAGES:
			with self.subTest(page=page):
				self.assertTrue(frappe.db.exists("Page", page))

	def test_schema_read_api_available(self) -> None:
		from kentender_procurement.std_engine.api.read import (
			get_std_parameter,
			get_std_version_parameters,
		)

		frappe.set_user("Administrator")
		package_id = "KE-PPRA-IT-2022-04"
		if not frappe.db.exists("STD Version", package_id):
			self.skipTest("Canonical STD package not imported")

		params = get_std_version_parameters(package_id)
		self.assertGreaterEqual(params["data"]["count"], 1)
		first = params["data"]["parameters"][0]
		detail = get_std_parameter(first["id"])
		self.assertEqual(detail["data"]["id"], first["id"])
