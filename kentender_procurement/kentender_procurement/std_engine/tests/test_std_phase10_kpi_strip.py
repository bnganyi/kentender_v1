from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.landing import get_std_workbench_kpi_strip
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1002KpiStrip(_Phase7Fixture):
	def tearDown(self):
		for name in frappe.get_all(
			"STD Generation Job", filters={"generation_job_code": ("like", "GJOB-1002-%")}, pluck="name"
		):
			frappe.delete_doc("STD Generation Job", name, force=True, ignore_permissions=True)
		for name in frappe.get_all(
			"STD Addendum Impact Analysis", filters={"impact_analysis_code": ("like", "IMPACT-1002-%")}, pluck="name"
		):
			frappe.delete_doc("STD Addendum Impact Analysis", name, force=True, ignore_permissions=True)
		super().tearDown()

	def _kpi_value_map(self) -> dict[str, int]:
		payload = get_std_workbench_kpi_strip()
		self.assertTrue(payload.get("ok"))
		return {row["id"]: int(row.get("value") or 0) for row in payload.get("kpis") or []}

	def test_payload_has_eight_expected_kpis(self):
		payload = get_std_workbench_kpi_strip()
		self.assertTrue(payload.get("ok"))
		rows = payload.get("kpis") or []
		self.assertEqual(8, len(rows))
		self.assertEqual(
			[
				"draft_versions",
				"validation_blocked",
				"legal_review_pending",
				"policy_review_pending",
				"active_versions",
				"instances_blocked",
				"generation_failures",
				"addendum_impact_pending",
			],
			[row.get("id") for row in rows],
		)
		for row in rows:
			self.assertIsInstance(row.get("value"), int)
			self.assertTrue(str(row.get("testid") or "").startswith("std-kpi-"))

	def test_generation_failures_and_addendum_pending_counts_increase(self):
		before = self._kpi_value_map()
		frappe.get_doc(
			{
				"doctype": "STD Generation Job",
				"generation_job_code": "GJOB-1002-FAILED-1",
				"instance_code": self.instance_code,
				"job_type": "All",
				"trigger_type": "Manual",
				"status": "Failed",
				"error_message": "Simulated failure",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "STD Addendum Impact Analysis",
				"impact_analysis_code": "IMPACT-1002-PENDING-1",
				"instance_code": self.instance_code,
				"addendum_code": "ADD-1002-1",
				"status": "Analysis Pending",
				"requires_regeneration": 1,
			}
		).insert(ignore_permissions=True)
		after = self._kpi_value_map()
		self.assertEqual(before["generation_failures"] + 1, after["generation_failures"])
		self.assertEqual(before["addendum_impact_pending"] + 1, after["addendum_impact_pending"])
