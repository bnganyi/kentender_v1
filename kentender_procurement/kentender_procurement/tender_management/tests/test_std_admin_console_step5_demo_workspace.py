# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 5 demo workspace + create demo tender."""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as procurement_tender_module,
)
from kentender_procurement.kentender_procurement.doctype.std_template import (
	std_template as std_template_module,
)
from kentender_procurement.tender_management.services.std_demo_workspace import (
	BANNER_TEXT,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	get_template_package_path,
	upsert_std_template,
)

TEMPLATE_NAME = "KE-PPRA-WORKS-BLDG-2022-04-POC"


class TestSTDAdminConsoleStep5DemoWorkspace(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		upsert_std_template(package_path=get_template_package_path(), commit=True)

	def test_create_or_open_std_demo_tender_primary(self):
		res = std_template_module.create_or_open_std_demo_tender(TEMPLATE_NAME, None)
		self.assertTrue(res.get("ok"), res)
		self.assertIn("tender", res)
		self.assertTrue(res.get("tender"))
		self.assertIn("/app/procurement-tender/", res.get("route", ""))
		name = res["tender"]
		try:
			doc = frappe.get_doc("Procurement Tender", name)
			self.assertEqual(doc.std_template, TEMPLATE_NAME)
			self.assertTrue(doc.tender_reference.startswith("STD-DEMO-"))
			self.assertIn("STD DEMO WORKSPACE", doc.poc_notes or "")
			self.assertTrue((doc.configuration_json or "").strip())
			self.assertEqual(len(doc.lots), 2)
			self.assertEqual(len(doc.boq_items), 9)
			self.assertEqual(doc.tender_status, "Configured")
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True)
			frappe.db.commit()

	def test_create_or_open_std_demo_tender_variant_single_lot(self):
		res = std_template_module.create_or_open_std_demo_tender(
			TEMPLATE_NAME,
			"VARIANT-SINGLE-LOT",
		)
		self.assertTrue(res.get("ok"), res)
		name = res["tender"]
		try:
			doc = frappe.get_doc("Procurement Tender", name)
			self.assertEqual(len(doc.lots), 1)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True)
			frappe.db.commit()

	def test_get_std_demo_workspace_html(self):
		res = std_template_module.create_or_open_std_demo_tender(TEMPLATE_NAME, None)
		self.assertTrue(res.get("ok"), res)
		name = res["tender"]
		try:
			html_res = procurement_tender_module.get_std_demo_workspace_html(name)
			self.assertTrue(html_res.get("ok"), html_res)
			html = html_res.get("html") or ""
			self.assertIn(BANNER_TEXT, html)
			self.assertIn("Current state summary", html)
			self.assertIn("Configured", html)
			self.assertIn("Not Validated", html)
		finally:
			frappe.delete_doc("Procurement Tender", name, force=True)
			frappe.db.commit()

	def test_get_std_demo_workspace_html_for_poc_template_without_explicit_demo_marker(self):
		"""POC template link alone qualifies for the demo workspace HTML (Step 5 OR rule)."""
		for stale in frappe.get_all(
			"Procurement Tender",
			filters={"tender_reference": "POC-NOMARKER-5"},
			pluck="name",
		):
			frappe.delete_doc("Procurement Tender", stale, force=True)
		frappe.db.commit()
		doc = frappe.new_doc("Procurement Tender")
		doc.naming_series = "PT-.YYYY.-.#####"
		doc.tender_title = "POC-linked tender"
		doc.tender_reference = "POC-NOMARKER-5"
		doc.std_template = TEMPLATE_NAME
		doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		doc.tender_scope = "NATIONAL"
		doc.poc_notes = "UAT notes without STD DEMO WORKSPACE substring."
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		created_name = doc.name
		try:
			out = procurement_tender_module.get_std_demo_workspace_html(created_name)
			self.assertTrue(out.get("ok"), out)
			self.assertIn(BANNER_TEXT, out.get("html") or "")
		finally:
			frappe.delete_doc("Procurement Tender", created_name, force=True)
			frappe.db.commit()

	def test_guest_cannot_read_demo_workspace_html(self):
		res = std_template_module.create_or_open_std_demo_tender(TEMPLATE_NAME, None)
		self.assertTrue(res.get("ok"), res)
		name = res["tender"]
		try:
			frappe.set_user("Guest")
			with self.assertRaises(frappe.PermissionError):
				procurement_tender_module.get_std_demo_workspace_html(name)
		finally:
			frappe.set_user("Administrator")
			frappe.delete_doc("Procurement Tender", name, force=True)
			frappe.db.commit()

	def test_guest_cannot_create_demo_tender(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				std_template_module.create_or_open_std_demo_tender(TEMPLATE_NAME, None)
		finally:
			frappe.set_user("Administrator")


if __name__ == "__main__":
	frappe.init(site="kentender.midas.com")
	frappe.connect()
	unittest.main()
