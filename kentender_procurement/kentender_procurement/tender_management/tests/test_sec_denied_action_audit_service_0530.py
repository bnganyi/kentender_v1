# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0530 — denied action audit service."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.audit.denied_action import (
	DeniedActionAuditService,
)


class TestSecDeniedActionAuditService0530(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._created: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for name in self._created:
			if name and frappe.db.exists("Audit Event", name):
				frappe.delete_doc("Audit Event", name, force=True, ignore_permissions=True)

	@staticmethod
	def _meta(value: object) -> dict:
		if isinstance(value, dict):
			return value
		if isinstance(value, str) and value.strip():
			try:
				out = json.loads(value)
			except Exception:
				return {}
			return out if isinstance(out, dict) else {}
		return {}

	def _assert_core_fields(self, name: str, *, actor: str, action_code: str, object_type: str, object_code: str, denial_code: str) -> None:
		row = frappe.db.get_value(
			"Audit Event",
			name,
			["event_type", "document_type", "document_name", "performed_by", "metadata"],
			as_dict=True,
		)
		self.assertTrue(row)
		self.assertEqual(row.get("document_type"), object_type)
		self.assertEqual(row.get("document_name"), object_code)
		meta = self._meta(row.get("metadata"))
		self.assertEqual(meta.get("actor_user_code"), actor)
		self.assertEqual(meta.get("action_code"), action_code)
		self.assertEqual(meta.get("object_type"), object_type)
		self.assertEqual(meta.get("object_code"), object_code)
		self.assertEqual(meta.get("denial_code"), denial_code)
		self.assertEqual(meta.get("result"), "Denied")

	def test_sec_0530_records_high_and_critical_denials(self) -> None:
		cases = [
			("std-admin@example.com", "CREATE_STD_INSTANCE_FROM_TENDER", "Tender STD Instance", "INST-0530-1", "STD_AUTH_PERMISSION_DENIED", "High"),
			("proc@example.com", "CONFIGURE_STD_TEMPLATE_MAPPINGS", "STD Template", "TPL-0530-2", "STD_AUTH_PERMISSION_DENIED", "High"),
			("assistant@example.com", "PUBLISH_TENDER", "TM2 Tender", "TND-0530-3", "PUBLISH_PERMISSION_DENIED", "Critical"),
			("approver@example.com", "EDIT_WORKS_BOQ_DURING_APPROVAL", "TM2 Tender", "TND-0530-4", "STD_AUTH_PERMISSION_DENIED", "High"),
			("opening@example.com", "PERFORM_BOQ_ARITHMETIC_CORRECTION", "TM2 Tender", "TND-0530-5", "BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION", "High"),
			("eval@example.com", "ADD_MANUAL_EVALUATION_CRITERIA", "TM2 Tender", "TND-0530-6", "MANUAL_EVALUATION_CRITERIA_DENIED", "High"),
			("contract@example.com", "SILENT_DCM_CONTRACT_OVERRIDE", "TM2 Tender", "TND-0530-7", "STD_AUTH_DCM_CONTRACT_BINDING_VIOLATION", "Critical"),
			("auditor@example.com", "EDIT_STD_INSTANCE_PARAMETERS", "Tender STD Instance", "INST-0530-8", "STD_AUTH_PERMISSION_DENIED", "High"),
			("user@example.com", "EDIT_STD_INSTANCE_PARAMETERS", "Tender STD Instance", "INST-0530-9", "POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED", "Critical"),
		]
		for actor, action_code, object_type, object_code, denial_code, risk_level in cases:
			with self.subTest(action=action_code):
				name = DeniedActionAuditService.record_denied_action(
					actor,
					action_code,
					object_type,
					object_code,
					{
						"denial_code": denial_code,
						"risk_level": risk_level,
						"message": "Denied by policy.",
						"required_permission": "PERM_X",
					},
					{"tender_code": "TND-0530"},
				)
				self.assertTrue(name)
				assert name is not None
				self._created.append(name)
				self._assert_core_fields(
					name,
					actor=actor,
					action_code=action_code,
					object_type=object_type,
					object_code=object_code,
					denial_code=denial_code,
				)

	def test_sec_0530_low_risk_without_audit_hint_skips(self) -> None:
		name = DeniedActionAuditService.record_denied_action(
			"user-low@example.com",
			"CONSUME_DOM",
			"Tender STD Generated Output",
			"OUT-0530",
			{"denial_code": "OUTPUT_STALE", "risk_level": "Low", "message": "Not current."},
			{},
		)
		self.assertIsNone(name)

	def test_sec_0530_low_risk_with_audit_hint_records(self) -> None:
		name = DeniedActionAuditService.record_denied_action(
			"user-low-audit@example.com",
			"CONSUME_DOM",
			"Tender STD Generated Output",
			"OUT-0530-2",
			{
				"denial_code": "OUTPUT_STALE",
				"risk_level": "Low",
				"audit_on_attempt": True,
				"message": "Not current.",
			},
			{"source": "test"},
		)
		self.assertTrue(name)
		assert name is not None
		self._created.append(name)
		meta = self._meta(frappe.db.get_value("Audit Event", name, "metadata"))
		self.assertEqual(meta.get("denial_code"), "OUTPUT_STALE")

	def test_sec_0530_pack_alias(self) -> None:
		name = DeniedActionAuditService.recordDeniedAction(
			"alias@example.com",
			"PUBLISH_TENDER",
			"TM2 Tender",
			"TND-0530-ALIAS",
			{"denial_code": "PUBLISH_PERMISSION_DENIED", "risk_level": "Critical"},
			{},
		)
		self.assertTrue(name)
		assert name is not None
		self._created.append(name)
