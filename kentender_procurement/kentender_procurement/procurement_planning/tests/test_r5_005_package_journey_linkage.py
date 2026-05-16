# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-005 / LV-R5-005-01 — Procurement Package PLC journey linkage in Planning APIs."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_detail import get_pp_package_detail
from kentender_procurement.procurement_planning.api.package_list import get_pp_package_list
from kentender_procurement.procurement_planning.package_journey_surfaces import (
	journey_link_hints_by_package_codes,
)

_PKG_CODE = "PKG-MOH-2026-001"
_JRN = "JRN-MOH-2026-001"


class TestR5005PackageJourneyLinkage(IntegrationTestCase):
	def _works_package_context(self):
		name = frappe.db.get_value("Procurement Package", {"package_code": _PKG_CODE}, "name")
		if not name:
			return None, None
		plan_id = frappe.db.get_value("Procurement Package", name, "plan_id")
		return name, plan_id

	def test_journey_hints_empty_input(self):
		self.assertFalse(journey_link_hints_by_package_codes([]))
		self.assertFalse(journey_link_hints_by_package_codes(["", "   "]))

	def test_works_package_list_includes_procurement_journey(self):
		pkg_name, plan_id = self._works_package_context()
		if not pkg_name or not plan_id:
			self.skipTest("WORKS procurement package seed not present on site.")

		out = get_pp_package_list(plan=plan_id, queue_id="all_packages", limit=250)
		self.assertTrue(out.get("ok"), msg=out)

		match = next(
			(r for r in (out.get("rows") or []) if (r.get("package_code") or "") == _PKG_CODE),
			None,
		)
		self.assertIsNotNone(match, msg=out)
		pj = match.get("procurement_journey")
		self.assertIsInstance(pj, dict, msg=pj)
		self.assertEqual(pj.get("journey_code"), _JRN)
		self.assertTrue(pj.get("journey_title"), msg=pj)
		self.assertIn("/desk/plc-procurement-journey/", pj.get("open_route") or "")

	def test_works_package_detail_includes_procurement_journey(self):
		pkg_name, _plan_id = self._works_package_context()
		if not pkg_name:
			self.skipTest("WORKS procurement package seed not present on site.")

		out = get_pp_package_detail(package=pkg_name)
		self.assertTrue(out.get("ok"), msg=out)

		pj = out.get("procurement_journey")
		self.assertIsInstance(pj, dict, msg=pj)
		self.assertEqual(pj.get("journey_code"), _JRN)
