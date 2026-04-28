from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.boq_instance_service import (
	add_boq_bill,
	add_boq_item,
	create_or_initialize_boq_instance,
	update_boq_item,
	validate_boq_instance,
)
from kentender_procurement.std_engine.services.instance_creation_service import create_std_instance


def _delete_if_exists(doctype: str, field: str, value: str):
	if doctype in {"STD BOQ Instance", "STD BOQ Bill Instance", "STD BOQ Item Instance"} and not frappe.db.table_exists(doctype):
		return
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDBOQInstanceService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Generated Output", "output_code", "STDOUT-0502-1"),
			("STD BOQ Item Instance", "item_instance_code", "SBII-0502-1"),
			("STD BOQ Bill Instance", "bill_instance_code", "SBBI-0502-1"),
			("STD BOQ Instance", "instance_code", "STDINST-0502-X"),
			("STD Instance", "tender_code", "TND-0502-1"),
			("STD BOQ Item Schema Definition", "schema_field_code", "STD-BOQ-SCH-0502-QTY"),
			("STD BOQ Definition", "boq_definition_code", "STD-BOQ-0502-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0502-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0502-V"),
			("STD Part Definition", "part_code", "STD-PART-0502-1"),
			("STD Template Version", "version_code", "STDTV-0502-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0502"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0502"),
		):
			_delete_if_exists(dt, field, value)

		frappe.get_doc({"doctype": "Source Document Registry", "source_document_code": "DOC1_WORKS_0502", "source_document_title": "STD", "issuing_authority": "PPRA", "source_revision_label": "Rev", "procurement_category": "Works", "legal_use_status": "Approved for Use", "status": "Active"}).insert()
		frappe.get_doc({"doctype": "STD Template Family", "template_code": "STD-WORKS-0502", "template_title": "0502 Family", "issuing_authority": "PPRA", "procurement_category": "Works", "allowed_procurement_methods": "[\"Open Tender\"]", "family_status": "Active", "is_active_family": 1}).insert()
		frappe.get_doc({"doctype": "STD Template Version", "version_code": "STDTV-0502-ACTIVE", "template_code": "STD-WORKS-0502", "version_label": "0502 Active", "revision_label": "Rev", "source_document_code": "DOC1_WORKS_0502", "issuing_authority": "PPRA", "procurement_category": "Works", "works_profile_type": "Building Civil", "version_status": "Active", "legal_review_status": "Approved", "policy_review_status": "Approved", "structure_validation_status": "Pass", "is_current_active_version": 1, "immutable_after_activation": 1}).insert()
		frappe.get_doc({"doctype": "STD Part Definition", "part_code": "STD-PART-0502-1", "version_code": "STDTV-0502-ACTIVE", "part_number": "V", "part_title": "BOQ", "order_index": 5, "is_supplier_facing": 1, "is_contract_facing": 1, "is_mandatory": 1}).insert()
		frappe.get_doc({"doctype": "STD Section Definition", "section_code": "STD-SEC-0502-V", "version_code": "STDTV-0502-ACTIVE", "part_code": "STD-PART-0502-1", "section_number": "V", "section_title": "Bills of Quantities", "section_classification": "Core", "editability": "Structured Editable", "is_mandatory": 1, "is_supplier_facing": 1, "is_contract_facing": 1, "order_index": 5, "source_document_code": "DOC1_WORKS_0502"}).insert()
		frappe.get_doc({"doctype": "STD BOQ Definition", "boq_definition_code": "STD-BOQ-0502-1", "version_code": "STDTV-0502-ACTIVE", "section_code": "STD-SEC-0502-V", "pricing_model": "Admeasurement", "quantity_owner": "Procuring Entity", "supplier_input_mode": "Rate Only", "amount_computation_rule": "qty*rate", "total_computation_rule": "sum(amount)", "arithmetic_correction_stage": "Evaluation", "allows_provisional_sums": 0, "allows_dayworks": 0, "is_required_for_readiness": 1}).insert()
		frappe.get_doc({"doctype": "STD BOQ Item Schema Definition", "schema_field_code": "STD-BOQ-SCH-0502-QTY", "boq_definition_code": "STD-BOQ-0502-1", "field_key": "quantity", "label": "Quantity", "item_owner": "Procuring Entity", "supplier_editable": 0, "required": 1}).insert()
		frappe.get_doc({"doctype": "STD Applicability Profile", "profile_code": "WORKS-PROFILE-0502-ACTIVE", "version_code": "STDTV-0502-ACTIVE", "profile_title": "Works", "procurement_category": "Works", "works_profile_type": "Building Civil", "allowed_methods": "[\"Open Tender\"]", "profile_status": "Active", "requires_boq": 1, "requires_drawings": 0, "requires_specifications": 0, "requires_site_information": 0, "requires_hse_requirements": 0, "requires_environmental_social_requirements": 0, "supports_lots": 0, "supports_alternative_tenders": 0, "supports_margin_of_preference": 0, "supports_reservations": 0}).insert()
		created = create_std_instance("TND-0502-1", "STDTV-0502-ACTIVE", "WORKS-PROFILE-0502-ACTIVE", {"procurement_category": "Works", "procurement_method": "Open Tender"}, "Administrator")
		self.instance_code = created["instance_code"]

	def tearDown(self):
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Instance", "tender_code", "TND-0502-1"),
			("STD BOQ Item Instance", "bill_instance_code", "SBBI-0502-1"),
			("STD BOQ Bill Instance", "boq_instance_code", "SBI-0502-1"),
			("STD BOQ Instance", "instance_code", self.instance_code),
			("STD BOQ Item Schema Definition", "schema_field_code", "STD-BOQ-SCH-0502-QTY"),
			("STD BOQ Definition", "boq_definition_code", "STD-BOQ-0502-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-0502-ACTIVE"),
			("STD Section Definition", "section_code", "STD-SEC-0502-V"),
			("STD Part Definition", "part_code", "STD-PART-0502-1"),
			("STD Template Version", "version_code", "STDTV-0502-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-0502"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_0502"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_bills_and_items_can_be_added(self):
		boq = create_or_initialize_boq_instance(self.instance_code, "Administrator")
		self.assertTrue(boq["boq_instance_code"])
		bill = add_boq_bill(self.instance_code, {"bill_number": "1", "bill_title": "General Items", "bill_type": "Work Items", "order_index": 1}, "Administrator")
		item = add_boq_item(bill["bill_instance_code"], {"item_number": "1.1", "description": "Excavation", "unit": "m3", "quantity": 10, "rate": 100}, "Administrator")
		self.assertEqual(1000.0, item["amount"])

	def test_missing_quantity_blocks_validation(self):
		bill = add_boq_bill(self.instance_code, {"bill_number": "1", "bill_title": "General Items", "bill_type": "Work Items", "order_index": 1}, "Administrator")
		add_boq_item(bill["bill_instance_code"], {"item_number": "1.1", "description": "Excavation", "unit": "m3", "quantity": 10, "rate": 100}, "Administrator")
		item_code = frappe.db.get_value("STD BOQ Item Instance", {"bill_instance_code": bill["bill_instance_code"]}, "item_instance_code")
		frappe.db.set_value("STD BOQ Item Instance", {"item_instance_code": item_code}, "unit", "", update_modified=False)
		validation = validate_boq_instance(self.instance_code)
		self.assertFalse(validation["is_valid"])

	def test_negative_quantity_rejected_and_published_edit_denied(self):
		bill = add_boq_bill(self.instance_code, {"bill_number": "1", "bill_title": "General Items", "bill_type": "Work Items", "order_index": 1}, "Administrator")
		with self.assertRaises(ValidationError):
			add_boq_item(bill["bill_instance_code"], {"item_number": "1.2", "description": "Invalid", "unit": "m3", "quantity": -1, "rate": 10}, "Administrator")
		instance = frappe.get_doc("STD Instance", {"instance_code": self.instance_code})
		frappe.flags.std_transition_service_context = True
		try:
			instance.instance_status = "Published Locked"
			instance.save(ignore_permissions=True)
		finally:
			frappe.flags.std_transition_service_context = False
		with self.assertRaises(ValidationError):
			add_boq_bill(self.instance_code, {"bill_number": "2", "bill_title": "Post Publish", "bill_type": "Work Items", "order_index": 2}, "Administrator")

