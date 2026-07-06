# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0002 — shared STD Config CSS uses Workbench Typography v1.0 tokens (phase-3 rigor)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _shared_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_config_shared.css"
	)


def _library_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_library_page.css"
	)


def _configurator_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_configurator_page.css"
	)


def _rule_block(source: str, selector: str) -> str:
	return source.split(selector, 1)[1].split("}", 1)[0]


class TestStdConfigTypography(UnitTestCase):
	def test_shared_font_aliases_delegate_to_wb_tokens(self) -> None:
		source = _shared_css_path().read_text(encoding="utf-8", errors="replace")
		root_block = source.split(":root {", 1)[1].split("}", 1)[0]
		for alias, shared in (
			("--kt-std-font-headline", "--kt-wb-font-headline"),
			("--kt-std-font-body", "--kt-wb-font-body"),
			("--kt-std-font-mono", "--kt-wb-font-mono"),
		):
			self.assertIn(f"{alias}: var({shared}", root_block, msg=alias)

	def test_library_root_uses_body_token(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-lib-root {")
		self.assertIn("var(--kt-wb-font-body-size)", block)
		self.assertNotIn("--kt-wb-body-size", block)

	def test_library_title_uses_title_token(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-lib-title {")
		self.assertIn("var(--kt-wb-title-size)", block)
		self.assertIn("var(--kt-wb-title-line-height)", block)
		self.assertNotRegex(block, r"font-size:\s*28px")
		self.assertNotRegex(block, r"font-size:\s*24px")

	def test_library_kpi_uses_metric_token(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-lib-kpi-value {")
		self.assertIn("var(--kt-wb-metric-size)", block)
		self.assertIn("var(--kt-wb-metric-weight)", block)
		self.assertNotRegex(block, r"font-size:\s*20px")

	def test_configurator_root_uses_body_token(self) -> None:
		source = _configurator_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-cfg-root {")
		self.assertIn("var(--kt-wb-font-body-size)", block)

	def test_configurator_title_uses_title_token(self) -> None:
		source = _configurator_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-cfg-title {")
		self.assertIn("var(--kt-wb-title-size)", block)
		self.assertIn("var(--kt-wb-title-line-height)", block)

	def test_configurator_section_uses_section_token(self) -> None:
		source = _configurator_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-cfg-section-title {")
		self.assertIn("var(--kt-wb-section-size)", block)
		self.assertNotIn("font-size: 16px", block)

	def test_configurator_table_uses_table_token(self) -> None:
		source = _configurator_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-cfg-table {")
		self.assertIn("var(--kt-wb-table-size)", block)

	def test_shared_spacing_tokens_defined(self) -> None:
		source = _shared_css_path().read_text(encoding="utf-8", errors="replace")
		root_block = source.split(":root {", 1)[1].split("}", 1)[0]
		for token in (
			"--kt-std-section-gap",
			"--kt-std-stack-gap-md",
			"--kt-std-card-padding",
			"--kt-std-body-padding",
			"--kt-std-topbar-height",
			"--kt-std-table-cell-padding",
		):
			self.assertIn(token, root_block, msg=token)

	def test_library_health_title_uses_section_token(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-lib-health__title {")
		self.assertIn("var(--kt-wb-section-size)", block)
		self.assertNotRegex(block, r"font-size:\s*1[89]px")

	def test_library_table_and_row_typography(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		table_block = _rule_block(source, ".kt-std-lib-table {")
		self.assertIn("var(--kt-wb-table-size)", table_block)
		row_block = source.split("\n.kt-std-lib-row-title {", 1)[1].split("}", 1)[0]
		self.assertIn("var(--kt-wb-item-title-size)", row_block)

	def test_library_body_uses_density_padding_token(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-std-lib-body {")
		self.assertIn("var(--kt-std-body-padding)", block)

	def test_library_css_no_mockup_hero_literals(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		self.assertNotIn("font-size: 28px", source)
		self.assertNotIn("font-size: 36px", source)
		self.assertNotRegex(source, r"\.kt-std-lib-kpi-value[^}]*font-size:\s*2[4-9]px")

	def test_no_invalid_body_size_token_in_std_css(self) -> None:
		for path in (_library_css_path(), _configurator_css_path()):
			source = path.read_text(encoding="utf-8", errors="replace")
			self.assertNotIn("--kt-wb-body-size", source, msg=str(path))
