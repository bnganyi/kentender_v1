# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-010 — WORKS master Demand seed replaces skip-only legacy shim."""

from __future__ import annotations

from unittest import SkipTest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.seeds.works_master_demand import (
	upsert_works_master_demand,
)
from kentender_procurement.procurement_lifecycle.legacy_demand_codes import (
	WORKS_DEMAND_CODE,
	WORKS_DEMAND_TITLE,
)
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import (
	DEMAND_TITLE,
	upsert_works_master_demand as shim_upsert,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
)


class TestDemInt010WorksMasterDemandSeed(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_shim_delegates_without_skip(self) -> None:
		try:
			first = shim_upsert()
		except SkipTest as exc:  # pragma: no cover - regression guard
			self.fail(f"legacy shim must not SkipTest after DEM-INT-010: {exc}")

		self.assertTrue(first.get("ok"))
		self.assertEqual(first.get("demand_code"), WORKS_DEMAND_CODE)
		self.assertEqual(DEMAND_TITLE, WORKS_DEMAND_TITLE)

		second = upsert_works_master_demand(commit=False)
		self.assertEqual(second["demand"], first["demand"])

		demand = frappe.get_doc("Demand", first["demand"])
		self.assertEqual(demand.demand_code, WORKS_DEMAND_CODE)
		self.assertEqual(demand.title, WORKS_DEMAND_TITLE)
		self.assertEqual(demand.status, "Approved")
		self.assertEqual(int(demand.planning_ready or 0), 1)
		self.assertEqual(demand.planning_usage, "Not taken up")
		self.assertEqual(float(demand.confirmed_estimate), float(ESTIMATED_VALUE))

		item = frappe.db.get_value(
			"Demand Item",
			{"demand": demand.name, "item_code": DEMAND_ITEM_CODE},
			["confirmed_estimate"],
			as_dict=True,
		)
		self.assertTrue(item)
		self.assertEqual(float(item.confirmed_estimate), float(ESTIMATED_VALUE))

		# Canonical resolve is demand_code (not DIA demand_id business-key lookup).
		self.assertEqual(
			frappe.db.get_value("Demand", {"demand_code": WORKS_DEMAND_CODE}, "name"),
			demand.name,
		)

		queue = get_approved_demands_awaiting_planning(
			filters={}, actor="Administrator"
		)
		self.assertTrue(queue.get("ok"))
		self.assertNotEqual(queue.get("error_code"), "DEMAND_MODULE_RETIRED")
		codes = {
			(row.get("demand") or {}).get("code") for row in (queue.get("rows") or [])
		}
		self.assertIn(WORKS_DEMAND_CODE, codes)
