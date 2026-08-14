# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SEED-002 / AC-013 / AC-020 — SCN-PLN-ADD-001 Demo v2.7 §7.6."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	TAKEUP_ACTIVE,
	VERSION_APPROVED,
	VERSION_DRAFT,
	VERSION_SUPERSEDED,
)
from kentender_procurement.procurement_planning.seeds import scn_pln_add_001 as scn


def _draft_total(plan_name: str, version_name: str) -> float:
	total = 0.0
	for it in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]]},
		pluck="name",
	):
		amt = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": it, "plan_version": version_name},
			"confirmed_estimate",
		)
		total += flt(amt)
	return total


class TestScnPlnAdd001(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.setup_result = scn.setup(force=True)

	def test_00_setup_base_planning(self) -> None:
		self.assertTrue(self.setup_result.get("ok"))
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			VERSION_APPROVED,
		)
		self.assertFalse(
			frappe.db.exists(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			)
		)
		self.assertFalse(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)

	def test_demand_ready_without_reservation(self) -> None:
		result = scn.run(reset_first=False, force=True, stop_before_finance=True)
		self.assertTrue(result.get("ok"), result)
		demand = frappe.db.get_value(
			"Demand", {"demand_code": C.DEMAND_CODE_RETURNED}, "name"
		)
		row = frappe.db.get_value(
			"Demand",
			demand,
			["status", "planning_ready", "confirmed_estimate"],
			as_dict=True,
		)
		self.assertEqual(row.status, "Approved")
		self.assertEqual(int(row.planning_ready or 0), 1)
		self.assertAlmostEqual(flt(row.confirmed_estimate), C.PLAN_ITEM_SCN_AMOUNT, places=2)
		self.assertFalse(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)
		self.assertTrue(
			frappe.db.exists(
				"Demand Decision",
				{"demand": demand, "decision": "Support", "actor": C.USER_BUSINESS_APPROVER},
			)
		)

	def test_draft_535m_v1_and_tender_remain_operational(self) -> None:
		result = scn.run(reset_first=False, force=True, stop_before_finance=True)
		self.assertTrue(result.get("ok"), result)
		self.assertTrue(result.get("stopped_before_finance"))
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE_SCN},
				"baseline_state",
			),
			ITEM_PROPOSED,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
				"status",
			),
			VERSION_DRAFT,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			VERSION_APPROVED,
		)
		plan = frappe.db.get_value(
			"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}, "name"
		)
		v1 = frappe.db.get_value(
			"Procurement Plan Version",
			{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
			"name",
		)
		v2 = frappe.db.get_value(
			"Procurement Plan Version",
			{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
			"name",
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan", plan, "current_approved_version"),
			v1,
		)
		self.assertAlmostEqual(_draft_total(plan, v2), C.PLAN_AMOUNT_V2, places=2)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE},
				"baseline_state",
			),
			ITEM_ACTIVE,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE},
				"tender_takeup_projection",
			),
			TAKEUP_ACTIVE,
		)
		item_021 = frappe.db.get_value(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}, "name"
		)
		handoff = frappe.db.get_value(
			"Planning Handoff Snapshot",
			{"plan_item": item_021},
			"tender_reference",
		)
		self.assertEqual(handoff, C.TENDER_CODE)
		self.assertFalse(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)

	def test_finance_creates_rsv_0002_v1_still_approved(self) -> None:
		result = scn.run(reset_first=False, force=True, stop_before_approve=True)
		self.assertTrue(result.get("ok"), result)
		self.assertTrue(result.get("stopped_before_approve"))
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}),
			1,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			VERSION_APPROVED,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
				"status",
			),
			VERSION_DRAFT,
		)

	def test_run_adds_022_and_535m(self) -> None:
		result = scn.run(reset_first=False, force=True)
		self.assertTrue(result.get("ok"), result)
		self.assertFalse(result.get("idempotent"))
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE_SCN},
				"baseline_state",
			),
			ITEM_ACTIVE,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
				"status",
			),
			VERSION_APPROVED,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			VERSION_SUPERSEDED,
		)
		self.assertAlmostEqual(flt(result.get("total")), C.PLAN_AMOUNT_V2, places=2)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}),
			1,
		)
		item_021 = frappe.db.get_value(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}, "name"
		)
		self.assertEqual(
			frappe.db.get_value(
				"Planning Handoff Snapshot",
				{"plan_item": item_021},
				"tender_reference",
			),
			C.TENDER_CODE,
		)

	def test_second_run_idempotent(self) -> None:
		first_count = frappe.db.count(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
		)
		rsv_count = frappe.db.count(
			"Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}
		)
		second = scn.run(reset_first=False, force=True)
		self.assertTrue(second.get("ok"), second)
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(
			frappe.db.count(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			),
			first_count,
		)
		self.assertEqual(first_count, 1)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}),
			rsv_count,
		)

	def test_reset_restores_base(self) -> None:
		scn.run(reset_first=False, force=True)
		reset = scn.reset(force=True)
		self.assertTrue(reset.get("ok"))
		self.assertFalse(
			frappe.db.exists(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			)
		)
		self.assertFalse(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			VERSION_APPROVED,
		)
		item = frappe.db.get_value(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}, "name"
		)
		total = sum(
			flt(r.allocated_amount)
			for r in frappe.get_all(
				"Plan Demand Allocation",
				filters={"plan_item": item, "status": "Effective"},
				fields=["allocated_amount"],
			)
		)
		self.assertAlmostEqual(total, C.PLAN_AMOUNT_V1, places=2)
		demand = frappe.db.get_value(
			"Demand", {"demand_code": C.DEMAND_CODE_RETURNED}, "name"
		)
		self.assertEqual(frappe.db.get_value("Demand", demand, "status"), "Returned")
