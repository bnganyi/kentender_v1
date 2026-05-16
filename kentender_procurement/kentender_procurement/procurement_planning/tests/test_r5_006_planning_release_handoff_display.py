# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-006 / LV-R5-006-01 — Planning Release Package handoff in Procurement Planning APIs."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_detail import get_pp_package_detail
from kentender_procurement.procurement_planning.api.package_list import get_pp_package_list
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
)

_PKG_CODE = "PKG-MOH-2026-001"
_JRN = "JRN-MOH-2026-001"
_EXPECTED_PKGREL = "PKGREL-MOH-2026-001"
_TM2_BC = "TND-MOH-2026-001"


class TestR5006PlanningReleaseHandoffWorkbench(IntegrationTestCase):
	def _works_package_context(self):
		name = frappe.db.get_value("Procurement Package", {"package_code": _PKG_CODE}, "name")
		if not name:
			return None, None
		plan_id = frappe.db.get_value("Procurement Package", name, "plan_id")
		return name, plan_id

	def test_pkgrel_code_from_journey(self):
		self.assertEqual(pkgrel_handoff_code_from_journey_code(_JRN), _EXPECTED_PKGREL)

	def test_works_package_list_planning_release_handoff(self):
		pkg_name, plan_id = self._works_package_context()
		if not pkg_name or not plan_id:
			self.skipTest("WORKS procurement package seed not present on site.")
		if not frappe.db.exists("Procurement Handoff Card", _EXPECTED_PKGREL):
			self.skipTest("WORKS Planning Release PKGREL card not present on site.")

		out = get_pp_package_list(plan=plan_id, queue_id="all_packages", limit=250)
		self.assertTrue(out.get("ok"), msg=out)
		match = next(
			(r for r in (out.get("rows") or []) if (r.get("package_code") or "") == _PKG_CODE),
			None,
		)
		self.assertIsNotNone(match)
		ph = match.get("planning_release_handoff")
		self.assertIsInstance(ph, dict, msg=ph)
		self.assertEqual(ph.get("handoff_code"), _EXPECTED_PKGREL)
		self.assertEqual(ph.get("tender_code"), _TM2_BC)

	def test_works_package_detail_planning_release_handoff(self):
		pkg_name, _plan_id = self._works_package_context()
		if not pkg_name:
			self.skipTest("WORKS procurement package seed not present on site.")
		if not frappe.db.exists("Procurement Handoff Card", _EXPECTED_PKGREL):
			self.skipTest("WORKS Planning Release PKGREL card not present on site.")

		out = get_pp_package_detail(package=pkg_name)
		self.assertTrue(out.get("ok"), msg=out)
		ph = out.get("planning_release_handoff")
		self.assertIsInstance(ph, dict, msg=ph)
		self.assertEqual(ph.get("handoff_title"), "Planning Release Package")
		self.assertEqual(ph.get("handoff_code"), _EXPECTED_PKGREL)
		self.assertEqual(ph.get("status"), "Consumed")
		self.assertEqual(ph.get("tender_code"), _TM2_BC)
		self.assertTrue(ph.get("tender_open_route"), msg=ph)
		self.assertIn("tm2-tender", ph.get("tender_open_route", "").lower())
