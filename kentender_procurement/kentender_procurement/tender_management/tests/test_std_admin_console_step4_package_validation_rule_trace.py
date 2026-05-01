# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 4 validation + rule trace."""

from __future__ import annotations

import json
import unittest

import frappe

from kentender_procurement.kentender_procurement.doctype.std_template import (
	std_template as std_template_module,
)
from kentender_procurement.tender_management.services.std_template_engine import populate_sample_tender
from kentender_procurement.tender_management.services.std_template_loader import (
	get_template_package_path,
	upsert_std_template,
)

TEMPLATE_NAME = "KE-PPRA-WORKS-BLDG-2022-04-POC"


class TestSTDAdminConsoleStep4PackageValidationRuleTrace(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		upsert_std_template(package_path=get_template_package_path(), commit=True)

	def test_validate_std_package_structure(self):
		res = std_template_module.validate_std_package(TEMPLATE_NAME)
		self.assertIn("overall_status", res)
		self.assertIn(res["overall_status"], ("PASSED", "PASSED_WITH_WARNINGS"), res)
		self.assertTrue(res.get("ok"), res)
		self.assertIn("checks", res)
		self.assertGreaterEqual(len(res["checks"]), 30)
		codes = {c["check_code"] for c in res["checks"]}
		self.assertIn("PKG_COMPONENTS_PRESENT", codes)
		self.assertIn("RUL_RULE_TYPES_SUPPORTED", codes)
		self.assertIn("html", res)
		self.assertIn("Overall status", res["html"])

	def test_trace_primary_sample(self):
		res = std_template_module.trace_std_rules_for_sample(TEMPLATE_NAME, None)
		self.assertTrue(res.get("ok"), res)
		self.assertEqual(res.get("trace_source"), "PRIMARY_SAMPLE")
		self.assertIsNone(res.get("variant_code"))
		rules = res.get("rules") or []
		self.assertEqual(len(rules), 31)
		vr = res.get("validation_result") or {}
		self.assertIn("messages", vr)
		self.assertIn("configuration_hash", vr)
		active = (vr.get("active_forms") or {}).keys()
		self.assertIn("FORM_TENDER_SECURITY", active)
		self.assertNotIn("FORM_TENDER_SECURING_DECLARATION", active)
		self.assertNotIn("FORM_FOREIGN_TENDERER_LOCAL_INPUT", active)
		self.assertIn("html", res)

	def test_trace_variant_tender_securing(self):
		res = std_template_module.trace_std_rules_for_sample(
			TEMPLATE_NAME,
			"VARIANT-TENDER-SECURING-DECLARATION",
		)
		self.assertTrue(res.get("ok"), res)
		self.assertEqual(res.get("trace_source"), "SAMPLE_VARIANT")
		vr = res.get("validation_result") or {}
		active = (vr.get("active_forms") or {}).keys()
		self.assertIn("FORM_TENDER_SECURING_DECLARATION", active)
		self.assertNotIn("FORM_TENDER_SECURITY", active)

	def test_trace_variant_international(self):
		res = std_template_module.trace_std_rules_for_sample(TEMPLATE_NAME, "VARIANT-INTERNATIONAL")
		self.assertTrue(res.get("ok"), res)
		vr = res.get("validation_result") or {}
		active = (vr.get("active_forms") or {}).keys()
		self.assertIn("FORM_FOREIGN_TENDERER_LOCAL_INPUT", active)

	def test_trace_variant_negative_blockers(self):
		for variant in (
			"VARIANT-MISSING-SITE-VISIT-DATE",
			"VARIANT-MISSING-ALTERNATIVE-SCOPE",
		):
			with self.subTest(variant=variant):
				res = std_template_module.trace_std_rules_for_sample(TEMPLATE_NAME, variant)
				self.assertFalse(res.get("ok"), res)
				vr = res.get("validation_result") or {}
				self.assertTrue(vr.get("blocks_generation"), vr)

	def test_trace_unknown_variant_error(self):
		res = std_template_module.trace_std_rules_for_sample(TEMPLATE_NAME, "VARIANT-NONEXISTENT-XYZ")
		self.assertFalse(res.get("ok"))
		self.assertIn("error", res)

	def test_guest_cannot_validate(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				std_template_module.validate_std_package(TEMPLATE_NAME)
		finally:
			frappe.set_user("Administrator")

	def test_trace_std_rules_for_tender(self):
		tname = "PW-STD-ADMIN4-TENDER"
		if frappe.db.exists("Procurement Tender", tname):
			frappe.delete_doc("Procurement Tender", tname, force=True)
		doc = frappe.new_doc("Procurement Tender")
		doc.tender_title = "Admin step 4 trace tender"
		doc.tender_reference = "STD-ADMIN-4-TRACE"
		doc.std_template = TEMPLATE_NAME
		doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		doc.tender_scope = "NATIONAL"
		populate_sample_tender(doc, None)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		try:
			res = std_template_module.trace_std_rules_for_tender(doc.name)
			self.assertTrue(res.get("ok"), res)
			self.assertEqual(res.get("trace_source"), "DEMO_TENDER")
			self.assertEqual(res.get("tender"), doc.name)
			self.assertIn("rules", res)
			self.assertIn("validation_result", res)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True)
			frappe.db.commit()


if __name__ == "__main__":
	frappe.init(site="kentender.midas.com")
	frappe.connect()
	unittest.main()
