# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-011 — WORKS seed golden path regression (District Hospital Renovation Works)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	PKG_CODE,
	PKGREL_CODE,
	PLAN_CODE,
	TENDER_CODE,
)


class TestPP8WorksSeedRegressionP8011(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self._skip = True
			return
		self._skip = False

	def test_pp8_011_works_master_seed_loads_consumed_by_tender(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		self.assertTrue(out.get("ok"), out)
		links = out.get("links") or {}
		self.assertEqual(links.get("demand"), DEMAND_CODE)
		self.assertEqual(links.get("package"), PKG_CODE)
		self.assertEqual(links.get("release"), PKGREL_CODE)
		self.assertEqual(links.get("tender"), TENDER_CODE)

	def test_pp8_011_works_master_validation_passes_golden_path(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		out = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)
		failures = out.get("failures") or []
		self.assertEqual(len(failures), 0, msg=failures)

	def test_pp8_011_active_plan_and_package_records_exist(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		self.assertTrue(frappe.db.exists("Procurement Plan", PLAN_CODE))
		self.assertTrue(frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))
