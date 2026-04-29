from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.landing import search_std_workbench_objects
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1004SearchFilters(_Phase7Fixture):
	def test_search_returns_known_seed_objects(self):
		res = search_std_workbench_objects(query="PH6", limit=50)
		self.assertTrue(res.get("ok"))
		codes = {str(x.get("code") or "") for x in (res.get("results") or [])}
		self.assertIn(self.version_code, codes)
		self.assertIn(self.profile_code, codes)
		self.assertIn(self.instance_code, codes)

	def test_filters_combine_with_queue_state(self):
		frappe.db.set_value("STD Template Version", {"version_code": self.version_code}, "version_status", "Validation Blocked")
		res = search_std_workbench_objects(
			query=self.version_code,
			queue_id="validation_blocked",
			scope_tab_id="templates",
			filters={"object_type": "Template Version", "template_version_status": "Validation Blocked"},
			limit=50,
		)
		self.assertTrue(res.get("ok"))
		rows = res.get("results") or []
		self.assertTrue(rows)
		for row in rows:
			self.assertEqual("Template Version", row.get("object_type"))
			self.assertEqual("Validation Blocked", row.get("status"))
