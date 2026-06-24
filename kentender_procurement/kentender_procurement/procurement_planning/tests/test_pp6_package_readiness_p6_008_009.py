# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-008 / P6-009 — Package Detail Readiness tab."""

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

_WIREFRAME_CHECKS = (
	"Demand approved",
	"Active plan exists",
	"Demand included in active plan",
	"Budget linked",
	"Package line complete",
	"Method selected",
	"Category selected",
)


class TestPP6PackageReadinessP6008Source(UnitTestCase):
	def test_readiness_panel_testids(self) -> None:
		path = (
			Path(__file__).resolve().parents[2]
			/ "public"
			/ "js"
			/ "pp3_planning_package_detail.js"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"pp3-package-readiness-panel",
			"pp3-package-readiness-summary",
			"pp3-package-readiness-checks",
			"pp3-package-readiness-run",
			"pp3-package-readiness-blockers",
			"pp3-package-readiness-resolve",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-008/P6-009)")


class TestPP6PackageReadinessP6008API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		frappe.db.commit()

	def test_readiness_checks_in_business_language(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		tab = (out.get("tabs") or {}).get("readiness") or {}
		labels = [c.get("label") for c in tab.get("checks") or []]
		for expected in _WIREFRAME_CHECKS:
			self.assertIn(expected, labels, msg=f"missing readiness check {expected}")
		self.assertNotIn("readiness_result_json", frappe.as_json(tab))
		self.assertIn("summary_label", tab)
		self.assertIn("may_run", tab)

	def test_failed_readiness_exposes_blockers_and_resolve(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		tab = (out.get("tabs") or {}).get("readiness") or {}
		if tab.get("failed"):
			self.assertTrue(tab.get("blockers"), tab)
		else:
			self.assertIsInstance(tab.get("blockers"), list)
