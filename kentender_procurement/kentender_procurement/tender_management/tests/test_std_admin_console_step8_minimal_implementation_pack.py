# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 8 minimal implementation pack (facade + §28 checks)."""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_module,
)
from kentender_procurement.kentender_procurement.doctype.std_template import (
	std_template as std_template_module,
)
from kentender_procurement.tender_management.services import std_admin_console
from kentender_procurement.tender_management.services.std_template_engine import (
	populate_sample_tender,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	get_template_package_path,
	upsert_std_template,
)

TEMPLATE_NAME = "KE-PPRA-WORKS-BLDG-2022-04-POC"

# Doc 8 §9 required server methods (facade must expose these names).
REQUIRED_FACADE_NAMES: frozenset[str] = frozenset(
	{
		"get_template_package_summary",
		"get_template_package_component",
		"reimport_std_template_package",
		"validate_std_package",
		"trace_std_rules_for_sample",
		"trace_std_rules_for_tender",
		"create_or_open_std_demo_tender",
		"get_required_forms_inspection",
		"get_boq_inspection",
		"get_demo_inspector_summary",
		"get_preview_audit_summary",
	}
)


class TestSTDAdminConsoleStep8MinimalImplementationPack(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		upsert_std_template(package_path=get_template_package_path(), commit=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_admin_impl_ac001_module_exports_required_api(self):
		for name in REQUIRED_FACADE_NAMES:
			self.assertTrue(hasattr(std_admin_console, name), msg=f"missing {name}")
			self.assertTrue(callable(getattr(std_admin_console, name)), msg=f"not callable: {name}")
		exported = set(std_admin_console.__all__)
		self.assertEqual(REQUIRED_FACADE_NAMES, exported)

	def test_facade_parity_get_template_package_summary(self):
		direct = std_template_module.get_template_package_summary(TEMPLATE_NAME)
		via = std_admin_console.get_template_package_summary(TEMPLATE_NAME)
		self.assertEqual(direct.keys(), via.keys())
		self.assertEqual(direct.get("ok"), via.get("ok"))

	def test_facade_parity_get_preview_audit_summary(self):
		doc = frappe.new_doc("Procurement Tender")
		doc.naming_series = "PT-.YYYY.-.#####"
		doc.tender_title = "Step8 facade tender"
		doc.tender_reference = f"STD-STEP8-{frappe.generate_hash(length=8)}"
		doc.std_template = TEMPLATE_NAME
		doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		doc.tender_scope = "NATIONAL"
		populate_sample_tender(doc, variant_code=None)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		tname = doc.name
		try:
			procurement_tender_module.generate_required_forms(tname)
			procurement_tender_module.generate_sample_boq(tname)
			procurement_tender_module.generate_tender_pack_preview(tname)
			direct = procurement_tender_module.get_preview_audit_summary(tname)
			via = std_admin_console.get_preview_audit_summary(tname)
			self.assertEqual(direct.get("preview_status"), via.get("preview_status"))
			self.assertEqual(direct.get("ok"), via.get("ok"))
			self.assertEqual((direct.get("audit") or {}).get("configuration_hash"), (via.get("audit") or {}).get("configuration_hash"))
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_guest_denied_facade_template_summary(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			std_admin_console.get_template_package_summary(TEMPLATE_NAME)

	def test_read_only_facade_does_not_mutate_tender_modified(self):
		doc = frappe.new_doc("Procurement Tender")
		doc.naming_series = "PT-.YYYY.-.#####"
		doc.tender_title = "Step8 read-only tender"
		doc.tender_reference = f"STD-STEP8-R-{frappe.generate_hash(length=8)}"
		doc.std_template = TEMPLATE_NAME
		doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		doc.tender_scope = "NATIONAL"
		populate_sample_tender(doc, variant_code=None)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		tname = doc.name
		try:
			mod_before = frappe.db.get_value("Procurement Tender", tname, "modified")
			std_admin_console.get_required_forms_inspection(tname)
			std_admin_console.get_boq_inspection(tname)
			std_admin_console.get_demo_inspector_summary(tname)
			std_admin_console.get_preview_audit_summary(tname)
			mod_after = frappe.db.get_value("Procurement Tender", tname, "modified")
			self.assertEqual(mod_before, mod_after)
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_facade_validate_std_package_parity(self):
		direct = std_template_module.validate_std_package(TEMPLATE_NAME)
		via = std_admin_console.validate_std_package(TEMPLATE_NAME)
		self.assertEqual(direct.get("overall_status"), via.get("overall_status"))
		self.assertEqual(direct.get("ok"), via.get("ok"))
