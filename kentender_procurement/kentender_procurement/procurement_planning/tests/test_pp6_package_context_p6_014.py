# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-014 — Package header stays visible across tabs."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


class TestPP6PackageContextPreservationP6014(UnitTestCase):
	def test_tab_switch_reuses_header_shell(self) -> None:
		path = (
			Path(__file__).resolve().parents[2]
			/ "public"
			/ "js"
			/ "package_detail_page.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("_shellHtml(d)", source)
		self.assertIn('data-testid="kt-pd-header"', source)
		self.assertIn("_tabsHtml(_state.activeTab)", source)
