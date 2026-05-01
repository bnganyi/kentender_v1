# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 9 — minimal DocType graph meta tests (schema only, no loader/engine).

Spec §16 defers full automated tests; workspace TDD gate requires DocType-level evidence after migrate.
See **STD-POC-010** in ISSUES_LOG.md.

Run:
    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step9_doctypes
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

PARENT_DOCTYPES = ("STD Template", "Procurement Tender")
CHILD_DOCTYPES = (
	"Tender Lot",
	"Tender BoQ Item",
	"Tender Required Form",
	"Tender Validation Message",
)


class TestStdWorksPocStep9DocTypes(IntegrationTestCase):
	def test_step9_ac001_all_six_doctypes_exist(self) -> None:
		for name in PARENT_DOCTYPES + CHILD_DOCTYPES:
			with self.subTest(doctype=name):
				self.assertTrue(
					frappe.db.exists("DocType", name),
					f"STEP9-AC-001: DocType {name!r} must exist",
				)

	def test_step9_ac002_child_tables_flagged(self) -> None:
		for name in CHILD_DOCTYPES:
			with self.subTest(doctype=name):
				self.assertEqual(
					frappe.db.get_value("DocType", name, "istable"),
					1,
					f"STEP9-AC-002: {name} must be a child table (istable=1)",
				)
		for name in PARENT_DOCTYPES:
			with self.subTest(doctype=name):
				self.assertEqual(
					frappe.db.get_value("DocType", name, "istable"),
					0,
					f"STEP9-AC-002: {name} must not be a child table",
				)

	def test_step9_ac003_std_template_package_fields(self) -> None:
		meta = frappe.get_meta("STD Template")
		fieldnames = {df.fieldname for df in meta.fields}
		for fn in ("template_code", "package_json", "package_hash"):
			with self.subTest(field=fn):
				self.assertIn(fn, fieldnames, f"STEP9-AC-003: STD Template must define {fn}")

	def test_step9_ac004_procurement_tender_links_std_template(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		df = meta.get_field("std_template")
		self.assertIsNotNone(df, "STEP9-AC-004: std_template field must exist")
		self.assertEqual(df.fieldtype, "Link")
		self.assertEqual(df.options, "STD Template")

	def test_step9_ac005_configuration_json_field(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		self.assertIsNotNone(
			meta.get_field("configuration_json"),
			"STEP9-AC-005: configuration_json must exist",
		)

	def test_step9_ac006_child_table_links_on_tender(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		for fieldname, options in (
			("lots", "Tender Lot"),
			("boq_items", "Tender BoQ Item"),
			("required_forms", "Tender Required Form"),
			("validation_messages", "Tender Validation Message"),
		):
			with self.subTest(field=fieldname):
				df = meta.get_field(fieldname)
				self.assertIsNotNone(df, f"STEP9-AC-006: {fieldname} table must exist")
				self.assertEqual(df.fieldtype, "Table")
				self.assertEqual(df.options, options)

	def test_step9_ac007_boq_item_categories(self) -> None:
		meta = frappe.get_meta("Tender BoQ Item")
		df = meta.get_field("item_category")
		self.assertIsNotNone(df)
		opts = (df.options or "").split("\n")
		for cat in (
			"PRELIMINARIES",
			"DAYWORKS",
			"PROVISIONAL_SUMS",
			"GRAND_SUMMARY",
		):
			with self.subTest(category=cat):
				self.assertIn(cat, opts, f"STEP9-AC-007: item_category must include {cat}")

	def test_step9_ac008_validation_message_severities(self) -> None:
		meta = frappe.get_meta("Tender Validation Message")
		df = meta.get_field("severity")
		self.assertIsNotNone(df)
		opts = (df.options or "").split("\n")
		for sev in ("INFO", "WARNING", "ERROR", "BLOCKER"):
			with self.subTest(severity=sev):
				self.assertIn(sev, opts, f"STEP9-AC-008: severity must include {sev}")

	def test_step9_ac009_module_placement(self) -> None:
		# Spec §8: use existing app module when "Procurement" is not a separate Module Def.
		for name in PARENT_DOCTYPES + CHILD_DOCTYPES:
			with self.subTest(doctype=name):
				self.assertEqual(
					frappe.db.get_value("DocType", name, "module"),
					"Kentender Procurement",
					f"STEP9-AC-009: {name} must be in Kentender Procurement module",
				)
