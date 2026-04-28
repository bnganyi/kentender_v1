# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase


def _minimal_template_family(template_code: str) -> dict[str, object]:
	return {
		"doctype": "STD Template Family",
		"template_code": template_code,
		"template_title": "PPRA Works STD Template Family",
		"issuing_authority": "PPRA",
		"procurement_category": "Works",
		"primary_procurement_method": "Open Tender",
		"allowed_procurement_methods": "[\"Open Tender\", \"Restricted Tender\"]",
		"family_status": "Active",
		"is_active_family": 1,
	}


def _cleanup_template_family(template_code: str) -> None:
	name = frappe.db.get_value("STD Template Family", {"template_code": template_code}, "name")
	if name:
		frappe.delete_doc("STD Template Family", name, force=True, ignore_permissions=True)


class TestSTDTemplateFamily(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_cleanup_template_family("STD-WORKS")
		_cleanup_template_family("STD-WORKS-DUP")

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			_cleanup_template_family("STD-WORKS")
			_cleanup_template_family("STD-WORKS-DUP")
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_create_template_family_success(self):
		doc = frappe.get_doc(_minimal_template_family("STD-WORKS")).insert()
		self.assertEqual(doc.template_code, "STD-WORKS")
		self.assertEqual(doc.default_language, "English")
		self.assertEqual(doc.family_status, "Active")

	def test_template_code_must_be_unique(self):
		frappe.get_doc(_minimal_template_family("STD-WORKS")).insert()
		with self.assertRaises((frappe.DuplicateEntryError, ValidationError)):
			frappe.get_doc(_minimal_template_family("STD-WORKS")).insert()

	def test_is_active_family_requires_active_status(self):
		payload = _minimal_template_family("STD-WORKS")
		payload["family_status"] = "Draft"
		with self.assertRaises(ValidationError):
			frappe.get_doc(payload).insert()

	def test_archive_blocked_when_active_template_versions_depend_on_family(self):
		doc = frappe.get_doc(_minimal_template_family("STD-WORKS-DUP")).insert()
		doc.family_status = "Archived"
		with patch(
			"kentender_procurement.procurement_planning.doctype.std_template_family.std_template_family."
			"STDTemplateFamily._has_active_template_version_dependency",
			return_value=True,
		):
			with self.assertRaises(ValidationError):
				doc.save()

