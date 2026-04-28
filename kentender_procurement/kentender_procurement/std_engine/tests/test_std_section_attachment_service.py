from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.instance_creation_service import create_std_instance
from kentender_procurement.std_engine.services.section_attachment_service import add_std_section_attachment


def _delete_if_exists(doctype: str, field: str, value: str):
	if doctype == "STD Section Attachment" and not frappe.db.table_exists("STD Section Attachment"):
		return
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDSectionAttachmentService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Generated Output", "output_code", "STDOUT-0404-1"),
			("STD Section Attachment", "attachment_code", "SATT-0404-1"),
			("STD Instance", "tender_code", "TND-0404-1"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0404-VII"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0404-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0404-VI"),
			("STD Section Definition", "section_code", "STD-SEC-0404-VII"),
			("STD Part Definition", "part_code", "STD-PART-0404-1"),
			("STD Template Version", "version_code", "STDTV-0404-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0404"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0404"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.delete("STD Audit Event", {"object_code": ["like", "STDINST-%"]})

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_0404",
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
				"template_code": "STD-WORKS-0404",
				"template_title": "0404 Family",
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
				"version_code": "STDTV-0404-ACTIVE",
				"template_code": "STD-WORKS-0404",
				"version_label": "0404 Active",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_0404",
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
				"part_code": "STD-PART-0404-1",
				"version_code": "STDTV-0404-ACTIVE",
				"part_number": "II",
				"part_title": "Employer's Requirements",
				"order_index": 2,
				"is_supplier_facing": 1,
				"is_contract_facing": 1,
				"is_mandatory": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Section Definition",
				"section_code": "STD-SEC-0404-VI",
				"version_code": "STDTV-0404-ACTIVE",
				"part_code": "STD-PART-0404-1",
				"section_number": "VI",
				"section_title": "Specifications",
				"section_classification": "Core",
				"editability": "Structured Editable",
				"is_mandatory": 1,
				"is_supplier_facing": 1,
				"is_contract_facing": 1,
				"order_index": 6,
				"source_document_code": "DOC1_WORKS_0404",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Section Definition",
				"section_code": "STD-SEC-0404-VII",
				"version_code": "STDTV-0404-ACTIVE",
				"part_code": "STD-PART-0404-1",
				"section_number": "VII",
				"section_title": "Drawings",
				"section_classification": "Core",
				"editability": "Structured Editable",
				"is_mandatory": 1,
				"is_supplier_facing": 1,
				"is_contract_facing": 1,
				"order_index": 7,
				"source_document_code": "DOC1_WORKS_0404",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Works Requirement Component Definition",
				"component_code": "STD-COMP-0404-VII",
				"version_code": "STDTV-0404-ACTIVE",
				"section_code": "STD-SEC-0404-VII",
				"component_title": "Drawing Register",
				"component_type": "Attachment Register",
				"is_required": 1,
				"supports_structured_text": 0,
				"supports_table_data": 1,
				"supports_attachments": 1,
				"attachment_required": 1,
				"drives_dsm": 1,
				"drives_dem": 1,
				"drives_dcm": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-0404-ACTIVE",
				"version_code": "STDTV-0404-ACTIVE",
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
		resp = create_std_instance(
			tender_code="TND-0404-1",
			template_version_code="STDTV-0404-ACTIVE",
			profile_code="WORKS-PROFILE-0404-ACTIVE",
			tender_context={"procurement_category": "Works", "procurement_method": "Open Tender"},
			actor="Administrator",
		)
		self.instance_code = resp["instance_code"]
		frappe.get_doc(
			{
				"doctype": "STD Generated Output",
				"output_code": "STDOUT-0404-1",
				"instance_code": self.instance_code,
				"output_type": "DSM",
				"version_number": 1,
				"status": "Current",
				"source_template_version_code": "STDTV-0404-ACTIVE",
				"source_profile_code": "WORKS-PROFILE-0404-ACTIVE",
				"generated_by_job_code": "JOB-0404-1",
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("STD Audit Event", {"object_code": ["in", [self.instance_code, "TND-0404-1"]]})
		for dt, field, value in (
			("STD Generated Output", "output_code", "STDOUT-0404-1"),
			("STD Section Attachment", "instance_code", self.instance_code),
			("STD Instance", "tender_code", "TND-0404-1"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0404-VII"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0404-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0404-VII"),
			("STD Section Definition", "section_code", "STD-SEC-0404-VI"),
			("STD Part Definition", "part_code", "STD-PART-0404-1"),
			("STD Template Version", "version_code", "STDTV-0404-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0404"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0404"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_drawings_and_specifications_can_be_attached_to_bound_sections(self):
		drawings = add_std_section_attachment(
			instance_code=self.instance_code,
			section_code="STD-SEC-0404-VII",
			file_reference="/files/section-vii-drawings.pdf",
			classification="Drawing",
			actor="Administrator",
			component_code="STD-COMP-0404-VII",
		)
		specs = add_std_section_attachment(
			instance_code=self.instance_code,
			section_code="STD-SEC-0404-VI",
			file_reference="/files/section-vi-specs.pdf",
			classification="Specification",
			actor="Administrator",
		)
		self.assertEqual("Invalidated", drawings["readiness_status"])
		self.assertEqual("Invalidated", specs["readiness_status"])
		self.assertTrue(drawings["file_hash"])
		self.assertTrue(specs["file_hash"])

	def test_generic_unbound_attachment_rejected(self):
		with self.assertRaises(ValidationError):
			add_std_section_attachment(
				instance_code=self.instance_code,
				section_code="UNKNOWN-SECTION",
				file_reference="/files/generic-attachment.pdf",
				classification="Supporting",
				actor="Administrator",
			)

	def test_published_attachment_cannot_be_replaced_without_addendum(self):
		seed = add_std_section_attachment(
			instance_code=self.instance_code,
			section_code="STD-SEC-0404-VII",
			file_reference="/files/original-drawing.pdf",
			classification="Drawing",
			actor="Administrator",
			component_code="STD-COMP-0404-VII",
		)
		attachment = frappe.get_doc("STD Section Attachment", {"attachment_code": seed["attachment_code"]})
		attachment.status = "Published"
		attachment.save(ignore_permissions=True)

		with self.assertRaises(ValidationError):
			add_std_section_attachment(
				instance_code=self.instance_code,
				section_code="STD-SEC-0404-VII",
				file_reference="/files/replaced-drawing.pdf",
				classification="Drawing",
				actor="Administrator",
				component_code="STD-COMP-0404-VII",
			)

