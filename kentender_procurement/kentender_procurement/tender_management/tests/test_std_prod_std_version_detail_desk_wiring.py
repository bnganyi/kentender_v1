# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod — Desk wiring tests for STD Version Detail page and family version actions."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestStdProdStdVersionDetailDeskWiring(UnitTestCase):
	def test_hooks_register_std_version_detail_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("std-version-detail"),
			"public/js/std_prod_std_version_detail_page.js",
		)

	def test_std_version_detail_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"std_prod_std_version_detail_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["std-version-detail"]', source)
		self.assertIn(
			"/assets/kentender_procurement/std_prod_impl/std_version_detail.html",
			source,
		)
		self.assertIn('testid: "std-prod-std-version-detail"', source)
		self.assertIn("kentender.std_prod.mount_page", source)

	def test_std_version_detail_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"std_prod_std_version_detail_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.std-prod-std-version-detail-shell .page-head", source)
		self.assertIn("display: none !important", source)

	def test_std_family_detail_page_js_wires_version_actions_to_version_detail_route(
		self,
	) -> None:
		engine = open(
			os.path.join(
				frappe.get_app_path("kentender_procurement"),
				"public",
				"js",
				"std_prod_engine.js",
			),
			encoding="utf-8",
		).read()
		self.assertIn('"open_in_new"', engine)
		self.assertIn('"edit"', engine)
		self.assertIn('"visibility"', engine)
		self.assertIn('navigate("std-version-detail"', engine)


class TestStdProdStdVersionDetailDeskWiringSite(IntegrationTestCase):
	def test_std_version_detail_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "std-version-detail"))
