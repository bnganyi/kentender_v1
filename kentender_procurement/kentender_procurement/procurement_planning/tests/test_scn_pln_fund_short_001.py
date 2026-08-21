# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SEED-003 / Demo v2.7 §7.7 — SCN-PLN-FUND-SHORT-001."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import FINANCE_AWAITING
from kentender_procurement.procurement_planning.seeds import scn_pln_fund_short_001 as scn
from kentender_procurement.procurement_planning.seeds.scn_pln_fund_short_001 import (
	HOLD_AMOUNT,
	HOLD_LABEL,
)


class TestScnPlnFundShort001(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.setup_result = scn.setup(force=True)

	def test_00_prepared_proposed_022(self) -> None:
		self.assertTrue(self.setup_result.get("ok"))
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE_SCN},
				"baseline_state",
			),
			"Proposed",
		)

	def test_run_creates_80_25_55_hold_without_rsv_0002(self) -> None:
		result = scn.run(reset_first=False, force=True)
		self.assertTrue(result.get("ok"), result)
		self.assertFalse(result.get("idempotent"))
		self.assertEqual(result.get("plan_item_code"), C.PLAN_ITEM_CODE_SCN)
		self.assertEqual(result.get("finance_status"), FINANCE_AWAITING)
		self.assertAlmostEqual(flt(result.get("amount_required")), C.PLAN_ITEM_SCN_AMOUNT, places=2)
		self.assertAlmostEqual(flt(result.get("available")), C.PLAN_ITEM_SCN_AMOUNT - HOLD_AMOUNT, places=2)
		self.assertAlmostEqual(flt(result.get("shortfall")), HOLD_AMOUNT, places=2)
		self.assertFalse(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)
		hold = frappe.db.get_value(
			"Funding Reservation",
			{"generated_reference": C.RSV_SHORT_CODE},
			["name", "remaining_reserved", "demand_title", "status"],
			as_dict=True,
		)
		self.assertTrue(hold)
		self.assertEqual(hold.status, "Reserved")
		self.assertAlmostEqual(flt(hold.remaining_reserved), HOLD_AMOUNT, places=2)
		self.assertEqual(hold.demand_title, HOLD_LABEL)
		line = frappe.db.get_value("Budget Line", {"generated_reference": C.BL_HWD_2027}, "name")
		self.assertAlmostEqual(
			flt(frappe.db.get_value("Budget Line", line, "amount_reserved")),
			HOLD_AMOUNT,
			places=2,
		)

	def test_second_run_idempotent(self) -> None:
		first_reserved = flt(
			frappe.db.get_value(
				"Budget Line",
				{"generated_reference": C.BL_HWD_2027},
				"amount_reserved",
			)
		)
		second = scn.run(reset_first=False, force=True)
		self.assertTrue(second.get("ok"), second)
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"generated_reference": C.RSV_SHORT_CODE}),
			1,
		)
		self.assertAlmostEqual(
			flt(
				frappe.db.get_value(
					"Budget Line",
					{"generated_reference": C.BL_HWD_2027},
					"amount_reserved",
				)
			),
			first_reserved,
			places=2,
		)

	def test_validate_include_scn_fund_short(self) -> None:
		scn.run(reset_first=False, force=True)
		from kentender_core.seeds.kentender_mvp_v1.orchestrator import (
			validate_kentender_mvp_v1,
		)

		report = validate_kentender_mvp_v1(include_scn_fund_short=True)
		self.assertTrue(report.get("ok"), report.get("summary"))

	def test_reset_restores_hwd_availability(self) -> None:
		scn.run(reset_first=False, force=True)
		reset = scn.reset(force=True)
		self.assertTrue(reset.get("ok"), reset)
		self.assertFalse(
			frappe.db.exists(
				"Funding Reservation",
				{"generated_reference": C.RSV_SHORT_CODE, "status": "Reserved"},
			)
		)
		self.assertTrue(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE}),
			"Must not delete V1 Tender reservation RSV-MOH-0001",
		)
		line = frappe.db.get_value("Budget Line", {"generated_reference": C.BL_HWD_2027}, "name")
		approved = flt(frappe.db.get_value("Budget Line", line, "approved_amount"))
		reserved = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		committed = flt(frappe.db.get_value("Budget Line", line, "amount_committed"))
		self.assertAlmostEqual(approved - reserved - committed, C.PLAN_ITEM_SCN_AMOUNT, places=2)
