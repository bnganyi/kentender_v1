# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0500 — common audit metadata schema."""

from __future__ import annotations

from datetime import datetime

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.audit.metadata import (
	AuditEventResult,
	AuditRiskLevel,
	build_audit_metadata,
	normalize_audit_metadata,
	validate_audit_metadata,
)


class TestSecAuditMetadataSchema0500(IntegrationTestCase):
	def test_sec_0500_build_and_validate_required_fields(self) -> None:
		meta = build_audit_metadata(
			audit_event_code="STD_TEMPLATE_ACTIVATED",
			event_type="STD_TEMPLATE_ACTIVATED",
			object_type="STD Template",
			object_code="STD-TPL-001",
			result=AuditEventResult.SUCCESS,
			risk_level=AuditRiskLevel.MEDIUM,
		)
		valid = validate_audit_metadata(meta)
		self.assertEqual(valid["event_type"], "STD_TEMPLATE_ACTIVATED")
		self.assertEqual(valid["result"], "Success")
		self.assertEqual(valid["risk_level"], "Medium")
		self.assertIsInstance(valid["timestamp"], datetime)

	def test_sec_0500_normalize_legacy_aliases(self) -> None:
		meta = normalize_audit_metadata(
			{
				"event_code": "DERIVED_MODEL_GENERATED",
				"event_type": "DERIVED_MODEL_GENERATED",
				"object_type": "Tender STD Generated Output",
				"object_code": "OUT-001",
				"instance_code": "INST-001",
				"actor": "Administrator",
				"result": "Success",
				"risk_level": "Low",
			}
		)
		self.assertEqual(meta["audit_event_code"], "DERIVED_MODEL_GENERATED")
		self.assertEqual(meta["std_instance_code"], "INST-001")
		self.assertEqual(meta["actor_user_code"], "Administrator")

	def test_sec_0500_high_critical_requires_actor_reference(self) -> None:
		meta = build_audit_metadata(
			audit_event_code="PUBLISH_TENDER",
			event_type="PUBLISH_TENDER",
			object_type="Procurement Tender",
			object_code="TND-001",
			result="Denied",
			risk_level="Critical",
		)
		with self.assertRaisesRegex(ValueError, "actor_user_code"):
			validate_audit_metadata(meta)

	def test_sec_0500_invalid_result_and_risk_rejected(self) -> None:
		with self.assertRaisesRegex(ValueError, "result"):
			validate_audit_metadata(
				{
					"audit_event_code": "X",
					"event_type": "X",
					"object_type": "Obj",
					"object_code": "OBJ-1",
					"result": "Unknown",
					"risk_level": "Low",
					"timestamp": datetime.utcnow(),
				}
			)
		with self.assertRaisesRegex(ValueError, "risk_level"):
			validate_audit_metadata(
				{
					"audit_event_code": "Y",
					"event_type": "Y",
					"object_type": "Obj",
					"object_code": "OBJ-2",
					"result": "Success",
					"risk_level": "VeryHigh",
					"timestamp": datetime.utcnow(),
				}
			)

	def test_sec_0500_hash_and_details_fields_supported(self) -> None:
		meta = build_audit_metadata(
			audit_event_code="EVIDENCE_PACKAGE_EXPORTED",
			event_type="EVIDENCE_PACKAGE_EXPORTED",
			object_type="Procurement Tender",
			object_code="TND-010",
			result="Success",
			risk_level="High",
			actor_user_code="auditor@example.com",
			input_hash="ih-1",
			output_hash="oh-2",
			complete_snapshot_hash="sh-3",
			evidence_package_hash="eh-4",
			details={"format": "json_manifest"},
		)
		valid = validate_audit_metadata(meta)
		self.assertEqual(valid["input_hash"], "ih-1")
		self.assertEqual(valid["evidence_package_hash"], "eh-4")
		self.assertEqual(valid["details"], {"format": "json_manifest"})
