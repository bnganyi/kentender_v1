# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Regression — demands with plan inclusion leave Needs Planning before packaging."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	demand_has_unpackaged_planning_inclusion,
)


class TestPP5NeedsPlanningQueueAfterInclude(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		out = ensure_pp5_needs_planning_ready(force_reset=True)
		self.assertTrue(out.get("ok"), out)

	def test_unpackaged_inclusion_flag_after_include(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self.assertFalse(demand_has_unpackaged_planning_inclusion(DEMAND_CODE))
		include_out = include_pp_demand_in_procurement_plan(
			demand_code=DEMAND_CODE,
			procurement_plan_code=PLAN_CODE,
			demand_item_codes=f'["{DEMAND_ITEM_CODE}"]',
		)
		self.assertTrue(include_out.get("ok"), include_out)
		self.assertTrue(demand_has_unpackaged_planning_inclusion(DEMAND_CODE))

	def test_approved_demand_queue_excludes_included_demand(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		include_out = include_pp_demand_in_procurement_plan(
			demand_code=DEMAND_CODE,
			procurement_plan_code=PLAN_CODE,
			demand_item_codes=f'["{DEMAND_ITEM_CODE}"]',
		)
		self.assertTrue(include_out.get("ok"), include_out)

		out = get_approved_demands_awaiting_planning({"search_text": DEMAND_CODE}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		codes = [
			str((row.get("demand") or {}).get("code") or "").strip()
			for row in out.get("rows") or []
		]
		self.assertNotIn(DEMAND_CODE, codes)
