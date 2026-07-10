# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod navigation route contract tests."""

from __future__ import annotations

import os
import re

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

_ENGINE_PATH = os.path.join(
	frappe.get_app_path("kentender_procurement"),
	"public",
	"js",
	"std_prod_engine.js",
)

_NAVIGATE_ROUTE_RE = re.compile(r'navigate\(\s*"([^"]+)"')
_MODULE_ROW_BLOCK_RE = re.compile(r"var MODULE_ROW_ROUTES = \{([^}]+)\}", re.DOTALL)
_MODULE_ROW_ROUTE_RE = re.compile(r'"(std-[^"]+)"')
_ALIAS_ROUTE_RE = re.compile(r'"(std-[^"]+)":\s*"(std-[^"]+)"')
_ACTION_ROUTE_RE = re.compile(r'"(View [^"]+|Preview [^"]+|Compare [^"]+|VIEW SOURCE)":\s*"(std-[^"]+)"')

_CANONICAL_STD_PAGES = (
	"std-library",
	"std-family-detail",
	"std-version-detail",
	"std-source-doc",
	"std-section-clauses",
	"std-clause-detail",
	"std-validation-report",
	"std-audit-log",
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
	"std-review-and-approval",
	"std-usage-and-tender-bindings",
	"std-import-package-review",
	"std-version-diff-and-supersession",
)


class TestStdProdNavigationRoutes(UnitTestCase):
	def setUp(self) -> None:
		self.source = open(_ENGINE_PATH, encoding="utf-8").read()

	def test_engine_declares_registered_route_registry(self) -> None:
		self.assertIn("STD_PROD_REGISTERED_ROUTES", self.source)
		self.assertIn("STD_PROD_ROUTE_ALIASES", self.source)
		self.assertIn("resolve_std_route", self.source)
		self.assertIn("handle_schema_action_button", self.source)
		for page in _CANONICAL_STD_PAGES:
			with self.subTest(page=page):
				self.assertIn(f'"{page}"', self.source)

	def test_route_aliases_map_to_registered_pages(self) -> None:
		aliases = dict(_ALIAS_ROUTE_RE.findall(self.source))
		self.assertIn("std-section-clause-map", aliases)
		self.assertEqual(aliases["std-section-clause-map"], "std-section-clauses")
		for alias, target in aliases.items():
			with self.subTest(alias=alias, target=target):
				self.assertIn(target, _CANONICAL_STD_PAGES)

	def test_navigate_targets_are_registered_or_aliased(self) -> None:
		aliases = dict(_ALIAS_ROUTE_RE.findall(self.source))
		for route in sorted(set(_NAVIGATE_ROUTE_RE.findall(self.source))):
			resolved = aliases.get(route, route)
			with self.subTest(route=route, resolved=resolved):
				self.assertIn(resolved, _CANONICAL_STD_PAGES)

	def test_module_row_routes_are_registered(self) -> None:
		block = _MODULE_ROW_BLOCK_RE.search(self.source)
		self.assertIsNotNone(block, "MODULE_ROW_ROUTES block missing from std_prod_engine.js")
		for route in sorted(set(_MODULE_ROW_ROUTE_RE.findall(block.group(1)))):
			with self.subTest(route=route):
				self.assertIn(route, _CANONICAL_STD_PAGES)

	def test_schema_action_title_routes_are_registered(self) -> None:
		for _label, route in _ACTION_ROUTE_RE.findall(self.source):
			with self.subTest(route=route):
				self.assertIn(route, _CANONICAL_STD_PAGES)

	def test_hooks_register_all_canonical_pages(self) -> None:
		from kentender_procurement.hooks import page_js

		for page in _CANONICAL_STD_PAGES:
			with self.subTest(page=page):
				self.assertIn(page, page_js)


class TestStdProdNavigationRoutesSite(IntegrationTestCase):
	def test_canonical_std_pages_exist_on_site(self) -> None:
		for page in _CANONICAL_STD_PAGES:
			with self.subTest(page=page):
				self.assertTrue(frappe.db.exists("Page", page))
