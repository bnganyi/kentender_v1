# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-REQ-001 — IT Requirements composer service contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.services.wizard_it_requirements_service import (
	FORBIDDEN_DISPLAY_LABELS,
	IT_REQUIREMENTS_STEP_CODE,
	_ensure_requirements_doc,
	_serialize_item,
	compute_requirements_completion,
	get_it_requirements,
	save_it_requirements,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import (
	_ensure_requirements,
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


class TestWizardItRequirementsService(IntegrationTestCase):
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

	def test_get_it_requirements_returns_sections_and_context(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual(payload["title"], "Data Center Hardware Refresh")
		self.assertEqual(payload["procuring_entity"]["name"], "National Treasury")
		self.assertIn("sections", payload)
		self.assertTrue(payload["sections"])
		self.assertIn("completion", payload)
		self.assertEqual(payload["selected_item_id"], "3.2")

	def test_seed_001_requirements_is_partially_complete(self) -> None:
		_ensure_requirements(SEED_CODE, {"instance_code": SEED_CODE})
		payload = get_it_requirements(SEED_CODE)
		completion = payload["completion"]
		self.assertEqual(completion["total"], 30)
		self.assertGreaterEqual(completion["completed"], 20)
		self.assertLess(completion["completed"], 30)
		self.assertGreater(completion["gaps"]["missing_evidence_instructions"], 0)

	def test_serialized_items_use_composer_display_labels(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		item = next(
			row
			for section in payload["sections"]
			for row in section["items"]
			if row["requirement_code"] == "3.2"
		)
		self.assertEqual(item["treatment_label"], "Evaluation-linked")
		self.assertEqual(item["evaluation_linked_label"], "Linked to Evaluation")
		self.assertIn(item["evidence_level_label"], {"Evidence Required", "Missing Evidence Instruction"})
		self.assertIn(item["acceptance_label"], {"Criteria Defined", "Missing Criteria"})
		for forbidden in FORBIDDEN_DISPLAY_LABELS:
			self.assertNotIn(forbidden, item["treatment_label"])
			self.assertNotIn(forbidden, item["evidence_level_label"])
			self.assertNotIn(forbidden, item["acceptance_label"])

	def test_save_persists_composer_fields(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		items = []
		for section in payload["sections"]:
			items.extend(section["items"])
		target = next(row for row in items if row["requirement_code"] == "3.2")
		target["bidder_instruction"] = "Provide numeric storage capacity in terabytes."
		target["evidence_instruction"] = "Upload manufacturer datasheet."
		target["acceptance_criteria"] = "Capacity verified during technical evaluation."
		target["category"] = "Hardware"
		result = save_it_requirements(
			SEED_CODE,
			{"selected_item_id": "3.2", "selected_item": target},
		)
		saved = next(
			row
			for section in result["sections"]
			for row in section["items"]
			if row["requirement_code"] == "3.2"
		)
		self.assertEqual(saved["bidder_instruction"], "Provide numeric storage capacity in terabytes.")
		self.assertEqual(saved["evidence_instruction"], "Upload manufacturer datasheet.")
		self.assertEqual(saved["acceptance_criteria"], "Capacity verified during technical evaluation.")
		self.assertEqual(saved["category"], "Hardware")

	def test_save_it_requirements_persists_selected_item(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		items = []
		for section in payload["sections"]:
			items.extend(section["items"])
		target = next(row for row in items if row["requirement_code"] == "3.2")
		target["description"] = "Updated storage capacity requirement for API persistence test."
		target["evaluation_binding"] = "technical_solution_proposal"
		result = save_it_requirements(
			SEED_CODE,
			{
				"selected_item_id": "3.2",
				"selected_item": target,
				"items": items,
			},
		)
		saved = next(
			row
			for section in result["sections"]
			for row in section["items"]
			if row["requirement_code"] == "3.2"
		)
		self.assertIn("Updated storage capacity requirement", saved["description"])

	def test_save_rejects_mandatory_item_without_description(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		items = []
		for section in payload["sections"]:
			items.extend(section["items"])
		target = next(row for row in items if row["requirement_code"] == "3.1")
		target["description"] = ""
		with self.assertRaises(frappe.ValidationError):
			save_it_requirements(SEED_CODE, {"items": items})

	def test_seed_003_requirements_is_complete(self) -> None:
		_ensure_requirements(SEED_COMPLETE_CODE, {"instance_code": SEED_COMPLETE_CODE})
		payload = get_it_requirements(SEED_COMPLETE_CODE)
		self.assertEqual(payload["completion"]["completed"], payload["completion"]["total"])
		self.assertEqual(payload["completion"]["gaps"]["missing_evidence_instructions"], 0)

	def test_save_complete_requirements_updates_step_status(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		items = []
		for section in payload["sections"]:
			for row in section["items"]:
				complete_row = dict(row)
				if not complete_row.get("description"):
					complete_row["description"] = f"Completed description for {complete_row['requirement_code']}."
				if not complete_row.get("requirement_type"):
					complete_row["requirement_type"] = "FUNCTIONAL"
				if int(complete_row.get("evidence_required") or 0) and not complete_row.get("evaluation_binding"):
					complete_row["evaluation_binding"] = "technical_solution_proposal"
				items.append(complete_row)
		save_it_requirements(SEED_CODE, {"items": items})
		step_status = frappe.db.get_value(
			"Wizard Step Instance",
			{"tender_std_instance": SEED_CODE, "step_code": IT_REQUIREMENTS_STEP_CODE},
			"status",
		)
		self.assertEqual(step_status, "COMPLETE")

	def test_compute_requirements_completion_counts_incomplete_items(self) -> None:
		result = compute_requirements_completion(
			[
				{
					"requirement_code": "1.1",
					"title": "Title",
					"description": "",
					"requirement_type": "FUNCTIONAL",
					"priority": "MANDATORY",
					"evidence_required": 0,
				}
			]
		)
		self.assertEqual(result["completed"], 0)
		self.assertEqual(result["total"], 1)

	def test_ensure_requirements_doc_is_idempotent(self) -> None:
		req_name = frappe.db.get_value("Tender STD IT Requirements", {"tender_std_instance": SEED_CODE})
		if req_name:
			frappe.delete_doc("Tender STD IT Requirements", req_name, force=True)
		first = _ensure_requirements_doc(SEED_CODE)
		second = _ensure_requirements_doc(SEED_CODE)
		self.assertEqual(first.name, second.name)
		self.assertEqual(
			frappe.db.count("Tender STD IT Requirements", {"tender_std_instance": SEED_CODE}),
			1,
		)

	def test_get_it_requirements_is_idempotent_when_doc_missing(self) -> None:
		req_name = frappe.db.get_value("Tender STD IT Requirements", {"tender_std_instance": SEED_CODE})
		if req_name:
			frappe.delete_doc("Tender STD IT Requirements", req_name, force=True)
		first = get_it_requirements(SEED_CODE)
		second = get_it_requirements(SEED_CODE)
		self.assertEqual(first["configuration_id"], second["configuration_id"])
		self.assertEqual(
			frappe.db.count("Tender STD IT Requirements", {"tender_std_instance": SEED_CODE}),
			1,
		)

	def test_get_it_requirements_includes_v2_flat_requirements_and_summary(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		self.assertIn("requirements", payload)
		self.assertIn("requirements_summary", payload)
		self.assertEqual(len(payload["requirements"]), payload["requirements_summary"]["total_count"])
		self.assertEqual(payload["tender_ref"], SEED_CODE)
		self.assertEqual(payload["tender_title"], "Data Center Hardware Refresh")
		self.assertIn("wizard_state_label", payload)
		self.assertIn("blocker_count", payload)
		self.assertIn("warning_count", payload)

	def test_v2_serialized_item_labels(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		item = next(row for row in payload["requirements"] if row["display_id"] == "3.2")
		self.assertEqual(item["treatment"], "Evaluation-linked")
		self.assertIn(
			item["evidence_status_label"],
			{"Evidence required", "Missing instruction"},
		)
		self.assertIn(
			item["acceptance_status_label"],
			{"Acceptance defined", "Missing acceptance"},
		)
		self.assertIn(item["status_label"], {"Complete", "Needs attention", "Draft"})
		self.assertIn(item["evaluation_reference_label"], {"Linked in Evaluation Setup", "Not linked to evaluation"})
		self.assertIn(
			item["forms_evidence_reference_label"],
			{"Evidence item will be configured in Forms & Evidence", "No evidence item required"},
		)
		self.assertIn(
			item["contract_values_reference_label"],
			{"May carry into contract values", "No contract carry-forward expected"},
		)
		self.assertEqual(item["category"], "Technical Requirement")

	def test_save_persists_v2_category_labels_as_legacy_storage(self) -> None:
		payload = get_it_requirements(SEED_CODE)
		items = []
		for section in payload["sections"]:
			items.extend(section["items"])
		target = next(row for row in items if row["requirement_code"] == "3.1")
		target["category"] = "Technical Requirement"
		result = save_it_requirements(
			SEED_CODE,
			{"selected_item_id": "3.1", "selected_item": target},
		)
		saved = next(
			row
			for section in result["sections"]
			for row in section["items"]
			if row["requirement_code"] == "3.1"
		)
		self.assertEqual(saved["category"], "Hardware")
		self.assertEqual(saved["v2_category"], "Technical Requirement")
		payload = get_it_requirements(SEED_CODE)
		item = next(row for row in payload["requirements"] if row["display_id"] == "3.2")
		self.assertEqual(item["treatment"], "Evaluation-linked")
		self.assertIn(
			item["evidence_status_label"],
			{"Evidence required", "Missing instruction"},
		)
		self.assertIn(
			item["acceptance_status_label"],
			{"Acceptance defined", "Missing acceptance"},
		)
		self.assertIn(item["status_label"], {"Complete", "Needs attention", "Draft"})
		self.assertIn(item["evaluation_reference_label"], {"Linked in Evaluation Setup", "Not linked to evaluation"})
		self.assertIn(
			item["forms_evidence_reference_label"],
			{"Evidence item will be configured in Forms & Evidence", "No evidence item required"},
		)
		self.assertIn(
			item["contract_values_reference_label"],
			{"May carry into contract values", "No contract carry-forward expected"},
		)
		self.assertEqual(item["category"], "Technical Requirement")
