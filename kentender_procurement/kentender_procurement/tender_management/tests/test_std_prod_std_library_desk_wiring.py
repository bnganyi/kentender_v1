# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod Phase 1 — Desk wiring tests for Official STD Library page."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


def _procurement_sidebar_export_path() -> str:
	return os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"workspace_sidebar",
		"procurement.json",
	)


class TestStdProdStdLibraryDeskWiring(UnitTestCase):
	def test_hooks_register_std_library_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("std-library"),
			"public/js/std_prod_std_library_page.js",
		)

	def test_std_library_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"std_prod_std_library_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["std-library"]', source)
		self.assertIn("/assets/kentender_procurement/std_prod_impl/std_library.html", source)
		self.assertIn('testid: "std-prod-std-library"', source)
		self.assertIn("kentender.std_prod.mount_page", source)

	def test_std_library_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"std_prod_std_library_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.std-prod-std-library-shell .page-head", source)
		self.assertIn("display: none !important", source)

	def test_procurement_sidebar_export_points_official_std_library_to_std_library_page(self) -> None:
		with open(_procurement_sidebar_export_path(), encoding="utf-8") as handle:
			data = json.load(handle)
		rows = [
			row
			for row in data.get("items") or []
			if row.get("label") == "Official STD Library" and row.get("type") == "Link"
		]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].get("link_type"), "Page")
		self.assertEqual(rows[0].get("link_to"), "std-library")


class TestStdProdStdLibraryDeskWiringSite(IntegrationTestCase):
	def test_std_library_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "std-library"))

	def test_procurement_sidebar_official_std_library_targets_std_library_page(self) -> None:
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		doc = frappe.get_doc("Workspace Sidebar", "Procurement")
		rows = [
			row
			for row in doc.items
			if row.type == "Link"
			and row.label == "Official STD Library"
			and (row.link_type or "").lower() == "page"
		]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].link_to, "std-library")
