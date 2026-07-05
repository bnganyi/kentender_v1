# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-007 — Package Detail Lines & Funding tab."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import PKG_CODE
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)


class TestPP6PackageLinesFundingP6007Source(UnitTestCase):
	def test_lines_funding_panel_testids(self) -> None:
		path = (
			Path(__file__).resolve().parents[2]
			/ "public"
			/ "js"
			/ "package_detail_page.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"kt-pd-panel-lines-funding",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-007)")


class TestPP6PackageLinesFundingP6007API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		frappe.db.commit()

	def test_lines_funding_totals_and_rows(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		tab = (out.get("tabs") or {}).get("lines_funding") or {}
		self.assertIn("98", tab.get("package_total_label") or "")
		self.assertEqual(tab.get("funding_label"), "Budget linked")
		self.assertTrue(tab.get("lines"), tab)
		self.assertGreaterEqual(len(tab.get("lines") or []), 1)
		row = tab["lines"][0]
		self.assertIn("demand_item_label", row)
		self.assertIn("package_line_label", row)
		self.assertIn("value_label", row)
		self.assertIn("98", row.get("value_label") or tab.get("package_total_label") or "")
