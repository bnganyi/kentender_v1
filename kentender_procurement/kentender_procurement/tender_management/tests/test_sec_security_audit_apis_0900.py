from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.api import (
	SEC_API_INTERNAL_ERROR,
	SEC_API_OBJECT_TYPE_REQUIRED,
	SEC_API_PAYLOAD_INVALID,
	SEC_API_TENDER_CODE_REQUIRED,
	sec_api_audit_events,
	sec_api_audit_tender_events,
	sec_api_evidence_export_availability,
)
from kentender_procurement.tender_management.security.evidence.export_authorization import (
	EvidenceExportAuthorizationOutcome,
)


class TestSecSecurityAuditApis0900(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")

	def test_sec_0900_audit_events_object_success(self) -> None:
		with patch(
			"kentender_procurement.tender_management.security.api.AuditEventService.get_audit_events_for_object",
			return_value=[{"name": "AE-1", "event_type": "E1"}],
		):
			res = sec_api_audit_events("TM2 Tender", "TND-0900-1")
		self.assertTrue(res["success"])
		self.assertEqual(res["actor_user_code"], "Administrator")
		self.assertEqual(res["object_type"], "TM2 Tender")
		self.assertEqual(res["object_code"], "TND-0900-1")
		self.assertEqual(len(res["events"]), 1)

	def test_sec_0900_audit_events_object_validation_error_shape(self) -> None:
		res = sec_api_audit_events("", "TND-0900-2")
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_OBJECT_TYPE_REQUIRED)

	def test_sec_0900_audit_tender_events_success(self) -> None:
		with patch(
			"kentender_procurement.tender_management.security.api.AuditEventService.get_audit_events_for_tender",
			return_value=[{"name": "AE-2", "event_type": "E2"}],
		):
			res = sec_api_audit_tender_events("TND-0900-3", filters='{"result":"Denied"}')
		self.assertTrue(res["success"])
		self.assertEqual(res["tender_code"], "TND-0900-3")
		self.assertEqual(len(res["events"]), 1)

	def test_sec_0900_export_availability_uses_session_actor(self) -> None:
		with patch(
			"kentender_procurement.tender_management.security.api.EvidenceExportAuthorizationService.check_can_export_evidence",
			return_value=EvidenceExportAuthorizationOutcome(True, None, "ok", "High"),
		) as chk:
			res = sec_api_evidence_export_availability(
				"TND-0900-4",
				context={"security_role_codes": ["ROLE_AUDITOR"]},
				actor="ignored.user@example.com",
			)
		self.assertTrue(res["success"])
		self.assertEqual(res["actor_user_code"], "Administrator")
		chk.assert_called_once()
		self.assertEqual(chk.call_args[0][0], "Administrator")

	def test_sec_0900_export_availability_denied_shape(self) -> None:
		with patch(
			"kentender_procurement.tender_management.security.api.EvidenceExportAuthorizationService.check_can_export_evidence",
			return_value=EvidenceExportAuthorizationOutcome(False, "AUDIT_EXPORT_DENIED", "denied", "High"),
		):
			res = sec_api_evidence_export_availability("TND-0900-5", context={})
		self.assertTrue(res["success"])
		self.assertFalse(res["allowed"])
		self.assertEqual(res["denial_code"], "AUDIT_EXPORT_DENIED")
		self.assertEqual(res["message"], "denied")

	def test_sec_0900_internal_error_masked(self) -> None:
		with patch(
			"kentender_procurement.tender_management.security.api.AuditEventService.get_audit_events_for_tender",
			side_effect=RuntimeError("boom"),
		):
			res = sec_api_audit_tender_events("TND-0900-ERR")
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_INTERNAL_ERROR)
		self.assertEqual(res["message"], "Unexpected server error.")

	def test_sec_0900_filters_invalid_json_error(self) -> None:
		res = sec_api_audit_tender_events("TND-0900-6", filters="{bad json")
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_PAYLOAD_INVALID)

	def test_sec_0900_tender_code_required_error(self) -> None:
		res = sec_api_audit_tender_events("")
		self.assertFalse(res["success"])
		self.assertEqual(res["error_code"], SEC_API_TENDER_CODE_REQUIRED)
