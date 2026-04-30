from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.production_safety import get_std_production_safety_report
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.production_safety_service import (
	build_std_production_safety_report,
)
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.tender_binding_service import bind_std_instance_to_tender
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1302ProductionSafetyChecks(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._prev_flag = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf["std_engine_v2_enabled"] = 1
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender(self.tender_code, self.instance_code, actor="Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		if self._prev_flag is None:
			frappe.conf.pop("std_engine_v2_enabled", None)
		else:
			frappe.conf["std_engine_v2_enabled"] = self._prev_flag
		super().tearDown()

	def test_report_passes_all_checks_with_explicit_smoke_signal(self):
		out = build_std_production_safety_report(smoke_tests_passed=True, actor="Administrator")
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("overall_pass"))
		checks = {row["check_key"]: row for row in out.get("checks") or []}
		self.assertTrue(checks["seed_package_loaded"]["passed"])
		self.assertTrue(checks["smoke_tests_pass"]["passed"])
		self.assertTrue(checks["feature_flag_default_reviewed"]["passed"])
		self.assertTrue(checks["active_doc1_template_exists"]["passed"])
		self.assertTrue(checks["no_legacy_upload_as_source_when_v2"]["passed"])
		self.assertTrue(checks["manual_downstream_rules_disabled"]["passed"])
		self.assertTrue(checks["audit_append_only_verified"]["passed"])

	def test_report_fails_when_legacy_binding_signal_exists(self):
		binding_name = frappe.db.get_value("STD Tender Binding", {"tender_code": self.tender_code}, "name")
		self.assertTrue(binding_name)
		frappe.db.set_value("STD Tender Binding", binding_name, "std_outputs_current", 0)
		frappe.db.set_value("STD Tender Binding", binding_name, "std_bundle_code", "")
		out = build_std_production_safety_report(smoke_tests_passed=True, actor="Administrator")
		self.assertTrue(out.get("ok"))
		self.assertFalse(out.get("overall_pass"))
		checks = {row["check_key"]: row for row in out.get("checks") or []}
		self.assertFalse(checks["no_legacy_upload_as_source_when_v2"]["passed"])

	def test_api_requires_auth_and_returns_report(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_production_safety_report, True)
		finally:
			frappe.set_user("Administrator")
		out = get_std_production_safety_report(True)
		self.assertTrue(out.get("ok"))
		self.assertIn("checks", out)
