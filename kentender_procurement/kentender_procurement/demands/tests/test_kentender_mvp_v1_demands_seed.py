# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SEED-001 — principal approved Demand canonical fixture."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	upsert_principal_approved_demand,
)


class TestKentenderMvpV1DemandsSeed(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_principal_approved_demand_is_canonical_and_idempotent(self) -> None:
		self.assertTrue(
			frappe.db.get_value(
				"Budget Line", {"generated_reference": C.BL_DHI_2027}, "name"
			),
			"Budget seed must provide MOH-BL-DHI-2027",
		)

		first = upsert_principal_approved_demand(commit=False)
		first_counts = self._related_counts(first["demand"])
		second = upsert_principal_approved_demand(commit=False)

		self.assertEqual(second["demand"], first["demand"])
		self.assertIsNone(second["reservation"])
		self.assertEqual(self._related_counts(second["demand"]), first_counts)
		self.assertEqual(
			frappe.db.count(
				"Funding Reservation",
				{"demand_code": C.DEMAND_CODE, "fixture_namespace": C.FIXTURE_NS},
			),
			0,
		)

		demand = frappe.get_doc("Demand", first["demand"])
		self.assertEqual(demand.demand_code, C.DEMAND_CODE)
		self.assertEqual(demand.title, "National digital health infrastructure upgrade")
		self.assertEqual(demand.procuring_entity, C.PE_MOH)
		self.assertEqual(demand.owner_org_unit, C.OU_DIR_DHP)
		self.assertEqual(demand.status, "Approved")
		self.assertEqual(demand.current_stage, "Complete")
		self.assertEqual(demand.planning_ready, 1)
		self.assertEqual(demand.planning_usage, "Not taken up")
		self.assertEqual(float(demand.confirmed_estimate), 455_000_000)
		self.assertEqual(str(demand.required_by_date), "2028-03-31")

		items = frappe.get_all(
			"Demand Item",
			filters={"demand": demand.name},
			fields=["item_code", "description", "confirmed_estimate"],
			order_by="item_code asc",
		)
		self.assertEqual(
			[(row.item_code, row.description) for row in items],
			[
				("DMDITEM-MOH-2027-014-001", "Resilient compute and storage platform"),
				(
					"DMDITEM-MOH-2027-014-002",
					"Network, monitoring and implementation services",
				),
			],
		)
		self.assertEqual(sum(float(row.confirmed_estimate) for row in items), 455_000_000)

		strategy_refs = frappe.get_all(
			"Demand Strategy Reference",
			filters={"demand": demand.name},
			fields=["reference_type", "target_code"],
			order_by="reference_type asc",
		)
		self.assertEqual(
			{(row.reference_type, row.target_code) for row in strategy_refs},
			{
				("Primary", C.TGT_AVAIL_2028),
				("Supporting", C.TGT_RESTORE_2028),
			},
		)
		self.assertEqual(
			frappe.db.count("Demand Value Treatment", {"demand": demand.name}),
			4,
		)

		allocation = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": demand.name},
			[
				"budget_line",
				"allocation_amount",
				"bo_confirmation_status",
				"funding_reservation",
			],
			as_dict=True,
		)
		self.assertEqual(
			frappe.db.get_value("Budget Line", allocation.budget_line, "generated_reference"),
			C.BL_DHI_2027,
		)
		self.assertEqual(float(allocation.allocation_amount), 455_000_000)
		self.assertNotEqual(allocation.bo_confirmation_status, "Confirmed")
		self.assertFalse(allocation.funding_reservation)

		snapshot = json.loads(demand.approved_baseline_snapshot)
		self.assertEqual(snapshot["demand_code"], C.DEMAND_CODE)
		self.assertFalse(snapshot.get("reservation"))

	@staticmethod
	def _related_counts(demand: str) -> dict[str, int]:
		return {
			doctype: frappe.db.count(doctype, {"demand": demand})
			for doctype in (
				"Demand Item",
				"Demand Strategy Reference",
				"Demand Value Treatment",
				"Demand Funding Allocation",
			)
		}
