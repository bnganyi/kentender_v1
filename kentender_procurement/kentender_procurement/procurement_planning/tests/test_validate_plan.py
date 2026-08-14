# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-007 / PLN-NFR-006 — issue-led validation."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	update_plan_item,
)
from kentender_procurement.procurement_planning.services.validate_plan import (
	effective_validation_status,
	validate_plan,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
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

	def test_ready_then_input_change_is_stale(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Validate stale")
		d = make_approved_demand(title="Validate stale demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		ready = validate_plan(plan=plan["plan"], user=planner)
		self.assertEqual(ready["status"], "Ready")
		changed = update_plan_item(
			plan_item=added["plan_item"],
			user=planner,
			fields={
				"lotting_decision": "Multiple lots",
				"expected_lot_count": 3,
				"lot_basis": "By delivery site",
				"ms_delivery_completion": "2028-04-15",
			},
		)
		self.assertTrue(changed.get("ok"), changed)
		status = effective_validation_status(plan=plan["plan"], version=plan["version"])
		self.assertEqual(status, "Stale")
		rerun = validate_plan(plan=plan["plan"], user=planner)
		self.assertEqual(rerun["status"], "Ready")
		self.assertEqual(
			effective_validation_status(plan=plan["plan"], version=plan["version"]),
			"Ready",
		)
