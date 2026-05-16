# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-007 / LV-R5-007-01 — Business readiness checklist on Procurement Planning detail (spec §11.5)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_detail import get_pp_package_detail
from kentender_procurement.procurement_planning.pp_package_business_readiness import CHECK_ORDER

_PKG_CODE = "PKG-MOH-2026-001"


class TestR5007PackageBusinessReadiness(IntegrationTestCase):
	def _works_package_context(self):
		name = frappe.db.get_value("Procurement Package", {"package_code": _PKG_CODE}, "name")
		if not name:
			return None, None
		plan_id = frappe.db.get_value("Procurement Package", name, "plan_id")
		return name, plan_id

	def test_checklist_constants_match_spec_sequence(self):
		labels = tuple(x[1] for x in CHECK_ORDER)
		self.assertEqual(
			labels,
			(
				"Scope ready",
				"Budget linked",
				"Demand approved",
				"Procurement method selected",
				"Procurement category selected",
				"STD category identified",
				"Package released",
				"Tender created",
			),
		)

	def test_works_package_detail_business_readiness_all_pass_when_seed_present(self):
		pkg_name, _plan_id = self._works_package_context()
		if not pkg_name:
			self.skipTest("WORKS procurement package seed not present on site.")
		want_tm = frappe.db.exists("TM2 Tender", {"procurement_package_code": _PKG_CODE})
		if not want_tm:
			self.skipTest("WORKS TM2 tender linked by procurement_package_code not present.")

		out = get_pp_package_detail(package=pkg_name)
		self.assertTrue(out.get("ok"), msg=out)

		br = out.get("business_readiness")
		self.assertIsInstance(br, dict)
		ch = br.get("checks")
		self.assertEqual(len(ch), len(CHECK_ORDER))
		self.assertTrue(br.get("all_ready"), msg=ch)

		got_ids = tuple(x.get("id") for x in ch)
		self.assertEqual(got_ids, tuple(k for k, _ in CHECK_ORDER))

		for row in ch:
			self.assertTrue(row.get("ok"), msg=row)
			self.assertIn("label", row)
