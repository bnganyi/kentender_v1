from __future__ import annotations

import frappe

from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.tender_binding_service import bind_std_instance_to_tender
from kentender_procurement.std_engine.services.tender_submission_guard_service import (
	DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED,
	check_manual_submission_requirement_permission,
	create_manual_submission_requirement,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR0902SubmissionGuard(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-0902-1", self.instance_code, actor="Administrator")

	def tearDown(self):
		frappe.db.delete("STD Tender Binding", {"tender_code": "TND-0902-1"})
		super().tearDown()

	def test_manual_checklist_creation_blocked_when_std_v2_enabled(self):
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			perm = check_manual_submission_requirement_permission("TND-0902-1", actor="Administrator")
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED, perm["denial_code"])
			with self.assertRaises(frappe.ValidationError):
				create_manual_submission_requirement("TND-0902-1", {"label": "Manual row"}, actor="Administrator")
			self.assertTrue(
				frappe.db.exists(
					"STD Audit Event",
					{
						"event_type": "PERMISSION_DENIED",
						"object_code": "TND-0902-1",
						"denial_code": DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED,
					},
				)
			)
		finally:
			frappe.conf.std_engine_v2_enabled = old

	def test_api_allows_manual_when_flag_disabled(self):
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 0
		try:
			perm = check_manual_submission_requirement_permission("TND-0902-1", actor="Administrator")
			self.assertTrue(perm["allowed"])
			resp = create_manual_submission_requirement("TND-0902-1", {"label": "Manual row"}, actor="Administrator")
			self.assertTrue(resp["created"])
		finally:
			frappe.conf.std_engine_v2_enabled = old
