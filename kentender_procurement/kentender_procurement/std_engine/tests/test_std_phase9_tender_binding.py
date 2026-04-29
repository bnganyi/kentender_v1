from __future__ import annotations

import frappe

from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.tender_binding_service import (
	bind_std_instance_to_tender,
	get_tender_std_binding,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR0901TenderBinding(_Phase7Fixture):
	def tearDown(self):
		for name in frappe.get_all("STD Tender Binding", filters={"tender_code": ("like", "TND-0901-%")}, pluck="name"):
			frappe.delete_doc("STD Tender Binding", name, force=True, ignore_permissions=True)
		super().tearDown()

	def test_bind_tender_to_std_instance_with_output_refs(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")

		res = bind_std_instance_to_tender("TND-0901-1", self.instance_code, actor="Administrator")
		self.assertEqual(self.instance_code, res["std_instance_code"])
		self.assertEqual("Ready", res["std_readiness_status"])
		self.assertTrue(res["std_bundle_code"])
		self.assertTrue(res["std_dsm_code"])
		self.assertTrue(res["std_dom_code"])
		self.assertTrue(res["std_dem_code"])
		self.assertTrue(res["std_dcm_code"])
		self.assertEqual(1, res["std_outputs_current"])

	def test_binding_query_returns_references_not_editable_copies(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-0901-2", self.instance_code, actor="Administrator")
		got = get_tender_std_binding("TND-0901-2")["binding"]
		self.assertEqual(self.instance_code, got["std_instance_code"])
		self.assertTrue(got["std_bundle_code"])
