# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SEED-001/003 — KENTENDER_MVP_V1 Planning seed + validate idempotency."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C


class TestPlanningMvpSeedContract(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		from kentender_core.seeds.kentender_mvp_v1.orchestrator import run_kentender_mvp_v1

		cls.seed = run_kentender_mvp_v1(
			reset=True, force=True, validate=True
		)

	def test_seed_ok(self) -> None:
		self.assertTrue(self.seed.get("ok"), msg=str(self.seed.get("validate")))

	def test_plan_identities(self) -> None:
		self.assertTrue(
			frappe.db.exists("Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE})
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			"Approved",
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE},
				"baseline_state",
			),
			"Active",
		)

	def test_allocations_455m(self) -> None:
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

	def test_idempotent_second_run(self) -> None:
		from kentender_core.seeds.kentender_mvp_v1.orchestrator import run_kentender_mvp_v1

		before_plans = frappe.db.count(
			"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}
		)
		before_items = frappe.db.count(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}
		)
		second = run_kentender_mvp_v1(
			reset=False, force=True, validate=True
		)
		self.assertTrue(second.get("ok"), msg=str(second.get("validate")))
		self.assertEqual(
			frappe.db.count("Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}),
			before_plans,
		)
		self.assertEqual(
			frappe.db.count(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}
			),
			before_items,
		)
		self.assertEqual(before_plans, 1)
		self.assertEqual(before_items, 1)

	def test_finance_after_plan_item_and_no_contribution(self) -> None:
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"generated_reference": C.RSV_CODE}),
			1,
		)
		self.assertFalse(frappe.db.exists("DocType", "Departmental Submission"))
		self.assertFalse(
			frappe.db.exists(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			)
		)

	def test_seed_004_persona_usa(self) -> None:
		from kentender_procurement.demands.services.demand_permissions import (
			ROLE_BUSINESS,
			ROLE_REQUESTER,
		)
		from kentender_procurement.procurement_planning.services.planning_permissions import (
			ROLE_DESIGNATED_APPROVER,
			ROLE_PLANNER,
			ROLE_VIEWER,
		)

		def _usa(user: str, role: str, pe: str, ou: str | None) -> int:
			rows = frappe.get_all(
				"User Scope Assignment",
				filters={
					"user": user,
					"role": role,
					"procuring_entity": pe,
					"fixture_namespace": C.FIXTURE_NS,
				},
				fields=["organisation_unit"],
			)
			if ou:
				return sum(1 for r in rows if r.organisation_unit == ou)
			return sum(1 for r in rows if not r.organisation_unit)

		self.assertGreaterEqual(
			_usa(C.USER_MEDICAL, ROLE_REQUESTER, C.PE_MOH, C.OU_DIR_DHP), 1
		)
		self.assertGreaterEqual(
			_usa(C.USER_MEDICAL, ROLE_BUSINESS, C.PE_MOH, C.OU_DIR_DHP), 1
		)
		self.assertGreaterEqual(
			_usa(C.USER_PUBLIC, ROLE_REQUESTER, C.PE_MOH, C.OU_DIR_HRMD), 1
		)
		self.assertGreaterEqual(
			_usa(C.USER_PUBLIC, ROLE_BUSINESS, C.PE_MOH, C.OU_DIR_HRMD), 1
		)
		self.assertGreaterEqual(
			_usa(C.USER_PLANNING_OFFICER, ROLE_PLANNER, C.PE_MOH, None), 1
		)
		self.assertGreaterEqual(
			_usa(C.USER_BUD_DUAL, "Budget Officer", C.PE_MOH, None), 1
		)
		self.assertGreaterEqual(
			_usa(C.USER_PLAN_APPROVER, ROLE_DESIGNATED_APPROVER, C.PE_MOH, None), 1
		)
		self.assertGreaterEqual(_usa(C.USER_VIEWER, ROLE_VIEWER, C.PE_MOH, None), 1)

	def test_scn_add_double_run_no_duplicates(self) -> None:
		from kentender_core.seeds.kentender_mvp_v1.validate import validate_kentender_mvp_v1
		from kentender_procurement.procurement_planning.seeds import scn_pln_add_001 as scn

		first = scn.run(reset_first=False, force=True)
		self.assertTrue(first.get("ok"), first)
		report = validate_kentender_mvp_v1(
			include_demands=True, include_planning=True, include_scn_add=True
		)
		self.assertTrue(report.get("ok"), report.get("summary"))
		second = scn.run(reset_first=False, force=True)
		self.assertTrue(second.get("ok"), second)
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(
			frappe.db.count(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			),
			1,
		)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}),
			1,
		)
		self.assertAlmostEqual(flt(second.get("total")), C.PLAN_AMOUNT_V2, places=2)
