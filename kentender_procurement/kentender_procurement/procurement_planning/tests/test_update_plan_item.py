# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-005 / PLN-AC-004 / PLN-AC-012 / PLN-AC-016."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	update_plan_item,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestUpdatePlanItem(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _item(self):
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Update item plan")
		d = make_approved_demand(title="Editor demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		return planner, added["plan_item"]

	def test_saves_method_schedule_and_lotting(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"requirement_description": "Upgrade national DHI stack",
				"procurement_category": "ICT",
				"procurement_method": "Open tender",
				"arrangement": "Single year",
				"lotting_decision": "Multiple lots",
				"expected_lot_count": 2,
				"lot_basis": "Split by region for delivery capacity",
				"ms_invitation_published": "2027-09-15",
				"ms_tender_opening": "2027-10-20",
				"ms_evaluation_completed": "2027-11-15",
				"ms_award_approval": "2027-12-15",
				"ms_contract_signature": "2028-01-15",
				"ms_delivery_completion": "2028-03-31",
				"statutory_treatment": "Open competition",
			},
		)
		self.assertTrue(result["ok"], result)

	def test_alternative_method_requires_grounds(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"procurement_method": "Direct procurement"},
		)
		self.assertFalse(result["ok"])
		self.assertIn("method_override_grounds", result["errors"])

	def test_multi_year_requires_justification_and_schedule(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"arrangement": "Multi-year"},
		)
		self.assertFalse(result["ok"])
		self.assertIn("multi_year_justification", result["errors"])
		self.assertIn("annual_funding_schedule", result["errors"])
