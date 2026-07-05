# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Workbench Typography v1.0 — shared token contract."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


def _typography_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_core"))
		/ "public"
		/ "css"
		/ "kt_workbench_typography.css"
	)


class TestWorkbenchTypographyContract(UnitTestCase):
	def test_typography_css_exists(self) -> None:
		path = _typography_css_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")

	def test_typography_tokens_match_v1_spec(self) -> None:
		source = _typography_css_path().read_text(encoding="utf-8")
		expected = {
			"--kt-wb-title-size": "24px",
			"--kt-wb-metric-size": "20px",
			"--kt-wb-section-size": "16px",
			"--kt-wb-item-title-size": "15px",
			"--kt-wb-table-size": "13px",
			"--kt-wb-font-body-size": "14px",
			"--kt-wb-identity-size": "32px",
		}
		for token, value in expected.items():
			self.assertIn(f"{token}: {value}", source, msg=f"missing or wrong {token}")

	def test_utility_classes_exposed(self) -> None:
		source = _typography_css_path().read_text(encoding="utf-8")
		for cls in (".kt-wb-title", ".kt-wb-metric", ".kt-wb-section-title", ".kt-wb-item-title", ".kt-wb-identity"):
			self.assertIn(cls, source, msg=f"missing {cls}")


class TestWorkbenchTypographyHooks(IntegrationTestCase):
	def test_typography_css_registered_on_desk_hooks(self) -> None:
		found = False
		for row in frappe.get_hooks("app_include_css", default=[]):
			items = row if isinstance(row, (list, tuple)) else [row]
			for path in items:
				if path and "kt_workbench_typography.css" in str(path):
					found = True
					break
			if found:
				break
		self.assertTrue(found, "kt_workbench_typography.css must be in kentender_core app_include_css")
