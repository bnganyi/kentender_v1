# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Officer guided field registry — completeness vs ``fields.json`` (doc 8 §13)."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.tender_management.services.officer_guided_field_registry import (
	assert_registry_covers_poc_required_editable_fields,
	doctype_fieldname_for_field_code,
	get_officer_guided_field_specs,
	get_officer_sync_field_codes,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class TestOfficerGuidedFieldRegistryUnit(UnitTestCase):
	def test_registry_covers_all_editable_package_fields(self) -> None:
		assert_registry_covers_poc_required_editable_fields()

	def test_doctype_fieldname_length_within_frappe_limit(self) -> None:
		for spec in get_officer_guided_field_specs():
			self.assertLessEqual(
				len(spec.doctype_fieldname),
				64,
				msg=f"Too long: {spec.field_code} -> {spec.doctype_fieldname}",
			)

	def test_synonym_mapping_for_core_tender_fields(self) -> None:
		self.assertEqual(doctype_fieldname_for_field_code("TENDER.TENDER_NAME"), "tender_title")
		self.assertTrue(get_officer_sync_field_codes())


class TestOfficerGuidedFieldRegistryIntegration(IntegrationTestCase):
	def test_hydration_round_trip_via_sync_updates_works_location(self) -> None:
		import json

		import frappe

		from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
			procurement_tender as controller,
		)

		frappe.set_user("Administrator")
		upsert_std_template()
		t = frappe.new_doc("Procurement Tender")
		t.std_template = TEMPLATE_CODE
		t.tender_title = "Hydration RT"
		t.tender_reference = "HYD-RT-1"
		t.insert(ignore_permissions=True)
		self.assertTrue(controller.load_template_defaults(t.name).get("ok"))
		t = frappe.get_doc("Procurement Tender", t.name)
		loc = "Officer-edited works location for registry test"
		t.db_set("og_tender_works_location", loc, update_modified=False)
		t.reload()
		self.assertTrue(controller.sync_officer_configuration(t.name).get("ok"))
		cfg = json.loads(frappe.get_value("Procurement Tender", t.name, "configuration_json"))
		self.assertEqual(cfg.get("TENDER.WORKS_LOCATION"), loc)
		frappe.delete_doc("Procurement Tender", t.name, force=True)
