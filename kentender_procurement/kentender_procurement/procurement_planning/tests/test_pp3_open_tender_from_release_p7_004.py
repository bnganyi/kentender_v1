# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-004 — Open Tender route from Released summary."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.released_to_tender import (
	get_pp_released_package_summary,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)


class TestPP3OpenTenderFromReleaseP7004(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")

	def test_pp7_004_summary_includes_tm2_tender_open_route(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_pp_released_package_summary(package_code=PKG_CODE)
		self.assertTrue(out.get("ok"), msg=out)
		tender = out.get("tender") or {}
		route = str(tender.get("open_route") or "").strip()
		self.assertTrue(route, msg=tender)
		self.assertIn("tm2-tender", route.lower())
