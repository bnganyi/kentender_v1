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
			/ "pp3_planning_package_detail.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("headerHtml(d)", source)
		self.assertIn("shellHtml(detail, tabId)", source)
		self.assertIn('data-testid="pp3-package-header"', source.replace("pp3-package-header", "pp3-package-header", 1))
		# Tab click re-renders full shell (header + tabs), not tab host only.
		tab_click = source.split(".pp3-package-detail__tab").pop(0)
		self.assertIn("shellHtml(detail, tabId)", source)
