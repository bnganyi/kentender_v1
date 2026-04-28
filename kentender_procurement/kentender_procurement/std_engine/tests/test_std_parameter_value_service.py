from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.instance_creation_service import create_std_instance
from kentender_procurement.std_engine.services.parameter_value_service import set_std_parameter_value


def _delete_if_exists(doctype: str, field: str, value: str):
	if doctype == "STD Instance Parameter Value" and not frappe.db.table_exists("STD Instance Parameter Value"):
		return
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDParameterValueService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Generated Output", "output_code", "STDOUT-0403-1"),
			("STD Instance Parameter Value", "instance_parameter_value_code", "SPV-0403-1"),
			("STD Instance", "tender_code", "TND-0403-1"),
			("STD Audit Event", "object_code", "TND-0403-1"),
			("STD Parameter Definition", "parameter_code", "STD-PARAM-0403-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0403-ACTIVE"),
			("STD Template Version", "version_code", "STDTV-0403-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0403-1"),
			("STD Part Definition", "part_code", "STD-PART-0403-1"),
			("STD Template Family", "template_code", "STD-WORKS-0403"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0403"),
		):
			_delete_if_exists(dt, field, value)

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_0403",
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
				"template_code": "STD-WORKS-0403",
				"template_title": "0403 Family",
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
				"version_code": "STDTV-0403-ACTIVE",
				"template_code": "STD-WORKS-0403",
				"version_label": "0403 Active",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_0403",
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
				"part_code": "STD-PART-0403-1",
				"version_code": "STDTV-0403-ACTIVE",
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
				"section_code": "STD-SEC-0403-1",
				"version_code": "STDTV-0403-ACTIVE",
				"part_code": "STD-PART-0403-1",
				"section_number": "1.1",
				"section_title": "Tender Data",
				"section_classification": "Core",
				"editability": "Parameter Only",
				"is_mandatory": 1,
				"is_supplier_facing": 1,
				"is_contract_facing": 0,
				"order_index": 1,
				"source_document_code": "DOC1_WORKS_0403",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": "STD-PARAM-0403-1",
				"version_code": "STDTV-0403-ACTIVE",
				"section_code": "STD-SEC-0403-1",
				"label": "Bid Validity Days",
				"parameter_group": "TDS",
				"data_type": "Int",
				"allowed_values": "[30,60,90]",
				"value_resolution_stage": "Tender Configuration",
				"required": 1,
				"drives_bundle": 0,
				"drives_dsm": 0,
				"drives_dom": 0,
				"drives_dem": 1,
				"drives_dcm": 0,
				"addendum_change_requires_acknowledgement": 0,
				"addendum_change_requires_deadline_review": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-0403-ACTIVE",
				"version_code": "STDTV-0403-ACTIVE",
				"profile_title": "Works Building Civil",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"allowed_methods": "[\"Open Tender\"]",
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

		resp = create_std_instance(
			tender_code="TND-0403-1",
			template_version_code="STDTV-0403-ACTIVE",
			profile_code="WORKS-PROFILE-0403-ACTIVE",
			tender_context={"procurement_category": "Works", "procurement_method": "Open Tender"},
			actor="Administrator",
		)
		self.instance_code = resp["instance_code"]
		frappe.get_doc(
			{
				"doctype": "STD Generated Output",
				"output_code": "STDOUT-0403-1",
				"instance_code": self.instance_code,
				"output_type": "DEM",
				"version_number": 1,
				"status": "Current",
				"source_template_version_code": "STDTV-0403-ACTIVE",
				"source_profile_code": "WORKS-PROFILE-0403-ACTIVE",
				"generated_by_job_code": "JOB-0403-1",
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("STD Audit Event", {"object_code": ["in", ["TND-0403-1", self.instance_code]]})
		for dt, field, value in (
			("STD Generated Output", "output_code", "STDOUT-0403-1"),
			("STD Instance Parameter Value", "instance_code", self.instance_code),
			("STD Instance", "tender_code", "TND-0403-1"),
			("STD Parameter Definition", "parameter_code", "STD-PARAM-0403-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0403-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0403-1"),
			("STD Part Definition", "part_code", "STD-PART-0403-1"),
			("STD Template Version", "version_code", "STDTV-0403-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0403"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0403"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_required_parameter_value_set_and_invalidation_applied(self):
		resp = set_std_parameter_value(
			instance_code=self.instance_code,
			parameter_code="STD-PARAM-0403-1",
			value=60,
			actor="Administrator",
		)
		self.assertEqual("Invalidated", resp["readiness_status"])
		self.assertIn("STDOUT-0403-1", resp["invalidated_outputs"])
		value_doc = frappe.get_doc(
			"STD Instance Parameter Value",
			{"instance_code": self.instance_code, "parameter_code": "STD-PARAM-0403-1"},
		)
		self.assertEqual("[60, 60]", str([int(value_doc.value_json), 60]))

	def test_invalid_data_type_rejected(self):
		with self.assertRaises((ValidationError, ValueError, TypeError)):
			set_std_parameter_value(
				instance_code=self.instance_code,
				parameter_code="STD-PARAM-0403-1",
				value="not-an-int",
				actor="Administrator",
			)

	def test_post_publication_change_denied(self):
		instance = frappe.get_doc("STD Instance", {"instance_code": self.instance_code})
		frappe.flags.std_transition_service_context = True
		try:
			instance.instance_status = "Published Locked"
			instance.save(ignore_permissions=True)
		finally:
			frappe.flags.std_transition_service_context = False

		with self.assertRaises(ValidationError):
			set_std_parameter_value(
				instance_code=self.instance_code,
				parameter_code="STD-PARAM-0403-1",
				value=30,
				actor="Administrator",
			)

