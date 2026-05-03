# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WH-003 — ``Tender Section Attachment`` child DocType + ``section_attachments`` on tender (doc 5 §9, §7.1).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_tender_hardening_wh003
"""

from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

_ATTACHMENT_TYPE_OPTIONS = (
	"Drawing\nTechnical Specification\nSite Photo\nPermit\n"
	"Geotechnical Report\nESHS Document\nOther"
)

_STATUS_OPTIONS = "Draft\nActive\nSuperseded"

_WH003_CHILD_FIELDS: tuple[tuple[str, str, int, str | None], ...] = (
	("attachment_code", "Data", 1, None),
	("file_name", "Data", 1, None),
	("file_url", "Data", 0, None),
	("section_code", "Data", 1, None),
	("component_code", "Data", 1, None),
	("attachment_type", "Select", 1, _ATTACHMENT_TYPE_OPTIONS),
	("version", "Data", 1, None),
	("supplier_facing", "Check", 0, None),
	("internal_only", "Check", 0, None),
	("source_hash", "Data", 0, None),
	("status", "Select", 1, _STATUS_OPTIONS),
	("publication_included", "Check", 0, None),
	("notes", "Small Text", 0, None),
)


def _minimal_section_attachment_row(**overrides: object) -> dict[str, object]:
	row: dict[str, object] = {
		"attachment_code": "WH003-A1",
		"file_name": "wh003_metadata_only.pdf",
		"section_code": "SEC-DRAW",
		"component_code": "WRK_DRAWINGS",
		"attachment_type": "Drawing",
		"status": "Active",
		"version": "V1",
		"supplier_facing": 1,
		"internal_only": 0,
	}
	row.update(overrides)
	return row


class TestWorksTenderHardeningWh003(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_wh003_child_meta_fields(self) -> None:
		meta = frappe.get_meta("Tender Section Attachment")
		self.assertEqual(meta.istable, 1)
		for fieldname, fieldtype, reqd, options in _WH003_CHILD_FIELDS:
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

	def test_wh003_procurement_tender_has_section_attachments_table(self) -> None:
		meta = frappe.get_meta("Procurement Tender")
		f = meta.get_field("section_attachments")
		self.assertIsNotNone(f)
		self.assertEqual(f.fieldtype, "Table")
		self.assertEqual(f.options, "Tender Section Attachment")
		self.assertTrue(f.read_only)

	def test_wh003_append_child_row_persists(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-003 Section Attachment Test"
		doc.tender_reference = "WH003-ROW-001"
		doc.append(
			"section_attachments",
			_minimal_section_attachment_row(
				file_url="https://example.invalid/file.pdf",
				source_hash="sha256:abc",
				publication_included=1,
				notes="WH-003 metadata row",
			),
		)
		doc.insert(ignore_permissions=True)
		try:
			reloaded = frappe.get_doc("Procurement Tender", doc.name)
			self.assertEqual(len(reloaded.section_attachments), 1)
			row = reloaded.section_attachments[0]
			self.assertEqual(row.attachment_code, "WH003-A1")
			self.assertEqual(row.file_name, "wh003_metadata_only.pdf")
			self.assertEqual(row.file_url, "https://example.invalid/file.pdf")
			self.assertEqual(row.section_code, "SEC-DRAW")
			self.assertEqual(row.component_code, "WRK_DRAWINGS")
			self.assertEqual(row.attachment_type, "Drawing")
			self.assertEqual(row.status, "Active")
			self.assertEqual(row.version, "V1")
			self.assertEqual(int(row.supplier_facing or 0), 1)
			self.assertEqual(int(row.internal_only or 0), 0)
			self.assertEqual(row.source_hash, "sha256:abc")
			self.assertEqual(int(row.publication_included or 0), 1)
			self.assertEqual(row.notes, "WH-003 metadata row")
		finally:
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)

	def test_wh003_supplier_facing_and_internal_only_conflict(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WH-003 Conflict Test"
		doc.tender_reference = "WH003-CONFLICT-001"
		doc.append(
			"section_attachments",
			_minimal_section_attachment_row(supplier_facing=1, internal_only=1),
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)
