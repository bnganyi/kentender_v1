# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 3 — Budget workbench consumes shared Workbench Typography v1.0 tokens."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _budget_workbench_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_budget"))
		/ "public"
		/ "css"
		/ "budget_workbench_page.css"
	)


def _rule_block(source: str, selector: str) -> str:
	return source.split(selector, 1)[1].split("}", 1)[0]


class TestBudgetWorkbenchTypographyPhase3(UnitTestCase):
	def test_font_aliases_delegate_to_shared_tokens(self) -> None:
		source = _budget_workbench_css_path().read_text(encoding="utf-8", errors="replace")
		root_block = source.split(":root {", 1)[1].split("}", 1)[0]
		for alias, shared in (
			("--ktw-font-headline", "--kt-wb-font-headline"),
			("--ktw-font-body", "--kt-wb-font-body"),
			("--ktw-font-mono", "--kt-wb-font-mono"),
		):
			self.assertIn(f"{alias}: var({shared})", root_block, msg=alias)
		self.assertNotRegex(root_block, r"--ktw-font-headline:\s*'Manrope'")

	def test_workbench_shell_uses_body_token(self) -> None:
		source = _budget_workbench_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-wbench {")
		self.assertIn("var(--kt-wb-font-body-size)", block)
		self.assertIn("var(--kt-wb-font-body)", block)

	def test_page_title_uses_title_token(self) -> None:
		source = _budget_workbench_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-wbench-title {")
		self.assertIn("var(--kt-wb-title-size)", block)
		self.assertIn("var(--kt-wb-title-line-height)", block)
		self.assertNotRegex(block, r"font-size:\s*24px")

	def test_summary_values_use_metric_token(self) -> None:
		source = _budget_workbench_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-wbench-summary-card-value {")
		self.assertIn("var(--kt-wb-metric-size)", block)
		self.assertNotRegex(block, r"font-size:\s*20px")

	def test_lines_panel_title_uses_section_token(self) -> None:
		source = _budget_workbench_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-wbench-lines-title {")
		self.assertIn("var(--kt-wb-section-size)", block)
		self.assertNotIn("font-size: 16px", block)

	def test_line_names_use_item_title_token(self) -> None:
		source = _budget_workbench_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-wbench-line-name {")
		self.assertIn("var(--kt-wb-item-title-size)", block)
		self.assertNotIn("font-size: 15px", block)

	def test_artefacts_title_uses_item_title_token(self) -> None:
		source = _budget_workbench_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-wbench-artefacts-title {")
		self.assertIn("var(--kt-wb-item-title-size)", block)
