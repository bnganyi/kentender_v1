# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW1 — schema regression: new Package Creation Wizard fields on
Procurement Package (`package_owner`, `target_release_date`,
`package_priority` Normal/High/Emergency) and Procurement Package Line
(`lot_group`, `delivery_location`), plus the legacy-priority backfill
patch."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.patches.pw1_backfill_package_priority_normal import execute as backfill_priority


class TestPW1PackageWizardSchema(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")

	def test_procurement_package_has_owner_and_release_date_fields(self):
		meta = frappe.get_meta("Procurement Package")
		self.assertTrue(meta.has_field("package_owner"))
		self.assertEqual(meta.get_field("package_owner").fieldtype, "Link")
		self.assertEqual(meta.get_field("package_owner").options, "User")
		self.assertTrue(meta.has_field("target_release_date"))
		self.assertEqual(meta.get_field("target_release_date").fieldtype, "Date")

	def test_package_priority_options_are_normal_high_emergency(self):
		meta = frappe.get_meta("Procurement Package")
		field = meta.get_field("package_priority")
		options = [o.strip() for o in (field.options or "").split("\n") if o.strip()]
		self.assertEqual(options, ["Normal", "High", "Emergency"])

	def test_package_line_has_lot_group_and_delivery_location(self):
		meta = frappe.get_meta("Procurement Package Line")
		self.assertTrue(meta.has_field("lot_group"))
		self.assertTrue(meta.has_field("delivery_location"))

	def test_backfill_patch_remaps_legacy_medium_low_to_normal(self):
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self.skipTest("Procurement Plan doctype unavailable in this test env")
		# Force legacy values directly at the DB layer (bypassing Select
		# validation) to simulate pre-migration rows, then run the patch.
		package_names = frappe.get_all("Procurement Package", pluck="name", limit=1)
		if not package_names:
			self.skipTest("No Procurement Package rows available to exercise the backfill on")
		name = package_names[0]
		original = frappe.db.get_value("Procurement Package", name, "package_priority")
		try:
			frappe.db.sql(
				"UPDATE `tabProcurement Package` SET `package_priority` = %s WHERE `name` = %s",
				("Medium", name),
			)
			backfill_priority()
			self.assertEqual(frappe.db.get_value("Procurement Package", name, "package_priority"), "Normal")
			frappe.db.sql(
				"UPDATE `tabProcurement Package` SET `package_priority` = %s WHERE `name` = %s",
				("Low", name),
			)
			backfill_priority()
			self.assertEqual(frappe.db.get_value("Procurement Package", name, "package_priority"), "Normal")
		finally:
			frappe.db.sql(
				"UPDATE `tabProcurement Package` SET `package_priority` = %s WHERE `name` = %s",
				(original, name),
			)

	def test_backfill_patch_is_idempotent_without_table(self):
		# Should never raise even if called repeatedly.
		backfill_priority()
		backfill_priority()
