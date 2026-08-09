# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SEED-003 — County Draft Demand DMD-CGK-2027-006 isolation fixture."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	COUNTY_AMOUNT,
	upsert_county_draft_demand,
)


class TestDemSeed003CountyDraft(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_county_draft_is_isolated_and_idempotent(self) -> None:
		first = upsert_county_draft_demand(commit=False)
		second = upsert_county_draft_demand(commit=False)

		self.assertEqual(second["demand"], first["demand"])
		self.assertEqual(second["demand_code"], C.DEMAND_CODE_COUNTY)
		self.assertIsNone(second["allocation"])
		self.assertIsNone(second["reservation"])

		demand = frappe.get_doc("Demand", first["demand"])
		self.assertEqual(demand.demand_code, C.DEMAND_CODE_COUNTY)
		self.assertEqual(
			demand.title,
			"Solar-powered vaccine refrigerators for rural health facilities",
		)
		self.assertEqual(demand.procuring_entity, C.PE_CGKIS)
		self.assertEqual(demand.owner_org_unit, C.OU_CGK_HEALTH)
		self.assertEqual(demand.requester, C.USER_KISUMU_OFFICER)
		self.assertEqual(demand.status, "Draft")
		self.assertEqual(demand.current_stage, "Request Preparation")
		self.assertEqual(float(demand.requester_estimate), COUNTY_AMOUNT)
		self.assertFalse(demand.confirmed_estimate)
		self.assertEqual(int(demand.planning_ready or 0), 0)

		self.assertEqual(
			frappe.db.count("Demand Item", {"demand": demand.name}), 1
		)
		self.assertEqual(
			frappe.db.count("Demand Strategy Reference", {"demand": demand.name}), 0
		)
		self.assertEqual(
			frappe.db.count("Demand Funding Allocation", {"demand": demand.name}), 0
		)
		self.assertEqual(
			frappe.db.count("Funding Exception", {"demand": demand.name}), 0
		)
		self.assertEqual(
			frappe.db.count(
				"Funding Reservation", {"demand_code": C.DEMAND_CODE_COUNTY}
			),
			0,
		)
		# Cross-entity isolation: Ministry principal Demand remains distinct.
		self.assertNotEqual(demand.procuring_entity, C.PE_MOH)
