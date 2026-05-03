# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-002 — ``Tender Works Requirement`` child DocType + ``works_requirements`` on tender (doc 5 §8, §7.1).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh002
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_COMPONENT_TYPE_OPTIONS = (
	"Scope\nSite Information\nTechnical Specification\nDrawing Register\n"
	"ESHS / HSE\nWork Programme\nKey Personnel\nEquipment\nCompletion Period\n"
	"Defects Liability\nOther"
)

_STATUS_OPTIONS = "Draft\nComplete\nMissing\nSuperseded"

_WH002_CHILD_FIELDS: tuple[tuple[str, str, int, str | None], ...] = (
	("component_code", "Data", 1, None),
	("component_type", "Select", 1, _COMPONENT_TYPE_OPTIONS),
	("title", "Data", 1, None),
	("structured_text", "Long Text", 1, None),
	("supplier_facing", "Check", 0, None),
	("submission_linked", "Check", 0, None),
	("contract_carry_forward", "Check", 0, None),
	("source_field_codes", "Small Text", 0, None),
	("status", "Select", 1, _STATUS_OPTIONS),
	("version", "Data", 1, None),
	("display_order", "Int", 0, None),
)


class TestWorksTenderHardeningWh002(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh002_child_meta_fields(self) -> None:
		meta = frappe.get_meta("Tender Works Requirement")
		self.assertEqual(meta.istable, 1)
		for fieldname, fieldtype, reqd, options in _WH002_CHILD_FIELDS:
			with self.subTest(field=fieldname):
				f = meta.get_field(fieldname)
				self.assertIsNotNone(f, f"missing field {fieldname}")
				self.assertEqual(f.fieldtype, fieldtype)
				self.assertEqual(int(f.reqd or 0), reqd)
				if options is not None:
					self.assertEqual(f.options, options)
		v = meta.get_field("version")
		self.assertEqual(v.default, "V1")
		st = meta.get_field("status")
		self.assertEqual(st.default, "Draft")
		do = meta.get_field("display_order")
		self.assertTrue(getattr(do, "non_negative", 0))

	def test_wh002_procurement_tender_has_works_requirements_table(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		f = meta.get_field("works_requirements")
		self.assertIsNotNone(f)
		self.assertEqual(f.fieldtype, "Table")
		self.assertEqual(f.options, "Tender Works Requirement")
		self.assertTrue(f.read_only)

	def test_wh002_append_child_row_persists(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-002 Child Row Test"
		doc.tender_reference = "WH002-ROW-001"
		doc.append(
			"works_requirements",
			{
				"component_code": "WH002-C1",
				"component_type": "Scope",
				"title": "Scope component",
				"structured_text": "Structured body for WH-002 test.",
				"status": "Complete",
				"version": "V1",
				"display_order": 1,
			},
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(len(reloaded.works_requirements), 1)
			row = reloaded.works_requirements[0]
			self.assertEqual(row.component_code, "WH002-C1")
			self.assertEqual(row.component_type, "Scope")
			self.assertEqual(row.title, "Scope component")
			self.assertEqual(row.status, "Complete")
			self.assertEqual(row.version, "V1")
			self.assertEqual(row.display_order, 1)
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
