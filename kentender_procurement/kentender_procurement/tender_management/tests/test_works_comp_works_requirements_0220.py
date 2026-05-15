# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0220 — WorksRequirementsCompletionService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_works_requirements_0220
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
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)


class TestWorksCompWorksRequirements0220(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tm2_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0220 Test Tender"
		doc.tender_reference = "WORKSCOMP0220-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("TM2 Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def test_works_comp_0220_validate_missing_specifications(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksRequirementsCompletionService.validate_works_requirements(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("WORKS_SPECIFICATIONS_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0220_save_minimal_valid(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksRequirementsCompletionService.save_works_requirements(
				si.name,
				{"specifications": {"structured_summary": "Renovation of outpatient block..."}},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			found = {(r.component_code or "").strip(): (r.structured_text or "").strip() for r in doc.works_requirements}
			self.assertEqual(found.get("SPECIFICATIONS"), "Renovation of outpatient block...")
			out = WorksRequirementsCompletionService.validate_works_requirements(si.name)
			self.assertTrue(out["valid"], out)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0220_profile_requires_hse_when_configuration_flag_set(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			td = frappe.get_doc("TM2 Tender", tender)
			td.configuration_json = json.dumps({"WORKS.REQUIRE_HSE_REQUIREMENTS": True})
			td.save(ignore_permissions=True)
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"SPECIFICATIONS",
				structured_text="Specs without HSE row",
				structured_data=None,
				requirement_status="Complete",
				attachment_required=False,
				attachment_status="Not Required",
				drives_bundle=True,
				drives_dsm=True,
				drives_dem=True,
				drives_dcm=True,
				ignore_publication_lock=False,
			)
			out = WorksRequirementsCompletionService.validate_works_requirements(si.name)
			self.assertIn("WORKS_HSE_REQUIREMENTS_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0220_attachment_reference_not_bound(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(frappe.ValidationError):
				WorksRequirementsCompletionService.save_works_requirements(
					si.name,
					{
						"specifications": {
							"structured_summary": "Scope text",
							"attachments": ["ATT-MISSING-REF"],
						},
					},
				)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0220_validate_lists_unbound_attachment(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"SPECIFICATIONS",
				structured_text="Scope",
				structured_data='{"attachment_codes": ["ORPHAN-ATT"], "wr_pack_version": 1}',
				requirement_status="Complete",
				attachment_required=True,
				attachment_status="Missing",
				drives_bundle=True,
				drives_dsm=True,
				drives_dem=True,
				drives_dcm=True,
				ignore_publication_lock=False,
			)
			out = WorksRequirementsCompletionService.validate_works_requirements(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("WORKS_ATTACHMENT_NOT_SECTION_BOUND", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0220_attach_file_smoke(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksRequirementsCompletionService.save_works_requirements(
				si.name,
				{"specifications": {"structured_summary": "Building works"}},
			)
			WorksRequirementsCompletionService.attach_works_requirement_file(
				si.name,
				"SPECIFICATIONS",
				file_name="spec.pdf",
				file_reference="/files/spec.pdf",
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			self.assertTrue(len(doc.section_attachments or []) >= 1)
			ac = doc.section_attachments[-1].attachment_code
			self.assertTrue(ac)
			self.assertEqual((doc.section_attachments[-1].section_code or "").strip(), "SPECIFICATIONS")
			self.assertEqual((doc.section_attachments[-1].component_code or "").strip(), "SPECIFICATIONS")

			WorksRequirementsCompletionService.save_works_requirements(
				si.name,
				{
					"specifications": {
						"structured_summary": "Building works",
						"attachments": [ac],
					},
				},
			)
			out = WorksRequirementsCompletionService.validate_works_requirements(si.name)
			self.assertTrue(out["valid"], out)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0220_nested_flags(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksRequirementsCompletionService.save_works_requirements(
				si.name,
				{
					"specifications": {"structured_summary": "Works scope"},
					"method_statement_required": True,
					"work_programme_required": False,
				},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			ccs = {(r.component_code or "").strip() for r in doc.works_requirements}
			self.assertIn("METHOD_STATEMENT", ccs)
			self.assertIn("WORK_PROGRAMME", ccs)
			out = WorksRequirementsCompletionService.validate_works_requirements(si.name)
			self.assertTrue(out["valid"], out)
		finally:
			self._delete_tender(tender)
