# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 8 (sync + whitelisted facades).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step8_sync_and_whitelists
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_core.seeds._common import (
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)
from kentender_core.seeds.constants import DEPT_PROC, ENTITY_MOH
from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as controller,
)
from kentender_procurement.tender_management.services.officer_tender_config import (
	merge_officer_overlay_into_configuration,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


def _ensure_procurement_officer_seed_user() -> None:
	frappe.set_user("Administrator")
	ensure_roles()
	moh = ensure_procuring_entity(ENTITY_MOH, "Ministry of Health")
	dept = ensure_department(DEPT_PROC, moh)
	upsert_seed_user(
		"procurement.officer@moh.test",
		"Procurement Officer MOH",
		"Procurement Officer",
		entity_name=moh,
		department_docname=dept,
	)


class TestOfficerPocStep8MergeOverlayUnit(UnitTestCase):
	def test_merge_preserves_unknown_configuration_keys(self) -> None:
		base = {"TENDER.TENDER_NAME": "Old", "CUSTOM.UNKNOWN": {"x": 1}}
		class _T:
			tender_title = "New Title"
			tender_reference = "REF-1"
			procurement_method = "OPEN_COMPETITIVE_TENDERING"
			tender_scope = "NATIONAL"
			procurement_category = "WORKS"
			template_code = TEMPLATE_CODE
			template_version = "1"
			package_hash = "phash"

		merged = merge_officer_overlay_into_configuration(base, _T())
		self.assertEqual(merged["TENDER.TENDER_NAME"], "New Title")
		self.assertEqual(merged["CUSTOM.UNKNOWN"], {"x": 1})


class TestOfficerPocStep8SyncIntegration(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Sync Test"
		self.tender.tender_reference = "SYNC-REF"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)
		self.assertTrue(controller.load_sample_tender(self.tender.name).get("ok"))

	def test_sync_officer_configuration_updates_json_and_resets_validation(self) -> None:
		self.assertTrue(controller.validate_tender_configuration(self.tender.name).get("ok"))
		t = frappe.get_doc("Procurement Tender", self.tender.name)
		self.assertNotEqual(t.validation_status, "Not Validated")

		t.tender_title = "Updated Officer Title"
		t.save(ignore_permissions=True)

		out = controller.sync_officer_configuration(self.tender.name)
		self.assertTrue(out.get("ok"))
		t2 = frappe.get_doc("Procurement Tender", self.tender.name)
		self.assertEqual(t2.validation_status, "Not Validated")
		cfg = json.loads(t2.configuration_json)
		self.assertEqual(cfg.get("TENDER.TENDER_NAME"), "Updated Officer Title")

	def test_validate_officer_configuration_after_title_change(self) -> None:
		t = frappe.get_doc("Procurement Tender", self.tender.name)
		t.tender_title = "Another Title"
		t.save(ignore_permissions=True)
		env = controller.validate_officer_configuration(self.tender.name)
		self.assertIn("validation_status", env)
		cfg = json.loads(frappe.get_value("Procurement Tender", self.tender.name, "configuration_json"))
		self.assertEqual(cfg.get("TENDER.TENDER_NAME"), "Another Title")

	def test_get_officer_required_forms_checklist_shape(self) -> None:
		self.assertTrue(controller.validate_officer_configuration(self.tender.name).get("ok"))
		self.assertTrue(controller.generate_officer_required_forms(self.tender.name).get("ok"))
		chk = controller.get_officer_required_forms_checklist(self.tender.name)
		self.assertTrue(chk.get("ok"))
		self.assertGreater(chk.get("count", 0), 0)
		self.assertTrue(all("required_because" in r for r in chk.get("rows", [])))

	def test_get_officer_boq_status(self) -> None:
		self.assertTrue(controller.generate_officer_representative_boq(self.tender.name).get("ok"))
		st = controller.get_officer_boq_status(self.tender.name)
		self.assertTrue(st.get("ok"))
		self.assertIn("boq_row_count", st)

	def test_initialize_officer_tender_from_template(self) -> None:
		std_name = frappe.db.get_value("STD Template", {"template_code": TEMPLATE_CODE}, "name")
		self.assertTrue(std_name)
		out = controller.initialize_officer_tender_from_template(std_name)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("tender"))
		frappe.delete_doc("Procurement Tender", out["tender"], force=True)


class TestOfficerPocStep8OfficerUserPermission(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		_ensure_procurement_officer_seed_user()
		frappe.set_user("Administrator")
		upsert_std_template()
		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Officer User Sync"
		self.tender.tender_reference = "OFF-SYNC"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)
		self.assertTrue(controller.load_sample_tender(self.tender.name).get("ok"))

	def test_procurement_officer_can_sync(self) -> None:
		frappe.set_user("procurement.officer@moh.test")
		t = frappe.get_doc("Procurement Tender", self.tender.name)
		t.tender_title = "Officer Edited"
		t.save()
		out = controller.sync_officer_configuration(self.tender.name)
		self.assertTrue(out.get("ok"))
