# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0520 — append-only audit event service."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.audit.event_service import (
	AuditEventService,
)


class TestSecAuditEventService0520(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._created: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for name in self._created:
			if frappe.db.exists("Audit Event", name):
				frappe.delete_doc("Audit Event", name, force=True, ignore_permissions=True)

	def _record(self, name: str) -> None:
		if name:
			self._created.append(name)

	@staticmethod
	def _meta(value: object) -> dict:
		if isinstance(value, dict):
			return value
		if isinstance(value, str) and value.strip():
			try:
				parsed = json.loads(value)
			except Exception:
				return {}
			return parsed if isinstance(parsed, dict) else {}
		return {}

	def test_sec_0520_record_success_denied_failed(self) -> None:
		success = AuditEventService.record_success(
			AuditEventCode.STD_TEMPLATE_VALIDATED,
			{
				"object_type": "STD Template",
				"object_code": "TPL-0520",
				"actor_user_code": "Administrator",
				"risk_level": "Medium",
				"action_code": "VALIDATE_STD_TEMPLATE",
			},
		)
		denied = AuditEventService.record_denied(
			AuditEventCode.PUBLICATION_DENIED,
			"PUBLISH_APPROVAL_REQUIRED",
			{
				"object_type": "TM2 Tender",
				"object_code": "TND-0520",
				"tender_code": "TND-0520",
				"actor_user_code": "Administrator",
				"risk_level": "High",
				"action_code": "PUBLISH_TENDER",
			},
		)
		failed = AuditEventService.record_failed(
			AuditEventCode.DERIVED_MODEL_GENERATION_FAILED,
			"DERIVED_OUTPUT_GENERATION_FAILED",
			{
				"object_type": "Tender STD Generated Output",
				"object_code": "OUT-0520",
				"actor_user_code": "Administrator",
				"risk_level": "Medium",
			},
		)
		for n in (success, denied, failed):
			self._record(n)
			self.assertTrue(frappe.db.exists("Audit Event", n))

		denied_meta = self._meta(frappe.db.get_value("Audit Event", denied, "metadata"))
		self.assertEqual((denied_meta or {}).get("result"), "Denied")
		self.assertEqual((denied_meta or {}).get("denial_code"), "PUBLISH_APPROVAL_REQUIRED")

	def test_sec_0520_query_by_object(self) -> None:
		n1 = AuditEventService.record_success(
			AuditEventCode.STD_PARAMETER_CHANGED,
			{
				"object_type": "Tender STD Instance",
				"object_code": "INST-0520-OBJ",
				"actor_user_code": "Administrator",
				"risk_level": "Low",
			},
		)
		self._record(n1)
		rows = AuditEventService.get_audit_events_for_object(
			"Tender STD Instance",
			"INST-0520-OBJ",
			{"event_type": AuditEventCode.STD_PARAMETER_CHANGED},
		)
		self.assertGreaterEqual(len(rows), 1)
		self.assertEqual(rows[0]["document_type"], "Tender STD Instance")
		self.assertEqual(rows[0]["document_name"], "INST-0520-OBJ")

	def test_sec_0520_query_by_tender(self) -> None:
		n1 = AuditEventService.record_denied(
			AuditEventCode.PUBLICATION_DENIED,
			"PUBLISH_PERMISSION_DENIED",
			{
				"object_type": "TM2 Tender",
				"object_code": "TND-0520-Q",
				"tender_code": "TND-0520-Q",
				"actor_user_code": "Administrator",
				"risk_level": "High",
			},
		)
		self._record(n1)
		rows = AuditEventService.get_audit_events_for_tender("TND-0520-Q", {"result": "Denied"})
		self.assertGreaterEqual(len(rows), 1)
		self.assertEqual((rows[0]["metadata"] or {}).get("tender_code"), "TND-0520-Q")

	def test_sec_0520_append_only_enforced(self) -> None:
		with self.assertRaises(frappe.PermissionError):
			AuditEventService.assert_append_only_operation("delete")
