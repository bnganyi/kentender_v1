# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 6 required forms + BoQ inspectors."""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_module,
)
from kentender_procurement.tender_management.services.std_forms_boq_inspectors import (
	BOQ_POC_WARNING,
	get_boq_inspection,
	get_required_forms_inspection,
)
from kentender_procurement.tender_management.services.std_template_engine import (
	populate_sample_tender,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	get_template_package_path,
	upsert_std_template,
)

TEMPLATE_NAME = "KE-PPRA-WORKS-BLDG-2022-04-POC"


class TestSTDAdminConsoleStep6FormsBoqInspectors(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		upsert_std_template(package_path=get_template_package_path(), commit=True)

	def _make_populated_tender(self, variant_code: str | None = None) -> str:
		name = frappe.generate_hash(length=10)
		doc = frappe.new_doc("Procurement Tender")
		doc.naming_series = "PT-.YYYY.-.#####"
		doc.tender_title = "Step6 inspector tender"
		doc.tender_reference = f"STD-STEP6-{name}"
		doc.std_template = TEMPLATE_NAME
		doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		doc.tender_scope = "NATIONAL"
		populate_sample_tender(doc, variant_code=variant_code)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		procurement_tender_module.generate_required_forms(doc.name)
		procurement_tender_module.generate_sample_boq(doc.name)
		return doc.name

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_primary_required_forms_inspection(self):
		tname = self._make_populated_tender(None)
		try:
			mod_before = frappe.db.get_value("Procurement Tender", tname, "modified")
			res = get_required_forms_inspection(tname)
			mod_after = frappe.db.get_value("Procurement Tender", tname, "modified")
			self.assertEqual(mod_before, mod_after)
			self.assertTrue(res.get("ok"))
			self.assertEqual(res["summary"]["total_forms"], 15)
			self.assertEqual(res["summary"]["duplicate_form_code_count"], 0)
			self.assertEqual(len(res["rows"]), 15)
			self.assertGreater(len(res.get("expected_comparison") or []), 0)
			self.assertIn("html", res)
			self.assertIn("std-admin-forms-inspector", res["html"])
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_international_variant_expected_forms(self):
		tname = self._make_populated_tender("VARIANT-INTERNATIONAL")
		try:
			res = get_required_forms_inspection(tname)
			self.assertEqual(res.get("variant_detected"), "VARIANT-INTERNATIONAL")
			codes = {r["form_code"] for r in res["rows"]}
			self.assertIn("FORM_FOREIGN_TENDERER_LOCAL_INPUT", codes)
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_boq_inspection_primary(self):
		tname = self._make_populated_tender(None)
		try:
			mod_before = frappe.db.get_value("Procurement Tender", tname, "modified")
			res = get_boq_inspection(tname)
			mod_after = frappe.db.get_value("Procurement Tender", tname, "modified")
			self.assertEqual(mod_before, mod_after)
			self.assertTrue(res.get("ok"))
			self.assertEqual(res["summary"]["row_count"], 9)
			self.assertEqual(res["summary"]["duplicate_item_code_count"], 0)
			self.assertEqual(res["summary"]["invalid_lot_reference_count"], 0)
			self.assertIn(BOQ_POC_WARNING[:40], res["poc_warning"])
			self.assertIn("std-admin-boq-inspector", res["html"])
			cats = {c["category"]: c["row_count"] for c in res["category_coverage"] if c["category"] != "OTHER"}
			self.assertGreater(cats.get("PRELIMINARIES", 0), 0)
			self.assertGreater(cats.get("GRAND_SUMMARY", 0), 0)
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_empty_required_forms_messages(self):
		tname = self._make_populated_tender(None)
		try:
			doc = frappe.get_doc("Procurement Tender", tname)
			doc.set("required_forms", [])
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			res = get_required_forms_inspection(tname)
			self.assertTrue(res.get("ok"))
			self.assertEqual(res["summary"]["total_forms"], 0)
			self.assertTrue(any("No required forms" in w for w in res.get("warnings") or []))
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_guest_cannot_inspect(self):
		tname = self._make_populated_tender(None)
		try:
			frappe.set_user("Guest")
			with self.assertRaises(frappe.PermissionError):
				get_required_forms_inspection(tname)
			frappe.set_user("Guest")
			with self.assertRaises(frappe.PermissionError):
				get_boq_inspection(tname)
		finally:
			frappe.set_user("Administrator")
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()

	def test_whitelisted_demo_summary(self):
		tname = self._make_populated_tender(None)
		try:
			out = procurement_tender_module.get_demo_inspector_summary(tname)
			self.assertTrue(out.get("ok"))
			self.assertIn("forms_html", out)
			self.assertIn("boq_html", out)
			self.assertIn("required_forms", out)
		finally:
			frappe.delete_doc("Procurement Tender", tname, force=True)
			frappe.db.commit()


if __name__ == "__main__":
	frappe.init(site="kentender.midas.com")
	frappe.connect()
	unittest.main()
