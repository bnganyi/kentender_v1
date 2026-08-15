import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.get_plan_item_editor import get_plan_item_editor
from kentender_procurement.procurement_planning.services.remove_plan_item import get_plan_item_removal, remove_plan_item_from_plan
from kentender_procurement.procurement_planning.services.update_plan_item import update_plan_item
from kentender_procurement.procurement_planning.tests._gate01_helpers import add_demand_to_plan, complete_plan_item_for_signoff, create_plan_as_planner, ensure_planner_user, ensure_scope, make_approved_demand


class TestPlanningUI05A06RevisionServices(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _context(self, title: str):
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title=title)
		demand = make_approved_demand(title=f"{title} Demand", item_amount=8_000_000)
		added = add_demand_to_plan(plan=plan["plan"], demand=demand["demand"], user=planner)
		return planner, plan, demand, added["plan_item"]

	def _token(self, plan: str):
		draft = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
		return draft, frappe.db.get_value("Procurement Plan Version", draft, "concurrency_token")

	def test_editor_projects_exact_admitted_contract(self):
		planner, plan, _demand, item = self._context("UI06 projection")
		result = get_plan_item_editor(plan_item=item, user=planner)
		self.assertEqual(result["surface"], "PLN-UI-06")
		self.assertEqual(result["method_options"], ["Open tender"])
		self.assertIn("Training and professional development services", result["category_options"])
		self.assertEqual(len(result["source_rows"]), 1)
		self.assertEqual(result["back_route"], f"/app/procurement-plan-builder?plan={plan['plan']}")
		self.assertIn("ms_notification_of_award", result["fields"])

	def test_editor_rejects_unknown_and_unconfigured_method(self):
		planner, plan, _demand, item = self._context("UI06 strict mutation")
		_draft, token = self._token(plan["plan"])
		method = update_plan_item(plan_item=item, user=planner, fields={"procurement_method": "Restricted tender"}, expected_version_token=token, idempotency_key="UI06-ALT")
		self.assertEqual(method["error_code"], "PROCUREMENT_METHOD_NOT_CONFIGURED")
		unknown = update_plan_item(plan_item=item, user=planner, fields={"confirmed_estimate": 1}, expected_version_token=token, idempotency_key="UI06-LOCKED")
		self.assertEqual(unknown["error_code"], "PLN_ITEM_FIELDS_NOT_PERMITTED")

	def test_save_rotates_token_and_replay_is_idempotent(self):
		planner, plan, _demand, item = self._context("UI06 save")
		_draft, token = self._token(plan["plan"])
		args = dict(plan_item=item, user=planner, fields={"requirement_description": "A governed annual-plan description", "procurement_method": "Open tender"}, expected_version_token=token, idempotency_key="UI06-SAVE")
		first = update_plan_item(**args)
		self.assertTrue(first["ok"])
		self.assertNotEqual(first["concurrency_token"], token)
		second = update_plan_item(**args)
		self.assertTrue(second["idempotent"])

	def test_removal_projection_is_mutation_free_and_confirm_returns_empty_builder(self):
		planner, plan, _demand, item = self._context("UI05A removal")
		draft, token = self._token(plan["plan"])
		before = frappe.db.get_value("Procurement Plan Item", item, "baseline_state")
		projection = get_plan_item_removal(plan=plan["plan"], plan_item=item, user=planner)
		self.assertTrue(projection["can_remove"])
		self.assertEqual(frappe.db.get_value("Procurement Plan Item", item, "baseline_state"), before)
		result = remove_plan_item_from_plan(plan=plan["plan"], plan_item=item, draft_version=draft, expected_version_token=token, reason="No longer required in this draft", idempotency_key="UI05A-REMOVE", user=planner)
		self.assertTrue(result["ok"])
		self.assertEqual(result["state_id"], "PLN-UI-03")
		replay = remove_plan_item_from_plan(plan=plan["plan"], plan_item=item, draft_version=draft, expected_version_token=token, reason="No longer required in this draft", idempotency_key="UI05A-REMOVE", user=planner)
		self.assertTrue(replay["idempotent"])

	def test_notification_of_award_is_part_of_finance_completeness(self):
		planner, plan, _demand, item = self._context("UI06 Finance")
		complete_plan_item_for_signoff(plan_item=item, user=planner)
		draft, token = self._token(plan["plan"])
		result = update_plan_item(plan_item=item, user=planner, fields={}, request_finance=True, expected_version_token=token, idempotency_key="UI06-FINANCE")
		self.assertTrue(result["ok"], result)
		self.assertTrue(result["complete"], result)
		self.assertEqual(result["finance_status"], "Awaiting confirmation")
