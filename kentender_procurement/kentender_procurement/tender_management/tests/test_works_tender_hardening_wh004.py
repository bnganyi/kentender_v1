# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-004 — ``Tender Derived Model Readiness`` + ``derived_model_readiness`` on tender (doc 5 §10, §7.1).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh004
"""

from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_MODEL_TYPE_OPTIONS = "Submission\nOpening\nEvaluation\nContract Carry-Forward"
_STATUS_OPTIONS = "Generated\nPlaceholder\nMissing\nBlocked"
_VALIDATION_STATUS_OPTIONS = "Pass\nWarning\nBlocked\nNot Checked"

_WH004_CHILD_FIELDS: tuple[tuple[str, str, int, str | None], ...] = (
	("model_type", "Select", 1, _MODEL_TYPE_OPTIONS),
	("model_code", "Data", 1, None),
	("source_std_template", "Link", 0, "STD Template"),
	("source_tender", "Link", 0, "Procurement Tender"),
	("status", "Select", 1, _STATUS_OPTIONS),
	("blocking_for_publication", "Check", 0, None),
	("components_summary", "Long Text", 0, None),
	("deferred_reason", "Small Text", 0, None),
	("validation_status", "Select", 1, _VALIDATION_STATUS_OPTIONS),
	("version", "Data", 1, None),
)


class TestWorksTenderHardeningWh004(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh004_child_meta_fields(self) -> None:
		meta = frappe.get_meta("Tender Derived Model Readiness")
		self.assertEqual(meta.istable, 1)
		for fieldname, fieldtype, reqd, options in _WH004_CHILD_FIELDS:
			with self.subTest(field=fieldname):
				f = meta.get_field(fieldname)
				self.assertIsNotNone(f, f"missing field {fieldname}")
				self.assertEqual(f.fieldtype, fieldtype)
				self.assertEqual(int(f.reqd or 0), reqd)
				if options is not None:
					self.assertEqual(f.options, options)
		v = meta.get_field("version")
		self.assertEqual(v.default, "V1")
		vs = meta.get_field("validation_status")
		self.assertEqual(vs.default, "Not Checked")

	def test_wh004_model_type_has_four_values(self) -> None:
		meta = frappe.get_meta("Tender Derived Model Readiness")
		f = meta.get_field("model_type")
		self.assertIsNotNone(f)
		self.assertEqual(
			set((f.options or "").strip().split("\n")),
			{"Submission", "Opening", "Evaluation", "Contract Carry-Forward"},
		)

	def test_wh004_procurement_tender_has_derived_model_readiness_table(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		f = meta.get_field("derived_model_readiness")
		self.assertIsNotNone(f)
		self.assertEqual(f.fieldtype, "Table")
		self.assertEqual(f.options, "Tender Derived Model Readiness")
		self.assertTrue(f.read_only)

	def test_wh004_append_placeholder_row_persists(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-004 Derived Model Readiness Test"
		doc.tender_reference = "WH004-ROW-001"
		doc.append(
			"derived_model_readiness",
			{
				"model_type": "Submission",
				"model_code": "DSM-WH004-TEST-V1",
				"status": "Placeholder",
				"deferred_reason": "Deferred to Tender Management v2 (WH-004 test).",
				"blocking_for_publication": 1,
				"components_summary": '{"rows": 0}',
			},
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(len(reloaded.derived_model_readiness), 1)
			row = reloaded.derived_model_readiness[0]
			self.assertEqual(row.model_type, "Submission")
			self.assertEqual(row.model_code, "DSM-WH004-TEST-V1")
			self.assertEqual(row.status, "Placeholder")
			self.assertIn("Tender Management v2", row.deferred_reason or "")
			self.assertEqual(int(row.blocking_for_publication or 0), 1)
			self.assertEqual(row.validation_status, "Not Checked")
			self.assertEqual(row.version, "V1")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh004_placeholder_missing_deferred_reason_raises(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-004 Deferred Reason Negative"
		doc.tender_reference = "WH004-NEG-001"
		doc.append(
			"derived_model_readiness",
			{
				"model_type": "Missing",
				"model_code": "MISS-WH004-001",
				"status": "Missing",
				"deferred_reason": "",
			},
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)

	def test_wh004_generated_allows_empty_deferred_reason(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-004 Generated Row"
		doc.tender_reference = "WH004-GEN-001"
		doc.append(
			"derived_model_readiness",
			{
				"model_type": "Evaluation",
				"model_code": "DEM-WH004-GEN-001",
				"status": "Generated",
				"deferred_reason": "",
			},
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(reloaded.derived_model_readiness[0].status, "Generated")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
