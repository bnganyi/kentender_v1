from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.evidence_export import export_std_evidence_package
from kentender_procurement.std_engine.services.evidence_export_service import (
	build_std_evidence_export_package,
)
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1301EvidenceExportService(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_invalid_request_missing_object_code(self):
		out = build_std_evidence_export_package("Template Version", "")
		self.assertFalse(out.get("ok"))
		self.assertEqual("invalid", out.get("error"))

	def test_template_version_export_ok_and_csv_present(self):
		out = build_std_evidence_export_package("Template Version", self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual("Template Version", out.get("object_type"))
		self.assertEqual(self.version_code, out.get("object_code"))
		self.assertIn("csv_text", out)
		self.assertIn("audit_event_code", str(out.get("csv_text") or ""))
		self.assertIn("metadata", out)
		self.assertIn("package", out)

	def test_std_instance_export_contains_lineage_sections(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		out = build_std_evidence_export_package("STD Instance", self.instance_code)
		self.assertTrue(out.get("ok"))
		package = out.get("package") or {}
		self.assertIn("source_document_reference", package)
		self.assertIn("template_family", package)
		self.assertIn("template_version", package)
		self.assertIn("applicability_profile", package)
		self.assertIn("generated_outputs", package)
		self.assertIn("audit_events", package)

	def test_non_audit_role_cannot_export(self):
		out = build_std_evidence_export_package("STD Instance", self.instance_code, actor="requisitioner@moh.test")
		self.assertFalse(out.get("ok"))
		self.assertEqual("not_permitted", out.get("error"))

	def test_api_guest_rejected(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, export_std_evidence_package, "Template Version", self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_api_export_ok_for_authorized_user(self):
		out = export_std_evidence_package("Template Version", self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertIn(".csv", str(out.get("filename") or ""))
		self.assertIn("package", out)

	def test_export_action_is_audited(self):
		before = frappe.db.count(
			"STD Audit Event",
			{"event_type": "EVIDENCE_EXPORTED", "object_type": "STD_INSTANCE", "object_code": self.instance_code},
		)
		out = build_std_evidence_export_package("STD Instance", self.instance_code)
		self.assertTrue(out.get("ok"))
		after = frappe.db.count(
			"STD Audit Event",
			{"event_type": "EVIDENCE_EXPORTED", "object_type": "STD_INSTANCE", "object_code": self.instance_code},
		)
		self.assertGreater(after, before)
