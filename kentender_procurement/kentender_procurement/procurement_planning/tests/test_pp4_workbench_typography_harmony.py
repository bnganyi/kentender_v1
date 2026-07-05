# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP4 Planning Workbench — typography harmonization contract."""

from __future__ import annotations

import re
from pathlib import Path

from frappe.tests import UnitTestCase


def _pp3_css_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "css"
		/ "pp3_planning_design_system.css"
	)


def _harmony_css_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "css"
		/ "pp4_workbench_typography_harmony.css"
	)


def _iframe_html_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "workbench_design"
		/ "needs_planning_default.html"
	)


class TestPP4WorkbenchTypographyHarmony(UnitTestCase):
	def test_pp3_workbench_title_uses_shared_token(self) -> None:
		source = _pp3_css_path().read_text(encoding="utf-8", errors="replace")
		block = source.split("body.kt-pp2-shell .pp3-workbench-toolbar__title", 1)[1].split("}", 1)[0]
		self.assertIn("var(--kt-wb-title-size)", block)
		self.assertNotIn("38px", block)

	def test_pp3_kpi_values_use_metric_token(self) -> None:
		source = _pp3_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			"body.kt-pp4-shell .pp4-stat-card__value",
			"body.kt-pp4-shell .pp4-np-kpi__value",
		):
			block = source.split(selector, 1)[1].split("}", 1)[0]
			self.assertIn("var(--kt-wb-metric-size)", block, msg=selector)
			self.assertNotRegex(block, r"font-size:\s*2[4-9]px", msg=selector)

	def test_pp3_list_titles_use_item_token(self) -> None:
		source = _pp3_css_path().read_text(encoding="utf-8", errors="replace")
		block = source.split("body.kt-pp2-shell .pp3-work-list__title {", 1)[1].split("}", 1)[0]
		self.assertIn("var(--kt-wb-item-title-size)", block)
		self.assertNotIn("20px", block)

	def test_harmony_css_targets_iframe_display_hero(self) -> None:
		source = _harmony_css_path().read_text(encoding="utf-8", errors="replace")
		self.assertIn("font-display-hero", source)
		self.assertIn("var(--kt-wb-title-size)", source)
		self.assertIn("var(--kt-wb-metric-size)", source)
		self.assertIn("div.font-display-hero.text-display-hero", source)

	def test_iframe_loads_typography_stylesheets(self) -> None:
		html = _iframe_html_path().read_text(encoding="utf-8", errors="replace")
		self.assertIn("/assets/kentender_core/css/kt_workbench_typography.css", html)
		self.assertIn("/assets/kentender_procurement/css/pp4_workbench_typography_harmony.css", html)

	def test_no_oversized_literals_in_pp3_workbench_selectors(self) -> None:
		source = _pp3_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			"body.kt-pp4-shell .pp4-np-title",
			"body.kt-pp4-shell .pp4-hero__title",
		):
			block = source.split(selector, 1)[1].split("}", 1)[0]
			self.assertIn("var(--kt-wb-title-size)", block, msg=selector)
			self.assertNotRegex(block, r"font-size:\s*3[0-9]px", msg=selector)
