from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class TestPlanningChg016Layout(unittest.TestCase):
	def test_empty_update_modal_and_api_contract(self) -> None:
		fixture = (ROOT / "public/js/planning_ui_fixtures/empty_update_cancel.js").read_text()
		binder = (ROOT / "public/js/planning_empty_update_dialog.js").read_text()
		builder = (ROOT / "public/js/planning_builder_bind.js").read_text()
		for copy in (
			"Cancel empty Plan update?", "Current Approved Version", "Approved value",
			"Draft Version", "Effective changes", "Keep draft", "Cancel empty update",
		):
			self.assertIn(copy, fixture)
		self.assertIn("get_empty_plan_update_cancellation", binder)
		self.assertIn("cancel_empty_plan_update", binder)
		self.assertNotIn("frappe.confirm", builder)
		self.assertNotIn("cancel_plan_update", builder)

	def test_client_context_does_not_restore_browser_pe_fy(self) -> None:
		client = (ROOT / "public/js/planning_client_utils.js").read_text()
		route_context = client.split("function routeContext()", 1)[1].split("function idempotencyKey", 1)[0]
		self.assertNotIn("kt_state.restore", route_context)
