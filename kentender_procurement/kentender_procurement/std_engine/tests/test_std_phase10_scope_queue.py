from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.landing import get_std_workbench_kpi_strip


class TestSTDCURSOR1003ScopeQueueContract(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self._old_user = None

	def tearDown(self):
		super().tearDown()

	def test_admin_payload_includes_full_scope_tab_set(self):
		payload = get_std_workbench_kpi_strip()
		self.assertTrue(payload.get("ok"))
		tabs = payload.get("scope_tabs") or []
		self.assertEqual(7, len(tabs))
		self.assertEqual(
			[
				"mywork",
				"templates",
				"active_versions",
				"instances",
				"generation_jobs",
				"addendum_impacts",
				"audit_view",
			],
			[x.get("id") for x in tabs],
		)
		self.assertEqual("full_governance", payload.get("visibility_policy"))
		self.assertIsInstance(payload.get("header_actions"), list)
		self.assertGreaterEqual(len(payload.get("header_actions") or []), 1)
		action_ids = {str((x or {}).get("id") or "") for x in (payload.get("header_actions") or [])}
		self.assertIn("production_safety_report", action_ids)

	def test_admin_payload_includes_all_required_queues(self):
		payload = get_std_workbench_kpi_strip()
		queues = payload.get("queues") or []
		self.assertEqual(17, len(queues))
		ids = {x.get("id") for x in queues}
		for required in (
			"draft_versions",
			"structure_in_progress",
			"validation_blocked",
			"validation_passed",
			"legal_review",
			"policy_review",
			"approved",
			"active_versions",
			"suspended",
			"superseded",
			"draft_instances",
			"instance_blocked",
			"instance_ready",
			"published_locked",
			"generation_failed",
			"addendum_impact",
			"archived",
		):
			self.assertIn(required, ids)
