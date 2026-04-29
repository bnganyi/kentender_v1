from __future__ import annotations

import frappe

from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.tender_binding_service import bind_std_instance_to_tender
from kentender_procurement.std_engine.services.tender_opening_guard_service import (
	DENIAL_CODE_DOM_REQUIRED,
	DENIAL_CODE_MANUAL_OPENING_BLOCKED,
	check_manual_opening_field_permission,
	create_manual_opening_field,
	validate_opening_can_proceed,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR0904OpeningGuard(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-0904-1", self.instance_code, actor="Administrator")

	def tearDown(self):
		frappe.db.delete("STD Tender Binding", {"tender_code": "TND-0904-1"})
		super().tearDown()

	def test_manual_opening_field_blocked_when_std_v2_enabled(self):
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			perm = check_manual_opening_field_permission("TND-0904-1", actor="Administrator")
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_MANUAL_OPENING_BLOCKED, perm["denial_code"])
			with self.assertRaises(frappe.ValidationError):
				create_manual_opening_field("TND-0904-1", {"label": "Manual open"}, actor="Administrator")
		finally:
			frappe.conf.std_engine_v2_enabled = old

	def test_opening_requires_dom_when_std_v2_enabled(self):
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			# Remove DOM reference to simulate missing DOM.
			frappe.db.set_value("STD Tender Binding", {"tender_code": "TND-0904-1"}, "std_dom_code", None, update_modified=False)
			v = validate_opening_can_proceed("TND-0904-1", actor="Administrator")
			self.assertFalse(v["allowed"])
			self.assertEqual(DENIAL_CODE_DOM_REQUIRED, v["denial_code"])
		finally:
			frappe.conf.std_engine_v2_enabled = old
