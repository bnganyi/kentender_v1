# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SEED-002 — Returned shortfall Demand DMD-MOH-2027-019."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	RETURNED_AMOUNT,
	RETURNED_REASON,
	RETURNED_SHORTFALL,
	upsert_returned_shortfall_demand,
)


class TestDemSeed002ReturnedShortfall(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_returned_shortfall_demand_is_canonical_and_idempotent(self) -> None:
		self.assertTrue(
			frappe.db.get_value(
				"Budget Line", {"generated_reference": C.BL_HWD_2027}, "name"
			),
			"Budget portfolio must provide MOH-BL-HWD-2027",
		)

		first = upsert_returned_shortfall_demand(commit=False)
		second = upsert_returned_shortfall_demand(commit=False)

		self.assertEqual(second["demand"], first["demand"])
		self.assertEqual(second["demand_code"], C.DEMAND_CODE_RETURNED)
		self.assertIsNone(second["reservation"])
		self.assertEqual(second["shortfall"], RETURNED_SHORTFALL)
		self.assertEqual(
			frappe.db.count(
				"Funding Reservation", {"demand_code": C.DEMAND_CODE_RETURNED}
			),
			0,
		)

		demand = frappe.get_doc("Demand", first["demand"])
		self.assertEqual(demand.demand_code, C.DEMAND_CODE_RETURNED)
		self.assertEqual(
			demand.title, "Digital health technical staff certification programme"
		)
		self.assertEqual(demand.procuring_entity, C.PE_MOH)
		self.assertEqual(demand.owner_org_unit, C.OU_DIR_HRMD)
		self.assertEqual(demand.requester, C.USER_PUBLIC)
		self.assertEqual(demand.current_owner, C.USER_PUBLIC)
		self.assertEqual(demand.status, "Returned")
		self.assertEqual(demand.current_stage, "Request Preparation")
		self.assertEqual(int(demand.planning_ready or 0), 0)
		self.assertEqual(float(demand.confirmed_estimate), RETURNED_AMOUNT)

		items = frappe.get_all(
			"Demand Item",
			filters={"demand": demand.name},
			fields=["item_code", "confirmed_estimate"],
		)
		self.assertEqual(len(items), 1)
		self.assertEqual(float(items[0].confirmed_estimate), RETURNED_AMOUNT)

		refs = frappe.get_all(
			"Demand Strategy Reference",
			filters={"demand": demand.name},
			fields=["reference_type", "target_code"],
		)
		self.assertEqual(len(refs), 1)
		self.assertEqual(refs[0].reference_type, "Primary")
		self.assertEqual(refs[0].target_code, C.TGT_SKILLS_2029)

		allocation = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": demand.name},
			[
				"budget_line",
				"allocation_amount",
				"bo_confirmation_status",
				"funds_check_result",
				"funding_reservation",
			],
			as_dict=True,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Budget Line", allocation.budget_line, "generated_reference"
			),
			C.BL_HWD_2027,
		)
		self.assertEqual(float(allocation.allocation_amount), RETURNED_AMOUNT)
		self.assertEqual(allocation.bo_confirmation_status, "Returned")
		self.assertEqual(allocation.funds_check_result, "Insufficient")
		self.assertFalse(allocation.funding_reservation)

		exc = frappe.db.get_value(
			"Funding Exception",
			{"demand": demand.name, "exception_type": "Insufficient Funding"},
			["status", "resolution_reason"],
			as_dict=True,
		)
		self.assertEqual(exc.status, "Resolved")
		self.assertEqual(exc.resolution_reason, RETURNED_REASON)

		ret = frappe.db.get_value(
			"Demand Decision",
			{
				"demand": demand.name,
				"stage": "Budget Confirmation",
				"decision": "Return",
			},
			["reason", "actor_role"],
			as_dict=True,
		)
		self.assertEqual(ret.reason, RETURNED_REASON)
		self.assertEqual(ret.actor_role, "Budget Officer")

		open_exc = frappe.db.count(
			"Funding Exception",
			{
				"demand": demand.name,
				"status": ["in", ["Open", "In Progress"]],
			},
		)
		self.assertEqual(open_exc, 0)
