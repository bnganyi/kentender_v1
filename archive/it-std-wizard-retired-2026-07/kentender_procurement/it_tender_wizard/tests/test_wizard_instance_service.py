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
	get_create_configuration_context,
	resolve_next_action,
	serialize_list_item,
)
from kentender_procurement.it_tender_wizard.tests.create_options_test_helpers import (
	cleanup_created_packages,
	ensure_released_it_procurement_package,
)
from kentender_procurement.it_tender_wizard.tests.std_test_fixtures import (
	ensure_canonical_it_std_active_for_tests,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID


class TestWizardInstanceService(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		ensure_canonical_it_std_active_for_tests()

	@classmethod
	def tearDownClass(cls) -> None:
		cleanup_created_packages()
		super().tearDownClass()

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

	def test_resolve_next_action_screen_01_labels(self) -> None:
		self.assertEqual(resolve_next_action(ws.IN_CONFIGURATION, 0)[1], "Continue Setup")
		self.assertEqual(resolve_next_action(ws.VALIDATION_FAILED, 0)[1], "Fix Blockers")
		self.assertEqual(resolve_next_action(ws.IN_CONFIGURATION, 2)[1], "Fix Blockers")
		self.assertEqual(resolve_next_action(ws.READY_FOR_REVIEW, 0)[1], "Submit for Review")
		self.assertEqual(resolve_next_action(ws.APPROVED_FOR_TENDER_CREATION, 0)[1], "Open Preview")
		self.assertEqual(resolve_next_action(ws.BOUND_TO_TENDER, 0)[1], "Open in Tender Management")

	def test_serialize_list_item_includes_next_action_and_issues(self) -> None:
		result = create_configuration(
			{
				"std_template_version_id": CANONICAL_PACKAGE_ID,
				"title": "List Serialize Next Action",
			}
		)
		name = frappe.db.get_value(
			"Tender STD Instance",
			{"instance_code": result["summary"]["configuration_id"]},
			"name",
		)
		doc = frappe.get_doc("Tender STD Instance", name)
		doc.wizard_state = ws.IN_CONFIGURATION
		doc.save(ignore_permissions=True)
		item = serialize_list_item(doc)
		self.assertEqual(item["next_action_label"], "Continue Setup")
		self.assertIn("blocker_count", item)
		self.assertIn("warning_count", item)
		self.assertEqual(item["wizard_state_label"], "In configuration")

	def test_create_configuration_context_returns_create_options(self) -> None:
		pkg = ensure_released_it_procurement_package(
			package_code="PP-ICT-WIZARD-CREATE-002",
			package_name="Data Center Hardware Refresh",
		)
		ctx = get_create_configuration_context()
		self.assertIn("create_options", ctx)
		self.assertNotIn("shells", ctx)
		self.assertNotIn("active_std_package", ctx)
		self.assertTrue(ctx["create_options"])
		match = next(
			row
			for row in ctx["create_options"]
			if row["procurement_package_id"] == pkg["name"]
		)
		self.assertEqual(match["procurement_package_label"], "PP-ICT-WIZARD-CREATE-002 — Data Center Hardware Refresh")
		self.assertEqual(match["planning_package_ref"], "PP-ICT-WIZARD-CREATE-002")
		self.assertEqual(match["procurement_method_label"], "Open Tender")
		self.assertIn("standard_tender_document_label", match)
		self.assertIn("standard_tender_document_selectable", match)

	def test_create_configuration_from_procurement_package(self) -> None:
		pkg = ensure_released_it_procurement_package(
			package_code="PP-ICT-WIZARD-CREATE-001",
			package_name="Wizard Integration Create Package",
			procuring_entity_code="PE-NATIONAL-TREASURY",
		)
		result = create_configuration(
			{
				"procurement_package_id": pkg["name"],
				"std_template_version_id": CANONICAL_PACKAGE_ID,
			}
		)
		summary = result["summary"]
		name = frappe.db.get_value(
			"Tender STD Instance",
			{"instance_code": summary["configuration_id"]},
			"name",
		)
		self.assertEqual(
			frappe.db.get_value("Tender STD Instance", name, "planning_package_code"),
			"PP-ICT-WIZARD-CREATE-001",
		)
		self.assertEqual(
			frappe.db.get_value("Tender STD Instance", name, "procuring_entity_name"),
			"National Treasury",
		)
		meta = frappe.parse_json(
			frappe.db.get_value("Tender STD Instance", name, "metadata_json") or "{}"
		)
		self.assertEqual(
			(meta.get("create_payload") or {}).get("procurement_package_id"),
			pkg["name"],
		)
