# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 2 — Hub, Package Detail, Package Wizard typography harmonization."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _css(name: str) -> Path:
	return Path(__file__).resolve().parents[2] / "public" / "css" / name


def _rule_block(source: str, selector: str) -> str:
	return source.split(selector, 1)[1].split("}", 1)[0]


class TestProcurementTypographyPhase2Harmony(UnitTestCase):
	def test_planning_hub_titles_use_title_token(self) -> None:
		source = _css("planning_hub_page.css").read_text(encoding="utf-8", errors="replace")
		for selector in (".kt-pph-header__title", ".kt-pph-hero__title"):
			block = _rule_block(source, selector)
			self.assertIn("var(--kt-wb-title-size)", block, msg=selector)
			self.assertNotRegex(block, r"font-size:\s*2[89]px", msg=selector)

	def test_planning_hub_stat_values_use_metric_token(self) -> None:
		source = _css("planning_hub_page.css").read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-pph-stat__value")
		self.assertIn("var(--kt-wb-metric-size)", block)
		self.assertNotRegex(block, r"font-size:\s*2[4-9]px")

	def test_package_detail_identity_title_uses_identity_token(self) -> None:
		source = _css("package_detail_page.css").read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-pd-title")
		self.assertIn("var(--kt-wb-identity-size)", block)
		self.assertNotIn("font-size: 28px", block)

	def test_package_detail_card_titles_use_section_token(self) -> None:
		source = _css("package_detail_page.css").read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-pd-card__title")
		self.assertIn("var(--kt-wb-section-size)", block)
		self.assertNotIn("font-size: 20px", block)

	def test_package_detail_sidebar_metrics_use_metric_token(self) -> None:
		source = _css("package_detail_page.css").read_text(encoding="utf-8", errors="replace")
		for selector in (".kt-pd-summary-value", ".kt-pd-bento-value"):
			block = _rule_block(source, selector)
			self.assertIn("var(--kt-wb-metric-size)", block, msg=selector)
			self.assertNotRegex(block, r"font-size:\s*2[89]px", msg=selector)

	def test_package_wizard_titles_use_title_token(self) -> None:
		source = _css("create_package_wizard_page.css").read_text(encoding="utf-8", errors="replace")
		for selector in (".kt-pw-title", ".kt-pw-success-title"):
			block = _rule_block(source, selector)
			self.assertIn("var(--kt-wb-title-size)", block, msg=selector)
			self.assertNotRegex(block, r"font-size:\s*2[689]px", msg=selector)

	def test_package_wizard_summary_hero_uses_metric_token(self) -> None:
		source = _css("create_package_wizard_page.css").read_text(encoding="utf-8", errors="replace")
		block = _rule_block(source, ".kt-pw-summary-hero")
		self.assertIn("var(--kt-wb-metric-size)", block)
		self.assertNotIn("font-size: 30px", block)
