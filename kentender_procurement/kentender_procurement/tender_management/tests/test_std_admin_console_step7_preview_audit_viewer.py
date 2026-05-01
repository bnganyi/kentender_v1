# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 7 preview and audit viewer."""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_module,
)
from kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender import (
	RENDER_CONTEXT_BANNER,
)
from kentender_procurement.tender_management.services.std_preview_audit_viewer import (
	PREVIEW_VIEWER_POC_WARNING,
	get_preview_audit_summary,
)
from kentender_procurement.tender_management.services.std_template_engine import (
	populate_sample_tender,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	get_template_package_path,
	upsert_std_template,
)

TEMPLATE_NAME = "KE-PPRA-WORKS-BLDG-2022-04-POC"


class TestSTDAdminConsoleStep7PreviewAuditViewer(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		upsert_std_template(package_path=get_template_package_path(), commit=True)

	def _make_tender(self, variant_code: str | None = None) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.naming_series = "PT-.YYYY.-.#####"
		doc.tender_title = "Step7 preview audit tender"
		doc.tender_reference = f"STD-STEP7-{frappe.generate_hash(length=8)}"
		doc.std_template = TEMPLATE_NAME
		doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		doc.tender_scope = "NATIONAL"
		populate_sample_tender(doc, variant_code=variant_code)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return doc.name

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_generated_preview_happy_path(self):
		tname = self._make_tender(None)
		try:
			procurement_tender_module.generate_required_forms(tname)
			procurement_tender_module.generate_sample_boq(tname)
			procurement_tender_module.generate_tender_pack_preview(tname)
			mod_before = frappe.db.get_value("Procurement Tender", tname, "modified")
			res = get_preview_audit_summary(tname)
			mod_after = frappe.db.get_value("Procurement Tender", tname, "modified")
			self.assertEqual(mod_before, mod_after)
			self.assertTrue(res.get("ok"))
			self.assertEqual(res.get("preview_status"), "Generated")
			self.assertIn(PREVIEW_VIEWER_POC_WARNING[:30], res.get("poc_warning", ""))
			self.assertEqual(res["required_forms_summary"]["row_count"], 15)
			self.assertEqual(res["boq_summary"]["row_count"], 9)
			self.assertTrue((res.get("audit") or {}).get("configuration_hash"))
			self.assertIn("std-admin-preview-audit-viewer", res.get("html", ""))
			self.assertIn("std-preview-audit-iframe", res.get("html", ""))
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_not_generated_empty_or_render_context(self):
		tname = self._make_tender(None)
		try:
			doc = frappe.get_doc("Procurement Tender", tname)
			doc.generated_tender_pack_html = f"{RENDER_CONTEXT_BANNER}\n{{}}"
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			res = get_preview_audit_summary(tname)
			self.assertEqual(res.get("preview_status"), "Not Generated")
			self.assertIn("No tender-pack preview", res.get("html", "") or "")
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_blocked_variant(self):
		tname = self._make_tender("VARIANT-MISSING-SITE-VISIT-DATE")
		try:
			procurement_tender_module.validate_tender_configuration(tname)
			res = get_preview_audit_summary(tname)
			self.assertEqual(res.get("preview_status"), "Blocked")
			self.assertTrue((res.get("validation_summary") or {}).get("has_blockers"))
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_guest_denied(self):
		tname = self._make_tender(None)
		try:
			frappe.set_user("Guest")
			with self.assertRaises(frappe.PermissionError):
				get_preview_audit_summary(tname)
		finally:
			frappe.set_user("Administrator")
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_whitelist_controller(self):
		tname = self._make_tender(None)
		try:
			out = procurement_tender_module.get_preview_audit_summary(tname)
			self.assertTrue(out.get("ok"))
			self.assertIn("preview_status", out)
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()


if __name__ == "__main__":
	frappe.init(site="kentender.midas.com")
	frappe.connect()
	unittest.main()
