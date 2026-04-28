from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.instance_creation_service import create_std_instance
from kentender_procurement.std_engine.services.section_attachment_service import add_std_section_attachment
from kentender_procurement.std_engine.services.works_requirements_service import (
	get_works_requirement_components,
	update_works_requirement_component,
	validate_works_requirements,
)


def _delete_if_exists(doctype: str, field: str, value: str):
	if doctype == "STD Instance Works Requirement Component" and not frappe.db.table_exists(doctype):
		return
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDWorksRequirementsService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Instance", "tender_code", "TND-0501-1"),
			("STD Generated Output", "output_code", "STDOUT-0501-1"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0501-VI"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0501-VII"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0501-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0501-VI"),
			("STD Section Definition", "section_code", "STD-SEC-0501-VII"),
			("STD Part Definition", "part_code", "STD-PART-0501-1"),
			("STD Template Version", "version_code", "STDTV-0501-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0501"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0501"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.delete("STD Audit Event", {"object_code": ["like", "STDINST-%"]})
		frappe.db.delete("STD Audit Event", {"object_code": "TND-0501-1"})

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_0501",
				"source_document_title": "STD Works Source",
				"issuing_authority": "PPRA",
				"source_revision_label": "Rev April 2022",
				"procurement_category": "Works",
				"legal_use_status": "Approved for Use",
				"status": "Active",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Template Family",
				"template_code": "STD-WORKS-0501",
				"template_title": "0501 Family",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"allowed_procurement_methods": "[\"Open Tender\"]",
				"family_status": "Active",
				"is_active_family": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Template Version",
				"version_code": "STDTV-0501-ACTIVE",
				"template_code": "STD-WORKS-0501",
				"version_label": "0501 Active",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_0501",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"version_status": "Active",
				"legal_review_status": "Approved",
				"policy_review_status": "Approved",
				"structure_validation_status": "Pass",
				"is_current_active_version": 1,
				"immutable_after_activation": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Part Definition",
				"part_code": "STD-PART-0501-1",
				"version_code": "STDTV-0501-ACTIVE",
				"part_number": "II",
				"part_title": "Employer Requirements",
				"order_index": 2,
				"is_supplier_facing": 1,
				"is_contract_facing": 1,
				"is_mandatory": 1,
			}
		).insert()
		for code, num, title in (
			("STD-SEC-0501-VI", "VI", "Specifications"),
			("STD-SEC-0501-VII", "VII", "Drawings"),
		):
			frappe.get_doc(
				{
					"doctype": "STD Section Definition",
					"section_code": code,
					"version_code": "STDTV-0501-ACTIVE",
					"part_code": "STD-PART-0501-1",
					"section_number": num,
					"section_title": title,
					"section_classification": "Core",
					"editability": "Structured Editable",
					"is_mandatory": 1,
					"is_supplier_facing": 1,
					"is_contract_facing": 1,
					"order_index": 1,
					"source_document_code": "DOC1_WORKS_0501",
				}
			).insert()
		frappe.get_doc(
			{
				"doctype": "STD Works Requirement Component Definition",
				"component_code": "STD-COMP-0501-VI",
				"version_code": "STDTV-0501-ACTIVE",
				"section_code": "STD-SEC-0501-VI",
				"component_title": "Specifications Component",
				"component_type": "Narrative",
				"is_required": 1,
				"supports_structured_text": 1,
				"supports_table_data": 0,
				"supports_attachments": 1,
				"attachment_required": 0,
				"drives_dsm": 1,
				"drives_dem": 1,
				"drives_dcm": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Works Requirement Component Definition",
				"component_code": "STD-COMP-0501-VII",
				"version_code": "STDTV-0501-ACTIVE",
				"section_code": "STD-SEC-0501-VII",
				"component_title": "Drawings Component",
				"component_type": "Attachment Register",
				"is_required": 1,
				"supports_structured_text": 0,
				"supports_table_data": 1,
				"supports_attachments": 1,
				"attachment_required": 1,
				"drives_dsm": 1,
				"drives_dem": 1,
				"drives_dcm": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-0501-ACTIVE",
				"version_code": "STDTV-0501-ACTIVE",
				"profile_title": "Works Building Civil",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"allowed_methods": "[\"Open Tender\"]",
				"profile_status": "Active",
				"requires_boq": 0,
				"requires_drawings": 1,
				"requires_specifications": 1,
				"requires_site_information": 0,
				"requires_hse_requirements": 0,
				"requires_environmental_social_requirements": 0,
				"supports_lots": 0,
				"supports_alternative_tenders": 0,
				"supports_margin_of_preference": 0,
				"supports_reservations": 0,
			}
		).insert()
		created = create_std_instance(
			tender_code="TND-0501-1",
			template_version_code="STDTV-0501-ACTIVE",
			profile_code="WORKS-PROFILE-0501-ACTIVE",
			tender_context={"procurement_category": "Works", "procurement_method": "Open Tender"},
			actor="Administrator",
		)
		self.instance_code = created["instance_code"]
		frappe.get_doc(
			{
				"doctype": "STD Generated Output",
				"output_code": "STDOUT-0501-1",
				"instance_code": self.instance_code,
				"output_type": "DEM",
				"version_number": 1,
				"status": "Current",
				"source_template_version_code": "STDTV-0501-ACTIVE",
				"source_profile_code": "WORKS-PROFILE-0501-ACTIVE",
				"generated_by_job_code": "JOB-0501-1",
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("STD Audit Event", {"object_code": ["in", [self.instance_code, "TND-0501-1"]]})
		for dt, field, value in (
			("STD Generated Output", "output_code", "STDOUT-0501-1"),
			("STD Section Attachment", "instance_code", self.instance_code),
			("STD Instance Works Requirement Component", "instance_code", self.instance_code),
			("STD Instance", "tender_code", "TND-0501-1"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0501-VII"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0501-VI"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0501-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0501-VII"),
			("STD Section Definition", "section_code", "STD-SEC-0501-VI"),
			("STD Part Definition", "part_code", "STD-PART-0501-1"),
			("STD Template Version", "version_code", "STDTV-0501-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0501"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0501"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_specifications_component_can_be_completed(self):
		rows = get_works_requirement_components(self.instance_code)
		self.assertEqual(2, len(rows))
		resp = update_works_requirement_component(
			self.instance_code,
			"STD-COMP-0501-VI",
			{"structured_text": "Technical specifications completed."},
			"Administrator",
		)
		self.assertEqual("Complete", resp["completion_status"])
		self.assertEqual("Invalidated", resp["readiness_status"])
		self.assertIn("STDOUT-0501-1", resp["invalidated_outputs"])

	def test_drawings_component_requires_attachment_for_readiness(self):
		update_works_requirement_component(
			self.instance_code,
			"STD-COMP-0501-VII",
			{"table_data": [{"drawing_no": "D-001", "title": "Site Plan"}]},
			"Administrator",
		)
		validation_before = validate_works_requirements(self.instance_code)
		reasons = {b["reason"] for b in validation_before["blockers"]}
		self.assertIn("ATTACHMENT_REQUIRED", reasons)

		add_std_section_attachment(
			instance_code=self.instance_code,
			section_code="STD-SEC-0501-VII",
			component_code="STD-COMP-0501-VII",
			file_reference="/files/drawing-register.pdf",
			classification="Drawing",
			actor="Administrator",
		)
		update_works_requirement_component(
			self.instance_code,
			"STD-COMP-0501-VI",
			{"structured_text": "Specs complete"},
			"Administrator",
		)
		validation_after = validate_works_requirements(self.instance_code)
		self.assertTrue(validation_after["is_valid"])
		self.assertEqual("Ready", validation_after["readiness_status"])

	def test_incomplete_required_component_blocks_readiness(self):
		validation = validate_works_requirements(self.instance_code)
		self.assertFalse(validation["is_valid"])
		self.assertEqual("Blocked", validation["readiness_status"])
		self.assertTrue(any(b["reason"] == "REQUIRED_COMPONENT_INCOMPLETE" for b in validation["blockers"]))

