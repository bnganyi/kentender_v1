# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-DASH-001 — Wizard instance service contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_instance_service import (
	assert_instance_std_version_immutable,
	create_configuration,
	delete_draft_configuration,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import force_reset_package_state_for_tests
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending
from kentender_procurement.std_engine.services.activation_readiness_service import sync_activation_flags


class TestWizardInstanceService(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
		CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()
		approve_all_pending(CANONICAL_PACKAGE_ID)
		sync_activation_flags(CANONICAL_PACKAGE_ID)
		activate_version(CANONICAL_PACKAGE_ID)
		frappe.set_user("Administrator")

	def test_create_binds_active_std_and_generates_steps(self) -> None:
		result = create_configuration(
			{
				"std_template_version_id": CANONICAL_PACKAGE_ID,
				"title": "Integration Test Configuration",
				"procuring_entity_id": "PE-TEST-001",
				"procuring_entity_name": "Test Entity",
			}
		)
		summary = result["summary"]
		self.assertTrue(summary["configuration_id"].startswith("ITCFG-"))
		self.assertEqual(summary["std_template_version_id"], CANONICAL_PACKAGE_ID)
		name = frappe.db.get_value(
			"Tender STD Instance",
			{"instance_code": summary["configuration_id"]},
			"name",
		)
		steps = frappe.get_all("Wizard Step Instance", filters={"tender_std_instance": name})
		self.assertEqual(len(steps), 15)
		self.assertTrue(frappe.db.exists("Wizard Audit Event", {"event_type": "wizard_instance_created"}))

	def test_std_version_immutable_after_creation(self) -> None:
		result = create_configuration(
			{
				"std_template_version_id": CANONICAL_PACKAGE_ID,
				"title": "Immutable STD Test",
			}
		)
		name = frappe.db.get_value(
			"Tender STD Instance",
			{"instance_code": result["summary"]["configuration_id"]},
			"name",
		)
		with self.assertRaises(frappe.ValidationError):
			assert_instance_std_version_immutable(name, "OTHER-VERSION")

	def test_delete_draft_only(self) -> None:
		result = create_configuration(
			{
				"std_template_version_id": CANONICAL_PACKAGE_ID,
				"title": "Delete Me",
			}
		)
		code = result["summary"]["configuration_id"]
		delete_draft_configuration(code)
		self.assertFalse(frappe.db.exists("Tender STD Instance", {"instance_code": code}))

	def test_planning_initiation_source_from_tender_id(self) -> None:
		result = create_configuration(
			{
				"std_template_version_id": CANONICAL_PACKAGE_ID,
				"title": "Planning Handoff",
				"tender_id": "TNT-HANDOFF-001",
				"procurement_plan_item_id": "PPLAN-000099",
			}
		)
		self.assertEqual(result["summary"]["initiation_source"], ws.INITIATION_PLANNING)
