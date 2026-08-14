# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-024 — repeatable MOH + Kisumu Demands seed without duplicates."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.seeds.kentender_mvp_v1.demands import upsert_demands
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	upsert_county_draft_demand,
	upsert_principal_approved_demand,
	upsert_returned_shortfall_demand,
)


class TestDemandSeedRepeatability(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_ac024_moh_and_kisumu_upsert_idempotent(self) -> None:
		"""DIA-AC-024 — MOH + Kisumu fixtures rebuild without duplicate records."""
		self.assertTrue(
			frappe.db.get_value(
				"Budget Line", {"generated_reference": C.BL_DHI_2027}, "name"
			),
			"Budget line MOH-BL-DHI-2027 required before Demands AC-024",
		)

		first = upsert_demands()
		second = upsert_demands()
		self.assertEqual(second["principal"]["demand"], first["principal"]["demand"])
		self.assertEqual(second["returned"]["demand"], first["returned"]["demand"])
		self.assertEqual(second["county"]["demand"], first["county"]["demand"])

		for code in (C.DEMAND_CODE, C.DEMAND_CODE_RETURNED, C.DEMAND_CODE_COUNTY):
			self.assertEqual(
				frappe.db.count("Demand", {"demand_code": code}),
				1,
				msg=f"duplicate Demand for {code}",
			)

		# Direct loaders remain idempotent independently.
		p1 = upsert_principal_approved_demand(commit=False)
		p2 = upsert_principal_approved_demand(commit=False)
		self.assertEqual(p1["demand"], p2["demand"])
		r1 = upsert_returned_shortfall_demand(commit=False)
		r2 = upsert_returned_shortfall_demand(commit=False)
		self.assertEqual(r1["demand"], r2["demand"])
		c1 = upsert_county_draft_demand(commit=False)
		c2 = upsert_county_draft_demand(commit=False)
		self.assertEqual(c1["demand"], c2["demand"])

		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": C.DEMAND_CODE}),
			0,
		)
		self.assertEqual(
			frappe.db.get_value("Demand", p1["demand"], "procuring_entity"),
			C.PE_MOH,
		)
		self.assertEqual(
			frappe.db.get_value("Demand", c1["demand"], "procuring_entity"),
			C.PE_CGKIS,
		)
