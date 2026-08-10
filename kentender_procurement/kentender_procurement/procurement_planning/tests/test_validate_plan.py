# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-007 / PLN-NFR-006 — issue-led validation."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestValidatePlan(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_incomplete_item_needs_attention_and_user_cannot_set_ready(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Validate plan")
		d = make_approved_demand(title="Validate demand")
		add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		payload = validate_plan(plan=plan["plan"], user=planner)
		self.assertTrue(payload["ok"])
		self.assertFalse(payload["user_may_set_ready"])
		self.assertIn(payload["status"], ("Needs attention", "Not run", "Blocked"))
		if payload["issues"]:
			issue = payload["issues"][0]
			self.assertIn("reason", issue)
			self.assertIn("corrective_action", issue)
			self.assertIn("owner", issue)
