# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 9 smoke (server-side API checks)."""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_module,
)
from kentender_procurement.kentender_procurement.doctype.std_template import (
	std_template as std_template_module,
)
from kentender_procurement.tender_management.services.std_preview_audit_viewer import (
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


class TestSTDAdminConsoleStep9SmokeApi(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		upsert_std_template(package_path=get_template_package_path(), commit=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_validate_std_package_passes_or_warnings(self):
		out = std_template_module.validate_std_package(TEMPLATE_NAME)
		self.assertIn(out.get("overall_status"), ("PASSED", "PASSED_WITH_WARNINGS"), msg=str(out)[:500])

	def test_trace_primary_sample_ok(self):
		out = std_template_module.trace_std_rules_for_sample(TEMPLATE_NAME, None)
		self.assertTrue(out.get("ok"))
		self.assertIn("PRIMARY_SAMPLE", out.get("trace_source", ""))

	def test_trace_positive_variant_tender_securing(self):
		out = std_template_module.trace_std_rules_for_sample(
			TEMPLATE_NAME,
			"VARIANT-TENDER-SECURING-DECLARATION",
		)
		self.assertTrue(out.get("ok"))
		html = out.get("html") or ""
		self.assertIn("FORM_TENDER_SECURING_DECLARATION", html.upper())

	def test_trace_negative_variant_has_blocker_signals(self):
		out = std_template_module.trace_std_rules_for_sample(
			TEMPLATE_NAME,
			"VARIANT-MISSING-SITE-VISIT-DATE",
		)
		self.assertEqual(out.get("trace_source"), "SAMPLE_VARIANT")
		html = (out.get("html") or "").lower()
		self.assertTrue("blocker" in html or "site" in html or "missing" in html)

	def test_blocked_tender_preview_audit_status(self):
		doc = frappe.new_doc("Procurement Tender")
		doc.naming_series = "PT-.YYYY.-.#####"
		doc.tender_title = "Step9 API smoke blocked"
		doc.tender_reference = f"STD-STEP9-{frappe.generate_hash(length=8)}"
		doc.std_template = TEMPLATE_NAME
		doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		doc.tender_scope = "NATIONAL"
		populate_sample_tender(doc, variant_code="VARIANT-MISSING-SITE-VISIT-DATE")
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		tname = doc.name
		try:
			procurement_tender_module.validate_tender_configuration(tname)
			res = get_preview_audit_summary(tname)
			self.assertEqual(res.get("preview_status"), "Blocked")
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()
