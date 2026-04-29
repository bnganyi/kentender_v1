from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.landing import search_std_workbench_objects
from kentender_procurement.std_engine.services.addendum_impact_service import analyze_std_addendum_impact
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1005ObjectListPanel(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		analyze_std_addendum_impact(
			self.instance_code,
			"ADD-1005-1",
			[{"change_type": "BOQ_QUANTITY_CHANGE", "details": {"item_code": "IT-1"}}],
			actor="Administrator",
		)

	def test_search_rows_include_required_business_object_types(self):
		res = search_std_workbench_objects(query="", limit=200)
		self.assertTrue(res.get("ok"))
		types = {str(r.get("object_type") or "") for r in (res.get("results") or [])}
		for required in (
			"Template Family",
			"Template Version",
			"Applicability Profile",
			"STD Instance",
			"Generated Output",
			"Generation Job",
			"Addendum Impact",
			"Readiness Run",
		):
			self.assertIn(required, types)

	def test_rows_expose_business_codes_and_titles(self):
		res = search_std_workbench_objects(query=self.instance_code, limit=80)
		rows = res.get("results") or []
		self.assertTrue(rows)
		for row in rows:
			self.assertTrue(str(row.get("code") or "").strip())
			self.assertTrue(str(row.get("title") or "").strip())
