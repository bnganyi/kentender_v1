from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.instance_creation_service import create_std_instance


def _delete_if_exists(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDInstanceCreationService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Instance", "tender_code", "TND-0402-1"),
			("STD Audit Event", "object_code", "TND-0402-1"),
			("STD Parameter Definition", "parameter_code", "STD-PARAM-0402-1"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0402-1"),
			("STD BOQ Definition", "boq_definition_code", "STD-BOQ-0402-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0402-ACTIVE"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0402-INCOMP"),
			("STD Template Version", "version_code", "STDTV-0402-ACTIVE"),
			("STD Template Version", "version_code", "STDTV-0402-INACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0402-1"),
			("STD Part Definition", "part_code", "STD-PART-0402-1"),
			("STD Template Family", "template_code", "STD-WORKS-0402"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0402"),
		):
			_delete_if_exists(dt, field, value)

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_0402",
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
				"template_code": "STD-WORKS-0402",
				"template_title": "0402 Family",
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
				"version_code": "STDTV-0402-ACTIVE",
				"template_code": "STD-WORKS-0402",
				"version_label": "0402 Active",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_0402",
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
				"doctype": "STD Template Version",
				"version_code": "STDTV-0402-INACTIVE",
				"template_code": "STD-WORKS-0402",
				"version_label": "0402 Suspended",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_0402",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"version_status": "Suspended",
				"legal_review_status": "Approved",
				"policy_review_status": "Approved",
				"structure_validation_status": "Pass",
				"is_current_active_version": 0,
				"immutable_after_activation": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Part Definition",
				"part_code": "STD-PART-0402-1",
				"version_code": "STDTV-0402-ACTIVE",
				"part_number": "I",
				"part_title": "Instructions",
				"order_index": 1,
				"is_supplier_facing": 1,
				"is_contract_facing": 0,
				"is_mandatory": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Section Definition",
				"section_code": "STD-SEC-0402-1",
				"version_code": "STDTV-0402-ACTIVE",
				"part_code": "STD-PART-0402-1",
				"section_number": "1.1",
				"section_title": "Tender Data",
				"section_classification": "Core",
				"editability": "Parameter Only",
				"is_mandatory": 1,
				"is_supplier_facing": 1,
				"is_contract_facing": 0,
				"order_index": 1,
				"source_document_code": "DOC1_WORKS_0402",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": "STD-PARAM-0402-1",
				"version_code": "STDTV-0402-ACTIVE",
				"section_code": "STD-SEC-0402-1",
				"label": "Bid Validity Days",
				"parameter_group": "TDS",
				"data_type": "Int",
				"value_resolution_stage": "Tender Configuration",
				"required": 1,
				"drives_bundle": 0,
				"drives_dsm": 0,
				"drives_dom": 0,
				"drives_dem": 0,
				"drives_dcm": 0,
				"addendum_change_requires_acknowledgement": 0,
				"addendum_change_requires_deadline_review": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Works Requirement Component Definition",
				"component_code": "STD-COMP-0402-1",
				"version_code": "STDTV-0402-ACTIVE",
				"section_code": "STD-SEC-0402-1",
				"component_title": "Site Information",
				"component_type": "Narrative",
				"is_required": 1,
				"supports_structured_text": 1,
				"supports_table_data": 0,
				"supports_attachments": 0,
				"attachment_required": 0,
				"drives_dsm": 0,
				"drives_dem": 0,
				"drives_dcm": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD BOQ Definition",
				"boq_definition_code": "STD-BOQ-0402-1",
				"version_code": "STDTV-0402-ACTIVE",
				"section_code": "STD-SEC-0402-1",
				"pricing_model": "Admeasurement",
				"quantity_owner": "Procuring Entity",
				"supplier_input_mode": "Rate Only",
				"amount_computation_rule": "qty*rate",
				"total_computation_rule": "sum(amount)",
				"arithmetic_correction_stage": "Evaluation",
				"allows_provisional_sums": 0,
				"allows_dayworks": 0,
				"is_required_for_readiness": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-0402-ACTIVE",
				"version_code": "STDTV-0402-ACTIVE",
				"profile_title": "Works Building Civil",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"allowed_methods": "[\"Open Tender\"]",
				"allowed_contract_types": "[\"Lump Sum\"]",
				"profile_status": "Active",
				"requires_boq": 1,
				"requires_drawings": 0,
				"requires_specifications": 0,
				"requires_site_information": 0,
				"requires_hse_requirements": 0,
				"requires_environmental_social_requirements": 0,
				"supports_lots": 0,
				"supports_alternative_tenders": 0,
				"supports_margin_of_preference": 0,
				"supports_reservations": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-0402-INCOMP",
				"version_code": "STDTV-0402-ACTIVE",
				"profile_title": "Works Restricted",
				"procurement_category": "Works",
				"works_profile_type": "Road Works",
				"allowed_methods": "[\"Restricted Tender\"]",
				"profile_status": "Active",
				"requires_boq": 0,
				"requires_drawings": 0,
				"requires_specifications": 0,
				"requires_site_information": 0,
				"requires_hse_requirements": 0,
				"requires_environmental_social_requirements": 0,
				"supports_lots": 0,
				"supports_alternative_tenders": 0,
				"supports_margin_of_preference": 0,
				"supports_reservations": 0,
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("STD Audit Event", {"object_code": ["like", "TND-0402-%"]})
		for dt, field, value in (
			("STD Instance", "tender_code", "TND-0402-1"),
			("STD Parameter Definition", "parameter_code", "STD-PARAM-0402-1"),
			("STD Works Requirement Component Definition", "component_code", "STD-COMP-0402-1"),
			("STD BOQ Definition", "boq_definition_code", "STD-BOQ-0402-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0402-INCOMP"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0402-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0402-1"),
			("STD Part Definition", "part_code", "STD-PART-0402-1"),
			("STD Template Version", "version_code", "STDTV-0402-INACTIVE"),
			("STD Template Version", "version_code", "STDTV-0402-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0402"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0402"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_create_instance_initializes_required_placeholders(self):
		resp = create_std_instance(
			tender_code="TND-0402-1",
			template_version_code="STDTV-0402-ACTIVE",
			profile_code="WORKS-PROFILE-0402-ACTIVE",
			tender_context={
				"procurement_category": "Works",
				"procurement_method": "Open Tender",
				"works_profile_type": "Building Civil",
				"contract_type": "Lump Sum",
			},
			actor="Administrator",
		)
		instance = frappe.get_doc("STD Instance", {"instance_code": resp["instance_code"]})
		self.assertEqual("Draft", instance.instance_status)
		self.assertEqual("Not Run", instance.readiness_status)
		self.assertEqual(1, len(resp["section_placeholders"]))
		self.assertEqual(1, len(resp["parameter_placeholders"]))
		self.assertEqual(1, len(resp["works_requirement_placeholders"]))
		self.assertEqual(1, len(resp["boq_placeholders"]))
		self.assertTrue(
			frappe.db.exists(
				"STD Audit Event",
				{"event_type": "STD_INSTANCE_CREATED", "object_code": instance.instance_code},
			)
		)

	def test_inactive_template_version_rejected(self):
		with self.assertRaises(ValidationError):
			create_std_instance(
				tender_code="TND-0402-1",
				template_version_code="STDTV-0402-INACTIVE",
				profile_code="WORKS-PROFILE-0402-ACTIVE",
				tender_context={"procurement_category": "Works", "procurement_method": "Open Tender"},
				actor="Administrator",
			)

	def test_incompatible_profile_rejected(self):
		with self.assertRaises(ValidationError):
			create_std_instance(
				tender_code="TND-0402-1",
				template_version_code="STDTV-0402-ACTIVE",
				profile_code="WORKS-PROFILE-0402-INCOMP",
				tender_context={
					"procurement_category": "Works",
					"procurement_method": "Open Tender",
					"works_profile_type": "Building Civil",
				},
				actor="Administrator",
			)

	def test_duplicate_current_instance_blocked_without_supersession_path(self):
		create_std_instance(
			tender_code="TND-0402-1",
			template_version_code="STDTV-0402-ACTIVE",
			profile_code="WORKS-PROFILE-0402-ACTIVE",
			tender_context={"procurement_category": "Works", "procurement_method": "Open Tender"},
			actor="Administrator",
		)
		with self.assertRaises(ValidationError):
			create_std_instance(
				tender_code="TND-0402-1",
				template_version_code="STDTV-0402-ACTIVE",
				profile_code="WORKS-PROFILE-0402-ACTIVE",
				tender_context={"procurement_category": "Works", "procurement_method": "Open Tender"},
				actor="Administrator",
			)

