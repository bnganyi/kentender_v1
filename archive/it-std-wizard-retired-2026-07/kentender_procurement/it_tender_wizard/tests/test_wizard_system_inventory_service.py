# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-INV-001 — System Inventory service contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.services.wizard_system_inventory_service import (
	INVENTORY_CATEGORIES,
	SYSTEM_INVENTORY_STEP_CODE,
	_ensure_inventory_doc,
	get_system_inventory,
	save_system_inventory,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import (
	_ensure_system_inventory,
	seed_dashboard_sample_instances,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import force_reset_package_state_for_tests
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.activation_readiness_service import sync_activation_flags
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending

SEED_CODE = "ITCFG-DASH-SEED-001"
SEED_COMPLETE_CODE = "ITCFG-DASH-SEED-003"


class TestWizardSystemInventoryService(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
		CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()
		approve_all_pending(CANONICAL_PACKAGE_ID)
		sync_activation_flags(CANONICAL_PACKAGE_ID)
		activate_version(CANONICAL_PACKAGE_ID)
		seed_dashboard_sample_instances()
		frappe.set_user("Administrator")

	def test_get_returns_all_eight_categories_grouped_without_internal_ids(self) -> None:
		payload = get_system_inventory(SEED_CODE)

		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual([group["category"] for group in payload["categories"]], list(INVENTORY_CATEGORIES))
		for option in payload["requirement_options"] + payload["schedule_options"]:
			self.assertEqual(option["id"], option["code"])
			self.assertTrue(option["name"])
			self.assertEqual(set(option), {"id", "code", "name"})
		items = [item for group in payload["categories"] for item in group["items"]]
		self.assertTrue(items)
		for item in items:
			self.assertEqual(item["item_id"], item["item_code"])
			self.assertNotIn("name", item)
			self.assertNotIn("parent", item)
			self.assertNotIn("parenttype", item)
			self.assertNotIn("parentfield", item)

	def test_inventory_is_technical_disclosure_only(self) -> None:
		payload = get_system_inventory(SEED_CODE)
		items = [item for group in payload["categories"] for item in group["items"]]

		self.assertEqual({item["pricing_policy"] for item in items}, {"REQUIRED", "OPTIONAL", "NOT_PRICED"})
		for item in items:
			self.assertNotIn("unit_price", item)
			self.assertNotIn("total_price", item)
			self.assertNotIn("price_schedule_binding", item)
			self.assertNotIn("cost_category", item)
			self.assertNotIn("quantity", item)
			self.assertNotIn("unit_of_measure", item)

	def test_selected_upsert_persists_technical_fields_and_code_refs(self) -> None:
		result = save_system_inventory(
			SEED_CODE,
			{
				"selected_item_id": "SYS-CORE-ERP",
				"selected_item": {
					"item_code": "SYS-CORE-ERP",
					"category": "SYSTEMS_IN_SCOPE",
					"title": "Core Finance System",
					"description": "Production ERP requiring controlled migration.",
					"scope_status": "IN_SCOPE",
					"required_action": "MIGRATE",
					"bidder_consideration": "Provide a migration and reconciliation approach.",
					"technical_details": "Version 4.2 production estate.",
					"data_volume": "500 GB",
					"integration_requirement": "API",
					"confidentiality_level": "CONFIDENTIAL",
					"review_status": "NEEDS_REVIEW",
					"pricing_policy": "NOT_PRICED",
					"requirement_refs": ["3.1", "3.2"],
					"schedule_refs": ["PHASE_1", "PH1-REQ"],
					"contract_carry_forward": 1,
					"display_order": 1,
				},
			},
		)

		saved = next(
			item
			for group in result["categories"]
			for item in group["items"]
			if item["item_code"] == "SYS-CORE-ERP"
		)
		self.assertEqual(saved["confidentiality_level"], "CONFIDENTIAL")
		self.assertEqual(saved["review_status"], "NEEDS_REVIEW")
		self.assertEqual(saved["pricing_policy"], "NOT_PRICED")
		self.assertEqual(saved["requirement_refs"], ["3.1", "3.2"])
		self.assertEqual(saved["schedule_refs"], ["PHASE_1", "PH1-REQ"])
		self.assertEqual(saved["contract_carry_forward"], 1)

	def test_selected_upsert_can_add_new_stable_code(self) -> None:
		result = save_system_inventory(
			SEED_CODE,
			{
				"selected_item_id": "OOS-ARCHIVE-001",
				"selected_item": {
					"item_code": "OOS-ARCHIVE-001",
					"category": "OUT_OF_SCOPE_ITEMS",
					"title": "Archive Tape Library",
					"description": "Retained only as a boundary reference.",
					"scope_status": "OUT_OF_SCOPE",
					"required_action": "NO_BIDDER_ACTION",
					"pricing_policy": "NOT_PRICED",
					"confidentiality_level": "INTERNAL",
					"review_status": "DRAFT",
				},
			},
		)
		codes = {
			item["item_code"]
			for group in result["categories"]
			for item in group["items"]
		}
		self.assertIn("OOS-ARCHIVE-001", codes)

	def test_selected_upsert_generates_hidden_stable_code_for_new_item(self) -> None:
		result = save_system_inventory(
			SEED_CODE,
			{
				"selected_item": {
					"category": "SYSTEMS_IN_SCOPE",
					"title": "Document Management Platform",
					"description": "Technical-disclosure entry for the document platform.",
					"scope_status": "IN_SCOPE",
					"required_action": "DISCLOSE",
					"pricing_policy": "NOT_PRICED",
					"confidentiality_level": "INTERNAL",
					"review_status": "DRAFT",
				},
			},
		)
		added = next(
			item
			for group in result["categories"]
			for item in group["items"]
			if item["title"] == "Document Management Platform"
		)
		self.assertRegex(added["item_code"], r"^SYS-DOCUMENT-MANAGEMENT-PLATFORM(?:-\d+)?$")

	def test_full_save_rejects_duplicate_item_codes(self) -> None:
		item = {
			"item_code": "DUP-001",
			"category": "SYSTEMS_IN_SCOPE",
			"title": "Duplicate",
			"description": "Duplicate inventory item.",
			"scope_status": "IN_SCOPE",
			"required_action": "RETAIN",
			"pricing_policy": "REQUIRED",
			"confidentiality_level": "PUBLIC",
			"review_status": "DRAFT",
		}
		with self.assertRaisesRegex(frappe.ValidationError, "Duplicate inventory item code"):
			save_system_inventory(SEED_CODE, {"items": [item, dict(item)]})

	def test_save_rejects_invalid_category_and_out_of_scope_bidder_action(self) -> None:
		item = {
			"item_code": "BAD-001",
			"category": "COMMERCIAL_PRICE",
			"title": "Invalid",
			"description": "Invalid inventory item.",
			"scope_status": "IN_SCOPE",
			"required_action": "RETAIN",
			"pricing_policy": "REQUIRED",
			"confidentiality_level": "PUBLIC",
			"review_status": "DRAFT",
		}
		with self.assertRaisesRegex(frappe.ValidationError, "category"):
			save_system_inventory(SEED_CODE, {"items": [item]})
		item["category"] = "OUT_OF_SCOPE_ITEMS"
		item["scope_status"] = "OUT_OF_SCOPE"
		with self.assertRaisesRegex(frappe.ValidationError, "cannot require bidder action"):
			save_system_inventory(SEED_CODE, {"items": [item]})

	def test_save_rejects_unknown_requirement_and_schedule_refs(self) -> None:
		item = {
			"item_code": "BAD-REF-001",
			"category": "INTEGRATION_POINTS",
			"title": "Unknown references",
			"description": "References must remain within this configuration.",
			"scope_status": "IN_SCOPE",
			"required_action": "INTEGRATE",
			"pricing_policy": "OPTIONAL",
			"confidentiality_level": "INTERNAL",
			"review_status": "DRAFT",
			"requirement_refs": ["UNKNOWN-REQ"],
			"schedule_refs": ["UNKNOWN-PHASE"],
		}
		with self.assertRaisesRegex(frappe.ValidationError, "unknown requirement"):
			save_system_inventory(SEED_CODE, {"items": [item]})
		item["requirement_refs"] = []
		with self.assertRaisesRegex(frappe.ValidationError, "unknown schedule"):
			save_system_inventory(SEED_CODE, {"items": [item]})

	def test_save_rejects_non_editable_state(self) -> None:
		_ensure_system_inventory(SEED_COMPLETE_CODE, {"instance_code": SEED_COMPLETE_CODE})
		with self.assertRaisesRegex(frappe.ValidationError, "cannot be edited"):
			save_system_inventory(
				SEED_COMPLETE_CODE,
				{"selected_item_id": "SYS-CORE-ERP", "selected_item": {"item_code": "SYS-CORE-ERP"}},
			)

	def test_save_rejects_locked_inventory(self) -> None:
		name = frappe.db.get_value("Tender STD System Inventory", {"tender_std_instance": SEED_CODE})
		frappe.db.set_value("Tender STD System Inventory", name, "lock_status", "REVIEW_LOCKED")
		try:
			with self.assertRaisesRegex(frappe.ValidationError, "locked"):
				save_system_inventory(
					SEED_CODE,
					{"selected_item_id": "SYS-CORE-ERP", "selected_item": {"item_code": "SYS-CORE-ERP"}},
				)
		finally:
			frappe.db.set_value("Tender STD System Inventory", name, "lock_status", "UNLOCKED")

	def test_complete_full_save_updates_step_status(self) -> None:
		payload = get_system_inventory(SEED_CODE)
		items = [item for group in payload["categories"] for item in group["items"]]
		for item in items:
			item["review_status"] = "APPROVED"
		save_system_inventory(SEED_CODE, {"items": items})
		status = frappe.db.get_value(
			"Wizard Step Instance",
			{"tender_std_instance": SEED_CODE, "step_code": SYSTEM_INVENTORY_STEP_CODE},
			"status",
		)
		self.assertEqual(status, "COMPLETE")

	def test_ensure_inventory_doc_and_seed_are_idempotent(self) -> None:
		name = frappe.db.get_value("Tender STD System Inventory", {"tender_std_instance": SEED_CODE})
		if name:
			frappe.delete_doc("Tender STD System Inventory", name, force=True)
		first = _ensure_inventory_doc(SEED_CODE)
		second = _ensure_inventory_doc(SEED_CODE)
		_ensure_system_inventory(SEED_CODE, {"instance_code": SEED_CODE})
		_ensure_system_inventory(SEED_CODE, {"instance_code": SEED_CODE})

		self.assertEqual(first.name, second.name)
		self.assertEqual(
			frappe.db.count("Tender STD System Inventory", {"tender_std_instance": SEED_CODE}),
			1,
		)
