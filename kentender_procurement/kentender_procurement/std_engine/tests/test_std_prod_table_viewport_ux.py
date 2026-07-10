# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod table horizontal scroll UX contract tests."""

from __future__ import annotations

import os

import frappe
from frappe.tests import UnitTestCase

_ENGINE_PATH = os.path.join(
	frappe.get_app_path("kentender_procurement"),
	"public",
	"js",
	"std_prod_engine.js",
)


class TestStdProdTableScrollUx(UnitTestCase):
	def setUp(self) -> None:
		self.source = open(_ENGINE_PATH, encoding="utf-8").read()

	def test_engine_declares_page_scroll_with_viewport_fixed_hscroll_rail(self) -> None:
		for token in (
			"std-prod-table-surface",
			"std-prod-table-scroll-host",
			"std-prod-table-hscroll-rail--viewport",
			"register_hscroll_host",
			"refresh_hscroll_rail",
			"resolve_table_surface_root",
			"stdProdNavWired",
			"enhance_table_scroll_ux",
			"data-std-prod-table-surface",
			"data-std-prod-table-scroll-host",
			"data-std-prod-table-hscroll-rail",
		):
			with self.subTest(token=token):
				self.assertIn(token, self.source)

	def test_scroll_host_uses_horizontal_overflow_without_viewport_height_lock(self) -> None:
		self.assertIn("overflow-x: auto", self.source)
		self.assertIn("overflow-y: visible", self.source)
		self.assertIn("width: max-content", self.source)
		self.assertIn("position: fixed", self.source)
		self.assertNotIn("std-prod-table-viewport", self.source)
		self.assertNotIn("height: 100vh", self.source)
		self.assertNotIn("install_table_viewport_layout", self.source)
