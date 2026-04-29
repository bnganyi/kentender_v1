from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.template_version_workbench import (
	export_std_template_version_audit_evidence_csv,
	get_std_template_version_audit_evidence,
)
from kentender_procurement.std_engine.services.template_version_audit_evidence_service import (
	build_std_template_version_audit_evidence,
	build_std_template_version_audit_export_csv,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1014TemplateVersionAuditEvidence(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("STD Audit Event", {"audit_event_code": ("like", "AUD-PH14-%")})
		super().tearDown()

	def _insert_audit(self, event_type: str = "TEMPLATE_VERSION_CREATED"):
		frappe.get_doc(
			{
				"doctype": "STD Audit Event",
				"audit_event_code": f"AUD-PH14-{frappe.generate_hash(length=8).upper()}",
				"event_type": event_type,
				"object_type": "TEMPLATE_VERSION",
				"object_code": self.version_code,
				"actor": "Administrator",
				"timestamp": frappe.utils.now(),
			}
		).insert(ignore_permissions=True)

	def test_not_found(self):
		out = build_std_template_version_audit_evidence("NO-SUCH-VERSION-999")
		self.assertFalse(out.get("ok"))

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_audit_evidence, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_timeline_includes_version_events(self):
		self._insert_audit()
		out = build_std_template_version_audit_evidence(self.version_code)
		self.assertTrue(out.get("ok"))
		tl = out.get("lifecycle_timeline") or []
		self.assertTrue(any(e.get("object_code") == self.version_code for e in tl))
		self.assertIn("evidence_sections", out)
		self.assertIn("permissions", out)

	def test_export_csv_for_administrator(self):
		self._insert_audit()
		out = build_std_template_version_audit_export_csv(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("audit_event_code", out.get("csv_text") or "")
		api_out = export_std_template_version_audit_evidence_csv(self.version_code)
		self.assertTrue(api_out.get("ok"))
		self.assertIn(".csv", str(api_out.get("filename") or ""))
