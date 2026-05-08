# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-003 — child DocTypes for STD template governance (doc 7 §§8–10).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_doctype_gov003
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

CHILD_DOCTYPES = (
	"STD Template Lifecycle Event",
	"STD Template Validation Finding",
	"STD Template Usage",
)


class TestStdTemplateGovernanceDocTypeGov003(IntegrationTestCase):
	def test_std_gov_003_child_doctypes_exist_and_are_tables(self) -> None:
		for name in CHILD_DOCTYPES:
			with self.subTest(doctype=name):
				self.assertTrue(frappe.db.exists("DocType", name))
				self.assertEqual(
					frappe.db.get_value("DocType", name, "istable"),
					1,
					f"{name} must be a child table",
				)
				self.assertEqual(
					frappe.db.get_value("DocType", name, "module"),
					"Kentender Procurement",
				)

	def test_std_gov_003_std_template_table_links(self) -> None:
		meta = frappe.get_meta("STD Template")
		for fieldname, options in (
			("lifecycle_events", "STD Template Lifecycle Event"),
			("validation_findings", "STD Template Validation Finding"),
			("template_usage", "STD Template Usage"),
		):
			with self.subTest(field=fieldname):
				df = meta.get_field(fieldname)
				self.assertIsNotNone(df, f"STD Template.{fieldname} missing")
				self.assertEqual(df.fieldtype, "Table")
				self.assertEqual(df.options, options)

	def test_std_gov_003_lifecycle_event_required_columns(self) -> None:
		meta = frappe.get_meta("STD Template Lifecycle Event")
		for fn in ("event_code", "event_type", "actor", "event_at"):
			self.assertIsNotNone(meta.get_field(fn), fn)

	def test_std_gov_003_validation_finding_severity_options(self) -> None:
		meta = frappe.get_meta("STD Template Validation Finding")
		df = meta.get_field("severity")
		opts = (df.options or "").split("\n")
		self.assertIn("Critical", opts)
		self.assertIn("Info", opts)

	def test_std_gov_003_usage_type_options(self) -> None:
		meta = frappe.get_meta("STD Template Usage")
		df = meta.get_field("usage_type")
		opts = (df.options or "").split("\n")
		self.assertIn("Tender", opts)
		self.assertIn("Planning Mapping Test", opts)
