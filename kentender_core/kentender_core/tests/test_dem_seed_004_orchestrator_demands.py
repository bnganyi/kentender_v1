# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SEED-004…007 — Demands upsert/clear/validate on the full MVP seed stack."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.seeds.kentender_mvp_v1.clear_demands import (
	clear_kentender_mvp_v1_demands,
)
from kentender_core.seeds.kentender_mvp_v1.demands import upsert_demands
from kentender_core.seeds.kentender_mvp_v1.validate import validate_kentender_mvp_v1


class TestDemSeed004OrchestratorDemands(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_upsert_clear_and_demands_validate(self) -> None:
		self.assertTrue(
			frappe.db.get_value(
				"Funding Reservation", {"generated_reference": C.RSV_CODE}, "name"
			),
			"Budget portfolio must provide RSV-MOH-0001 before Demands stage",
		)

		first = upsert_demands()
		self.assertTrue(first.get("ok"))
		self.assertEqual(first["principal"]["demand_code"], C.DEMAND_CODE)
		self.assertEqual(first["returned"]["demand_code"], C.DEMAND_CODE_RETURNED)
		self.assertEqual(first["county"]["demand_code"], C.DEMAND_CODE_COUNTY)

		second = upsert_demands()
		self.assertEqual(second["principal"]["demand"], first["principal"]["demand"])
		self.assertEqual(second["returned"]["demand"], first["returned"]["demand"])
		self.assertEqual(second["county"]["demand"], first["county"]["demand"])

		report = validate_kentender_mvp_v1(include_demands=True)
		demand_checks = [c for c in report["checks"] if c["name"].startswith("demands.")]
		self.assertTrue(demand_checks, "Demands invariant checks must run")
		failed_demands = [c for c in demand_checks if not c["ok"]]
		self.assertFalse(failed_demands, msg=failed_demands)

		cleared = clear_kentender_mvp_v1_demands()
		self.assertTrue(cleared.get("ok"))
		self.assertEqual(
			frappe.db.count(
				"Demand",
				{
					"demand_code": [
						"in",
						[
							C.DEMAND_CODE,
							C.DEMAND_CODE_RETURNED,
							C.DEMAND_CODE_COUNTY,
						],
					]
				},
			),
			0,
		)
		# RSV identity survives Demands clear.
		self.assertEqual(
			frappe.db.count(
				"Funding Reservation", {"generated_reference": C.RSV_CODE}
			),
			1,
		)

		# Re-seed after clear remains valid.
		again = upsert_demands()
		self.assertTrue(again.get("ok"))
		report2 = validate_kentender_mvp_v1(include_demands=True)
		failed2 = [
			c
			for c in report2["checks"]
			if c["name"].startswith("demands.") and not c["ok"]
		]
		self.assertFalse(failed2, msg=failed2)
