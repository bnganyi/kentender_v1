# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-019 / DEM-AC-021 — material change invalidates BO; allocs = estimate."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import (
	apply_material_funding_change,
	approve_and_reserve_demand,
	confirm_demand_funding,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_final_approval,
	budget_line,
)


class TestDemandFunding(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac021_allocations_must_equal_estimate_before_approve(self) -> None:
		"""DIA-AC-021 — allocations must equal confirmed estimate before approval."""
		actors = actor_bundle("dem-ac021")
		name = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC021 allocation equality",
		)
		# Force mismatch after BO confirm (bypass confirm gate).
		alloc = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": name, "bo_confirmation_status": "Confirmed"},
			"name",
		)
		frappe.db.set_value(
			"Demand Funding Allocation",
			alloc,
			"allocation_amount",
			900,
		)
		with self.assertRaises(Exception) as ctx:
			approve_and_reserve_demand(demand=name, user=actors["paa"])
		self.assertIn("equal", str(ctx.exception).lower())
		self.assertEqual(frappe.db.get_value("Demand", name, "status"), "In Review")

		# Confirm path also blocks mismatch (rebuild at Budget Confirmation).
		name2 = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC021 confirm mismatch",
		)
		# Return-like: reset to Budget Confirmation Pending with wrong amount.
		frappe.db.set_value(
			"Demand",
			name2,
			{"current_stage": "Budget Confirmation", "status": "In Review"},
		)
		for row in frappe.get_all(
			"Demand Funding Allocation", filters={"demand": name2}, pluck="name"
		):
			frappe.delete_doc(
				"Demand Funding Allocation", row, ignore_permissions=True, force=1
			)
		line = budget_line()
		with self.assertRaises(Exception):
			confirm_demand_funding(
				demand=name2,
				allocations=[
					{
						"budget_line": line,
						"allocation_amount": 900,
						"matching_source": "Budget Officer",
					}
				],
				user=actors["bo"],
			)

	def test_ac019_material_change_invalidates_bo_signoff(self) -> None:
		"""DIA-AC-019 — material change after BO sign-off → Budget Confirmation."""
		actors = actor_bundle("dem-ac019")
		name = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC019 material change",
		)
		self.assertEqual(
			frappe.db.get_value("Demand", name, "current_stage"),
			"Final Approval",
		)
		result = apply_material_funding_change(
			demand=name,
			confirmed_estimate=1200,
			user=actors["paa"],
		)
		self.assertEqual(result["demand"]["current_stage"], "Budget Confirmation")
		self.assertEqual(result["demand"]["status"], "In Review")
		self.assertEqual(float(result["demand"]["confirmed_estimate"]), 1200.0)
		allocs = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": name},
			fields=["bo_confirmation_status", "bo_confirmed_by"],
		)
		self.assertTrue(allocs)
		self.assertTrue(
			all((a.bo_confirmation_status or "") == "Pending" for a in allocs)
		)
		self.assertTrue(all(not a.bo_confirmed_by for a in allocs))
		self.assertTrue(
			frappe.db.exists(
				"Demand Decision",
				{"demand": name, "decision": "Material change"},
			)
		)
