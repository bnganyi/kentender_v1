# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-016 — cancel after partial consume releases unconsumed only."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_procurement.demands.services.demand_lifecycle import (
	cancel_and_release_demand,
	consume_demand_in_planning,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_approved,
)


class TestDemandCancelRelease(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac016_cancel_releases_unconsumed_balance_only(self) -> None:
		"""DIA-AC-016 — after partial consume, cancel releases remainder only."""
		actors = actor_bundle("dem-ac016")
		name = advance_to_approved(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC016 cancel release",
		)
		code = frappe.db.get_value("Demand", name, "demand_code")
		item = frappe.db.get_value("Demand Item", {"demand": name}, "name")
		rsv_name = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": name},
			"funding_reservation",
		)
		self.assertTrue(rsv_name)
		self.assertAlmostEqual(
			flt(frappe.db.get_value("Funding Reservation", rsv_name, "remaining_reserved")),
			1000.0,
		)

		consume_demand_in_planning(
			demand=name,
			demand_item=item,
			consumed_amount=400,
			user=actors["planner"],
		)
		self.assertAlmostEqual(
			flt(frappe.db.get_value("Funding Reservation", rsv_name, "remaining_reserved")),
			600.0,
		)
		self.assertEqual(
			frappe.db.get_value("Funding Reservation", rsv_name, "status"),
			"Partially converted",
		)

		decisions_before = frappe.db.count("Demand Decision", {"demand": name})
		cancelled = cancel_and_release_demand(
			demand=name, reason="Programme cancelled", user=actors["paa"]
		)
		self.assertEqual(cancelled["demand"]["status"], "Cancelled")
		rsv = frappe.get_doc("Funding Reservation", rsv_name)
		self.assertEqual(rsv.status, "Released")
		self.assertAlmostEqual(flt(rsv.remaining_reserved), 0.0)
		# Consumed 400 must remain evidenced; audit/decisions preserved.
		self.assertGreaterEqual(
			frappe.db.count("Demand Decision", {"demand": name}),
			decisions_before,
		)
		self.assertEqual(
			frappe.db.count(
				"Planning Consumption",
				{"demand": name, "consumed_amount": 400},
			),
			1,
		)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": code}),
			1,
		)
