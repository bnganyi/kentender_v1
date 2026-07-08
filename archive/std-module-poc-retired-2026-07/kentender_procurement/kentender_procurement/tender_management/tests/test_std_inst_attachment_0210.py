# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0210 — section-bound attachments on ``Tender STD Instance``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_attachment_0210
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.attachment import StdInstanceAttachmentService
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TestStdInstAttachment0210(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0210 Test Tender"
		doc.tender_reference = "STDINST0210-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def test_std_inst_0210_attach_file_to_section(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceAttachmentService.attach_file_to_section(
				si.name,
				"SECTION_VI",
				"spec.pdf",
				"/files/spec.pdf",
				"Supplier Facing",
				component_code="COMP-A",
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(len(doc.section_attachments), 1)
			row = doc.section_attachments[0]
			self.assertTrue(row.attachment_code.startswith("STD-ATT-"))
			self.assertEqual(row.section_code, "SECTION_VI")
			self.assertEqual(row.version_number, 1)
			self.assertEqual(row.status, "Draft")
			out = StdInstanceAttachmentService.validate_attachment_requirements(si.name)
			self.assertTrue(out["ok"])
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0210_unbound_section_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceAttachmentService.attach_file_to_section(
					si.name,
					"  ",
					"f.pdf",
					"/files/f.pdf",
				)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.append(
				"section_attachments",
				{
					"attachment_code": "STD-ATT-manualbad",
					"section_code": "",
					"file_reference": "/files/x.pdf",
					"file_name": "x.pdf",
					"classification": "Internal Only",
					"version_number": 1,
					"status": "Draft",
				},
			)
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0210_replace_through_addendum(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceAttachmentService.attach_file_to_section(
				si.name,
				"S1",
				"v1.pdf",
				"/files/v1.pdf",
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			old_code = doc.section_attachments[0].attachment_code
			StdInstanceAttachmentService.replace_attachment_through_addendum(
				si.name,
				old_code,
				"v2.pdf",
				"/files/v2.pdf",
				"ADDM-001",
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(len(doc.section_attachments), 2)
			by_code = {r.attachment_code: r for r in doc.section_attachments}
			self.assertEqual(by_code[old_code].status, "Superseded")
			new_rows = [r for r in doc.section_attachments if r.supersedes_attachment_code == old_code]
			self.assertEqual(len(new_rows), 1)
			self.assertEqual(new_rows[0].version_number, 2)
			self.assertEqual(new_rows[0].status, "Draft")
			self.assertEqual(new_rows[0].source_addendum_code, "ADDM-001")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0210_published_row_immutable(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceAttachmentService.attach_file_to_section(
				si.name,
				"S-PUB",
				"locked.pdf",
				"/files/locked.pdf",
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.section_attachments[0].status = "Published"
			doc.save(ignore_permissions=True)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.section_attachments[0].file_reference = "/files/tampered.pdf"
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0210_publication_instance_lock(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			name = si.name
			for target in (
				"In Configuration",
				"Ready for Publication",
				"Locked for Approval",
				"Published Locked",
			):
				si = StdInstanceStateService.apply_transition(name, target, ignore_permissions=True)
				name = si.name
			with self.assertRaises(frappe.ValidationError):
				StdInstanceAttachmentService.attach_file_to_section(
					name,
					"S2",
					"a.pdf",
					"/files/a.pdf",
					ignore_publication_lock=False,
				)
			StdInstanceAttachmentService.attach_file_to_section(
				name,
				"S2",
				"a.pdf",
				"/files/a.pdf",
				ignore_publication_lock=True,
			)
			doc = frappe.get_doc("Tender STD Instance", name)
			self.assertTrue(any(r.section_code == "S2" for r in doc.section_attachments))
		finally:
			self._cleanup_tender(tender)
