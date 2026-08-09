# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-001 — submit without Strategy / Budget / procurement method."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import submit_demand
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests._ac_helpers import create_draft, ensure_user


class TestDemandSubmit(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac001_submit_without_strategy_budget_or_method(self) -> None:
		"""DIA-AC-001 — Requester can submit with no Strategy/Budget/method."""
		req = ensure_user("dem-ac001-req@example.com", [ROLE_REQUESTER])
		name = create_draft(req, estimate=1000, title="AC001 submit without specialist data")
		self.assertEqual(
			frappe.db.count("Demand Strategy Reference", {"demand": name}),
			0,
		)
		self.assertEqual(
			frappe.db.count("Demand Funding Allocation", {"demand": name}),
			0,
		)
		doc = frappe.get_doc("Demand", name)
		self.assertFalse(doc.get("procurement_method"))
		self.assertFalse(doc.confirmed_estimate)

		submitted = submit_demand(demand=name, user=req)
		self.assertEqual(submitted["demand"]["status"], "In Review")
		self.assertEqual(submitted["demand"]["current_stage"], "Business Review")
		self.assertNotIn("procurement_method", submitted["demand"])
		self.assertEqual(
			frappe.db.count("Demand Strategy Reference", {"demand": name}),
			0,
		)
		self.assertEqual(
			frappe.db.count("Demand Funding Allocation", {"demand": name}),
			0,
		)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": submitted["demand"]["demand_code"]}),
			0,
		)
