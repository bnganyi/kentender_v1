# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-007 / DEM-AC-014 — idempotent approve+reserve; fail-closed reserve."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import (
	approve_and_reserve_demand,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_final_approval,
)


class TestDemandApproveReserve(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac007_repeat_approve_does_not_duplicate_reservation(self) -> None:
		"""DIA-AC-007 — repeating approval does not create a duplicate RSV."""
		actors = actor_bundle("dem-ac007")
		name = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC007 idempotent approve",
		)
		code = frappe.db.get_value("Demand", name, "demand_code")
		key = f"ac007-{code}"
		first = approve_and_reserve_demand(
			demand=name, user=actors["paa"], idempotency_key=key
		)
		self.assertEqual(first["demand"]["status"], "Approved")
		self.assertEqual(len(first["reservations"]), 1)
		rsv_after_first = frappe.db.count(
			"Funding Reservation", {"demand_code": code}
		)
		self.assertEqual(rsv_after_first, 1)

		with self.assertRaises(Exception):
			approve_and_reserve_demand(
				demand=name, user=actors["paa"], idempotency_key=key
			)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": code}),
			1,
		)
		self.assertEqual(
			frappe.db.get_value("Demand", name, "status"),
			"Approved",
		)

	def test_ac014_failed_reserve_leaves_unapproved_and_no_partial(self) -> None:
		"""DIA-AC-014 — failed reservation leaves Demand unapproved; no partial RSV."""
		actors = actor_bundle("dem-ac014")
		name = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC014 fail-closed reserve",
		)
		code = frappe.db.get_value("Demand", name, "demand_code")
		before = frappe.db.count("Funding Reservation", {"demand_code": code})

		with patch(
			"kentender_budget.services.budget_check_reserve_contracts.reserve_funding",
			side_effect=frappe.ValidationError("Forced reserve failure"),
		):
			with self.assertRaises(frappe.ValidationError):
				approve_and_reserve_demand(demand=name, user=actors["paa"])

		doc = frappe.get_doc("Demand", name)
		self.assertNotEqual(doc.status, "Approved")
		self.assertEqual(doc.current_stage, "Budget Confirmation")
		self.assertEqual(int(doc.planning_ready or 0), 0)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": code}),
			before,
		)
		allocs = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": name},
			fields=["bo_confirmation_status", "funding_reservation"],
		)
		self.assertTrue(allocs)
		self.assertTrue(
			all((a.bo_confirmation_status or "") == "Pending" for a in allocs)
		)
		self.assertTrue(all(not a.funding_reservation for a in allocs))
