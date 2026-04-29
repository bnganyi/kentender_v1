from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.instance_workbench import (
	get_std_instance_addendum_impact_panel,
	get_std_instance_audit_trail,
	get_std_instance_boq_workbench_panel,
	get_std_instance_outputs_preview,
	get_std_instance_parameter_catalogue,
	get_std_instance_readiness_panel,
	get_std_instance_works_requirements_panel,
	run_std_instance_readiness_now,
)
from kentender_procurement.std_engine.api.tender_std_panel import get_tender_std_panel_data
from kentender_procurement.std_engine.services.instance_parameter_catalogue_service import (
	build_std_instance_parameter_catalogue,
)
from kentender_procurement.std_engine.services.tender_binding_service import bind_std_instance_to_tender
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1102Through1107InstancePanels(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_parameter_catalogue_ok(self):
		out = build_std_instance_parameter_catalogue(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("instance_code"), self.instance_code)
		self.assertIn("groups", out)
		self.assertIn("read_only", out)

	def test_whitelist_parameter_catalogue(self):
		out = get_std_instance_parameter_catalogue(self.instance_code)
		self.assertTrue(out.get("ok"))

	def test_works_panel_ok(self):
		out = get_std_instance_works_requirements_panel(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("components", out)
		self.assertIn("attachment_action_labels", out)

	def test_boq_panel_ok(self):
		out = get_std_instance_boq_workbench_panel(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("validation", out)

	def test_outputs_preview_ok(self):
		out = get_std_instance_outputs_preview(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("outputs_by_type", out)
		self.assertIn("warnings", out)

	def test_readiness_panel_ok(self):
		out = get_std_instance_readiness_panel(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("manual_ready_forbidden"))

	def test_run_readiness_whitelist(self):
		out = run_std_instance_readiness_now(self.instance_code)
		self.assertIn("status", out)

	def test_addendum_panel_ok(self):
		out = get_std_instance_addendum_impact_panel(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("impact_analyses", out)

	def test_audit_trail_ok(self):
		out = get_std_instance_audit_trail(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("events", out)


class TestSTDCURSOR1108TenderStdPanel(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_tender_panel_with_binding(self):
		inst = frappe.get_doc("STD Instance", {"instance_code": self.instance_code})
		tc = inst.tender_code
		bind_std_instance_to_tender(tc, self.instance_code, actor="Administrator")
		out = get_tender_std_panel_data(tc)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("tender_code"), tc)
		self.assertTrue(out.get("hide_manual_attachment_ui"))
		self.assertIsNotNone(out.get("generated_outputs"))
