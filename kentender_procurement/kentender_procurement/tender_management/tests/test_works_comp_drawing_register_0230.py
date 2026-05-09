# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0230 — WorksDrawingRegisterService + StdInstanceDrawingRegisterService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_drawing_register_0230
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)


class TestWorksCompDrawingRegister0230(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_procurement_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0230 Test Tender"
		doc.tender_reference = "WORKSCOMP0230-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("Procurement Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def _valid_row_payload(self) -> dict:
		return {
			"drawing_code": "DWG-001",
			"title": "Floor plan — Level 1",
			"revision": "C",
			"file_reference": "/files/plans/level1.pdf",
			"section_code": "DRAWINGS",
			"classification": "Supplier Facing",
			"issue_status": "Current",
		}

	def test_works_comp_0230_validate_empty_register(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("DRAWING_REGISTER_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_optional_register_via_configuration_json(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			td = frappe.get_doc("Procurement Tender", tender)
			td.configuration_json = json.dumps({"WORKS.DRAWING_REGISTER_OPTIONAL": True})
			td.save(ignore_permissions=True)
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertNotIn("DRAWING_REGISTER_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_validate_file_missing(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.append(
				"drawing_register",
				{
					"register_row_code": f"STD-DR-{frappe.generate_hash(length=10)}",
					"drawing_code": "DWG-NOF",
					"title": "No file",
					"revision": "1",
					"file_reference": "",
					"section_code": "DRAWINGS",
					"classification": "Supplier Facing",
					"issue_status": "Current",
				},
			)
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)

			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("DRAWING_FILE_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_validate_revision_missing(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.append(
				"drawing_register",
				{
					"register_row_code": f"STD-DR-{frappe.generate_hash(length=10)}",
					"drawing_code": "DWG-NOR",
					"title": "No rev",
					"revision": "",
					"file_reference": "/files/x.pdf",
					"section_code": "DRAWINGS",
					"classification": "Supplier Facing",
					"issue_status": "Current",
				},
			)
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)

			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("DRAWING_REVISION_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_validate_invalid_section(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.append(
				"drawing_register",
				{
					"register_row_code": f"STD-DR-{frappe.generate_hash(length=10)}",
					"drawing_code": "DWG-X",
					"title": "Plan",
					"revision": "1",
					"file_reference": "/f.pdf",
					"section_code": "SPECIFICATIONS",
					"classification": "Supplier Facing",
					"issue_status": "Current",
				},
			)
			doc.save(ignore_permissions=True)

			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("DRAWING_SECTION_INVALID", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_validate_duplicate_rows(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			base = {
				"drawing_code": "DWG-DUP",
				"title": "Dup test",
				"revision": "A",
				"file_reference": "/files/a.pdf",
				"section_code": "DRAWINGS",
				"classification": "Supplier Facing",
				"issue_status": "Current",
			}
			doc.append(
				"drawing_register",
				{"register_row_code": f"STD-DR-{frappe.generate_hash(length=10)}", **base},
			)
			doc.append(
				"drawing_register",
				{"register_row_code": f"STD-DR-{frappe.generate_hash(length=10)}", **base},
			)
			doc.save(ignore_permissions=True)

			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("DRAWING_DUPLICATE_REVISION", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_save_payload_duplicate_throws(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			row = self._valid_row_payload()
			with self.assertRaises(frappe.ValidationError):
				WorksDrawingRegisterService.save_drawing_register(
					si.name,
					{"drawings": [row, dict(row)]},
				)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_save_validate_happy_path(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksDrawingRegisterService.save_drawing_register(
				si.name,
				{"drawings": [self._valid_row_payload()]},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(len(doc.drawing_register or []), 1)
			r = doc.drawing_register[0]
			self.assertEqual((r.drawing_code or "").strip(), "DWG-001")
			self.assertEqual((r.section_code or "").strip(), "DRAWINGS")

			out = WorksDrawingRegisterService.validate_drawing_register(si.name)
			self.assertTrue(out["valid"], out)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_attach_file_updates_row(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksDrawingRegisterService.save_drawing_register(
				si.name,
				{"drawings": [self._valid_row_payload()]},
			)
			WorksDrawingRegisterService.attach_drawing_file(
				si.name,
				"DWG-001",
				revision="C",
				file_name="level1.pdf",
				file_reference="/files/plans/level1-updated.pdf",
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual((doc.drawing_register[0].file_reference or "").strip(), "/files/plans/level1-updated.pdf")
			self.assertEqual((doc.drawing_register[0].file_name or "").strip(), "level1.pdf")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0230_substantive_edit_marks_stale(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			row = self._valid_row_payload()
			WorksDrawingRegisterService.save_drawing_register(si.name, {"drawings": [row]})
			inst = frappe.get_doc("Tender STD Instance", si.name)
			stale_after_first = parse_outputs_stale_flags(inst)
			self.assertIn("Bundle", stale_after_first)

			row2 = dict(row)
			row2["title"] = "Floor plan — Level 1 (revised detail)"
			WorksDrawingRegisterService.save_drawing_register(si.name, {"drawings": [row2]})
			inst2 = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(len(inst2.drawing_register or []), 1)
			raw = (inst2.outputs_stale_flags or "").strip()
			self.assertTrue(raw)
			parsed = json.loads(raw)
			self.assertIsInstance(parsed, list)
			self.assertIn("Bundle", parsed)
		finally:
			self._delete_tender(tender)
