# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 3 package viewer RPC."""

from __future__ import annotations

import json
import unittest

import frappe

from kentender_procurement.kentender_procurement.doctype.std_template import (
	std_template as std_template_module,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	get_template_package_path,
	upsert_std_template,
)


class TestSTDAdminConsoleStep3PackageViewer(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		upsert_std_template(package_path=get_template_package_path(), commit=True)

	def test_get_template_package_summary_ok(self):
		res = std_template_module.get_template_package_summary("KE-PPRA-WORKS-BLDG-2022-04-POC")
		self.assertTrue(res.get("ok"), res)
		self.assertIn("html", res)
		self.assertIn("POC Administration View", res["html"])
		self.assertIn("sections", res)
		self.assertGreaterEqual(len(res["sections"]), 1)

	def test_get_template_package_component_manifest(self):
		res = std_template_module.get_template_package_component(
			"KE-PPRA-WORKS-BLDG-2022-04-POC",
			"manifest",
		)
		self.assertTrue(res.get("ok"), res)
		data = json.loads(res["json"])
		self.assertEqual(data.get("template_code"), "KE-PPRA-WORKS-BLDG-2022-04-POC")

	def test_get_template_package_component_full_package(self):
		res = std_template_module.get_template_package_component(
			"KE-PPRA-WORKS-BLDG-2022-04-POC",
			"full_package",
		)
		self.assertTrue(res.get("ok"), res)
		data = json.loads(res["json"])
		self.assertIn("manifest", data)

	def test_guest_cannot_reimport(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				std_template_module.reimport_std_template_package()
		finally:
			frappe.set_user("Administrator")


if __name__ == "__main__":
	frappe.init(site="kentender.midas.com")
	frappe.connect()
	unittest.main()
