from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.stale_output_service import mark_std_outputs_stale
from kentender_procurement.std_engine.tests.test_std_phase6_generation_engine import _Phase6Fixture


class _Phase7Fixture(_Phase6Fixture):
	def tearDown(self):
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"STD Readiness Run", filters={"object_code": self.instance_code}, fields=["name", "readiness_run_code"]
		):
			frappe.db.delete("STD Readiness Finding", {"readiness_run_code": row["readiness_run_code"]})
			frappe.delete_doc("STD Readiness Run", row["name"], force=True, ignore_permissions=True)
		super().tearDown()


class TestSTDCURSOR0701ReadinessRuleEngine(_Phase7Fixture):
	def test_complete_fixture_passes_readiness(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		res = run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		self.assertEqual("Ready", res["status"])
		self.assertFalse(res["findings"])
		self.assertEqual("Ready", frappe.db.get_value("STD Instance", {"instance_code": self.instance_code}, "readiness_status"))

	def test_missing_boq_blocks(self):
		"""No bills on BOQ → validate_boq_instance fails → readiness Blocked."""
		boq_codes = frappe.get_all("STD BOQ Instance", filters={"instance_code": self.instance_code}, pluck="boq_instance_code")
		for bc in boq_codes:
			for bill in frappe.get_all(
				"STD BOQ Bill Instance", filters={"boq_instance_code": bc}, fields=["name", "bill_instance_code"]
			):
				for it in frappe.get_all(
					"STD BOQ Item Instance", filters={"bill_instance_code": bill["bill_instance_code"]}, pluck="name"
				):
					frappe.delete_doc("STD BOQ Item Instance", it, force=True, ignore_permissions=True)
				frappe.delete_doc("STD BOQ Bill Instance", bill["name"], force=True, ignore_permissions=True)
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		res = run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		self.assertEqual("Blocked", res["status"])
		codes = {f["rule_code"] for f in res["findings"]}
		self.assertIn("R_BOQ_COMPLETE", codes)

	def test_missing_dem_output_blocks(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		dem = frappe.db.get_value("STD Generated Output", {"instance_code": self.instance_code, "output_type": "DEM", "status": "Current"}, "name")
		frappe.delete_doc("STD Generated Output", dem, force=True, ignore_permissions=True)
		res = run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		self.assertEqual("Blocked", res["status"])
		self.assertTrue(any("DEM" in f["rule_code"] for f in res["findings"]))

	def test_manual_readiness_mutation_requires_service_context(self):
		inst = frappe.get_doc("STD Instance", {"instance_code": self.instance_code})
		inst.reload()
		with self.assertRaises(frappe.ValidationError):
			inst.readiness_status = "Ready"
			inst.save(ignore_permissions=True)


class TestSTDCURSOR0702StaleOutputDetection(_Phase7Fixture):
	def test_deadline_change_marks_dom_stale(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		mark_std_outputs_stale(self.instance_code, "tds_submission_deadline", actor="Administrator")
		res = run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		self.assertEqual("Blocked", res["status"])
		self.assertTrue(any("R_OUTPUT_STALE_DOM" in f["rule_code"] for f in res["findings"]))

