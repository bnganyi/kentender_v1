# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-010 — Package Detail Review tab."""

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


class TestPP6PackageReviewP6010Source(UnitTestCase):
	def test_review_panel_testids(self) -> None:
		path = (
			Path(__file__).resolve().parents[2]
			/ "public"
			/ "js"
			/ "package_detail_page.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"kt-pd-panel-review",
			"kt-pd-review-summary",
			"kt-pd-decision-history-row",
			"kt-pd-approve",
			"kt-pd-return",
			"kt-pd-clarify",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-010)")


class TestPP6PackageReviewP6010API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		frappe.db.commit()

	def test_draft_package_review_not_submitted_with_submit_gate(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		tab = (out.get("tabs") or {}).get("review") or {}
		self.assertEqual(tab.get("status_label"), "Not submitted")
		self.assertIn("may_submit", tab)
		self.assertIn("may_approve", tab)
		self.assertIn("may_return", tab)
