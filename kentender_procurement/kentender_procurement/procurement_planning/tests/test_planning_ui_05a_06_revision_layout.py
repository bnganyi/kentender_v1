from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public" / "js"


class TestPlanningUI05A06RevisionLayout(unittest.TestCase):
	def test_removal_dialog_is_authoritative_and_accessible(self):
		fixture = (PUBLIC / "planning_ui_fixtures" / "remove_plan_item_dialog.js").read_text()
		binder = (PUBLIC / "planning_removal_dialog.js").read_text()
		for copy in ("Reason for removal", "Keep item", "Included Demand sources"):
			self.assertIn(copy, fixture)
		self.assertIn('role="dialog"', fixture)
		self.assertIn('aria-modal="true"', fixture)
		self.assertIn("get_plan_item_removal", binder)
		self.assertIn("expected_version_token", binder)
		self.assertIn("idempotency_key", binder)
		self.assertIn('event.key === "Escape"', binder)
		self.assertNotIn("source checkbox", fixture.lower())

	def test_editor_matches_approved_focused_contract(self):
		fixture = (PUBLIC / "planning_ui_fixtures" / "plan_item_editor.js").read_text()
		binder = (PUBLIC / "planning_item_editor_bind.js").read_text()
		for copy in (
			"Approved requirement", "Procurement approach", "Indicative lotting",
			"Notification of award", "Planned time to contract signature",
			"Back to plan update", "Save draft", "Request Finance confirmation",
		):
			self.assertIn(copy, fixture)
		self.assertIn("max-w-4xl", fixture)
		self.assertIn("ms_notification_of_award", fixture)
		service = (ROOT / "procurement_planning" / "services" / "get_plan_item_editor.py").read_text()
		self.assertIn("Training and professional development services", service)
		self.assertNotIn("Governing regime", fixture)
		self.assertNotIn("Restricted tender", fixture)
		self.assertNotIn("Breadcrumb", fixture)
		self.assertNotIn("add-another-demand", fixture)

	def test_split_binders_are_loaded_after_shared_client(self):
		hooks = (ROOT / "hooks.py").read_text()
		self.assertLess(hooks.index("planning_client_utils.js"), hooks.index("planning_removal_dialog.js"))
		self.assertLess(hooks.index("planning_client_utils.js"), hooks.index("planning_item_editor_bind.js"))


if __name__ == "__main__":
	unittest.main()
