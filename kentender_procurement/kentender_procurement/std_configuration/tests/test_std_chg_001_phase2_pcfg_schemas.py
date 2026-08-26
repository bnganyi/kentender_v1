# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 2 — PCFG schema DocTypes and cross-cutting objects.

Covers only the guards explicitly named by spec §7.7-§7.18 and §11.2 that belong at
save time (not the fuller §11 coverage/validation engine, which is Phase 6): a
render-or-downstream consumer requirement, unique keys within an owning Draft/
Version, one edge per (source, target) pair, scored-criterion weight, and a
Return decision's required correction.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

PACKAGE_CODE = "KE-TEST-STD-P2"


class TestSTDChg001Phase2PCFGSchemas(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._cleanup()
		self.package = frappe.get_doc(
			{
				"doctype": "STD Cfg Package",
				"package_code": PACKAGE_CODE,
				"official_title": "Test Package for Phase 2",
				"requirement_profile": "Information Technology",
			}
		).insert(ignore_permissions=True)
		self.draft = frappe.get_doc(
			{
				"doctype": "STD Cfg Draft",
				"package_id": PACKAGE_CODE,
				"proposed_version_number": 1,
				"official_issue_label": "April 2021 edition",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		self._cleanup()

	def _cleanup(self):
		# Scoped to THIS test's own package's Draft/Version names — a blanket
		# `{"reference_doctype": "STD Cfg Draft"}` (no reference_name filter)
		# or `["like", "%"]` here would delete every OTHER package's content
		# too, including the real golden `KE-PPRA-IT` fixture (Phase 9).
		# Confirmed live: this exact bug class silently passed for 8 phases
		# because each phase's tests were the only content on the site at the
		# time it ran — only Phase 9's persistent fixture surfaced it.
		draft_names = frappe.get_all("STD Cfg Draft", {"package_id": PACKAGE_CODE}, pluck="name")
		for doctype in (
			"STD Cfg Parameter Definition",
			"STD Cfg Requirement Schema",
			"STD Cfg Schedule Schema",
			"STD Cfg Inventory Schema",
			"STD Cfg Price Schema",
			"STD Cfg Evaluation Schema",
			"STD Cfg Form Schema",
			"STD Cfg Contract Schema",
			"STD Cfg Output Mapping",
			"STD Cfg Validation Finding",
		):
			if draft_names:
				frappe.db.delete(doctype, {"reference_name": ["in", draft_names]})
		if draft_names:
			frappe.db.delete("STD Cfg Assistance Batch", {"draft_id": ["in", draft_names]})
			task_names = frappe.get_all("STD Cfg Review Task", {"draft_id": ["in", draft_names]}, pluck="name")
			if task_names:
				frappe.db.delete("STD Cfg Decision", {"review_task_id": ["in", task_names]})
			frappe.db.delete("STD Cfg Review Task", {"draft_id": ["in", draft_names]})
		frappe.db.delete("STD Cfg Tender Manifest", {"package_code": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Draft", {"package_id": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Version", {"package_id": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Package", {"package_code": PACKAGE_CODE})
		frappe.db.commit()

	def _owner(self):
		return {"reference_doctype": "STD Cfg Draft", "reference_name": self.draft.name}

	# --- STD Cfg Parameter Definition -----------------------------------------

	def test_parameter_without_render_or_downstream_binding_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Parameter Definition",
				**self._owner(),
				"parameter_key": "tender.validity_days",
				"label": "Tender validity",
				"value_type": "Duration",
				"runtime_owner": "Tender Preparation",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_parameter_choice_requires_allowed_values(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Parameter Definition",
				**self._owner(),
				"parameter_key": "tender.currency",
				"label": "Tender currency",
				"value_type": "Choice",
				"runtime_owner": "Tender Preparation",
				"render_binding": "TDS.currency",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_parameter_key_unique_within_draft(self):
		base = {
			"doctype": "STD Cfg Parameter Definition",
			**self._owner(),
			"parameter_key": "tender.validity_days",
			"label": "Tender validity",
			"value_type": "Duration",
			"runtime_owner": "Tender Preparation",
			"render_binding": "TDS.validity",
		}
		frappe.get_doc(base).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(base).insert(ignore_permissions=True)

	def test_valid_parameter_definition_saves(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Parameter Definition",
				**self._owner(),
				"parameter_key": "tender.validity_days",
				"label": "Tender validity",
				"value_type": "Duration",
				"runtime_owner": "Tender Preparation",
				"required": 1,
				"minimum_value": "120",
				"render_binding": "Section II — Tender Data Sheet",
				"downstream_binding": "Contract Formation",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)

	# --- STD Cfg Requirement Schema --------------------------------------------

	def test_requirement_schema_missing_downstream_binding_rejected_by_framework(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Requirement Schema",
				**self._owner(),
				"category": "Security",
				"display_order": 4,
				"allowed_response_types": "Compliance choice",
				"acceptance_mode": "Independent test evidence",
				"render_binding": "Sections V and VI",
				"bidder_response_binding": "Technical compliance response",
				"evaluation_binding": "Requirement evaluation input",
				# contract_carry_forward_binding intentionally omitted
			}
		)
		with self.assertRaises(frappe.MandatoryError):
			doc.insert(ignore_permissions=True)

	def test_requirement_category_unique_within_draft(self):
		base = {
			"doctype": "STD Cfg Requirement Schema",
			**self._owner(),
			"category": "Security",
			"display_order": 4,
			"allowed_response_types": "Compliance choice",
			"acceptance_mode": "Independent test evidence",
			"render_binding": "Sections V and VI",
			"bidder_response_binding": "Technical compliance response",
			"evaluation_binding": "Requirement evaluation input",
			"contract_carry_forward_binding": "Accepted supplier obligation",
		}
		frappe.get_doc(base).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(base).insert(ignore_permissions=True)

	# --- STD Cfg Evaluation Schema ----------------------------------------------

	def test_scored_criterion_requires_weight(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Evaluation Schema",
				**self._owner(),
				"stage": "Technical evaluation",
				"criterion_key": "tech-response-quality",
				"criterion_structure": "Technical response quality",
				"display_order": 1,
				"treatment": "Scored",
				"response_source": "Narrative response",
				"failure_effect": "Fails technical evaluation if below threshold",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_pass_fail_criterion_forbids_weight(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Evaluation Schema",
				**self._owner(),
				"stage": "Technical evaluation",
				"criterion_key": "mandatory-compliance",
				"criterion_structure": "Mandatory requirement compliance",
				"display_order": 1,
				"treatment": "Pass/Fail",
				"response_source": "Requirement response",
				"weight": 10,
				"failure_effect": "Fails technical evaluation",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	# --- STD Cfg Output Mapping --------------------------------------------------

	def test_output_mapping_same_source_multiple_targets_allowed(self):
		frappe.get_doc(
			{
				"doctype": "STD Cfg Output Mapping",
				**self._owner(),
				"source_binding_key": "tender.validity_days",
				"owning_area": "PCFG-03",
				"target": "Render",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "STD Cfg Output Mapping",
				**self._owner(),
				"source_binding_key": "tender.validity_days",
				"owning_area": "PCFG-03",
				"target": "Contract Formation",
			}
		).insert(ignore_permissions=True)

	def test_output_mapping_duplicate_pair_rejected(self):
		base = {
			"doctype": "STD Cfg Output Mapping",
			**self._owner(),
			"source_binding_key": "tender.validity_days",
			"owning_area": "PCFG-03",
			"target": "Render",
		}
		frappe.get_doc(base).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(base).insert(ignore_permissions=True)

	# --- STD Cfg Assistance Batch -------------------------------------------------

	def test_assistance_batch_snapshots_draft_record_version(self):
		batch = frappe.get_doc(
			{
				"doctype": "STD Cfg Assistance Batch",
				"draft_id": self.draft.name,
				"assistance_type": "Prior configuration",
				"input_reference": "IT_STD_Config_Control_Pack_v3.json",
				"actor": "Administrator",
			}
		)
		batch.insert(ignore_permissions=True)
		self.assertEqual(batch.draft_record_version_snapshot, self.draft.record_version)

	# --- STD Cfg Decision ------------------------------------------------------

	def _make_review_task(self):
		return frappe.get_doc(
			{
				"doctype": "STD Cfg Review Task",
				"draft_id": self.draft.name,
				"reviewer": "Administrator",
				"submitted_by": "Administrator",
				"submitted_at": frappe.utils.now_datetime(),
				"snapshot_record_version": self.draft.record_version,
			}
		).insert(ignore_permissions=True)

	def test_return_decision_requires_correction(self):
		task = self._make_review_task()
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Decision",
				"review_task_id": task.name,
				"decision": "Return for correction",
				"decided_by": "Administrator",
				"decided_at": frappe.utils.now_datetime(),
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_activate_decision_forbids_correction_text(self):
		task = self._make_review_task()
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Decision",
				"review_task_id": task.name,
				"decision": "Activate package",
				"decided_by": "Administrator",
				"decided_at": frappe.utils.now_datetime(),
				"correction_required": "should not be here",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_valid_return_decision_saves(self):
		task = self._make_review_task()
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Decision",
				"review_task_id": task.name,
				"decision": "Return for correction",
				"decided_by": "Administrator",
				"decided_at": frappe.utils.now_datetime(),
				"correction_required": "Correct the bidder response mapping for Security requirements.",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)

	# --- STD Cfg Tender Manifest -------------------------------------------------

	def test_manifest_rejects_duplicate_item_key(self):
		version = frappe.get_doc(
			{
				"doctype": "STD Cfg Version",
				"package_id": PACKAGE_CODE,
				"version_number": 1,
				"status": "Active",
				"official_issue_label": "April 2021 edition",
				"official_source_file_id": frappe.get_doc(
					{
						"doctype": "STD Cfg Source Document",
						"reference_doctype": "STD Cfg Draft",
						"reference_name": self.draft.name,
						"official_title": "Test Source",
						"official_issue_label": "April 2021 edition",
						"file_id": "/files/test.pdf",
					}
				)
				.insert(ignore_permissions=True)
				.name,
			}
		).insert(ignore_permissions=True)

		manifest = frappe.get_doc(
			{
				"doctype": "STD Cfg Tender Manifest",
				"manifest_version": "1",
				"package_code": PACKAGE_CODE,
				"std_version_id": version.name,
				"official_title": "Test Package for Phase 2",
				"official_issue": "April 2021 edition",
				"items": [
					{
						"item_key": "tender_reference",
						"step_id": "CFG-01",
						"label": "Tender reference",
						"value_type": "Generated Display",
						"source_mode": "Generated",
						"required_mode": "Always",
						"render_binding": "Cover",
						"completion_effect": "Blocks step",
					},
					{
						"item_key": "tender_reference",
						"step_id": "CFG-01",
						"label": "Duplicate",
						"value_type": "Generated Display",
						"source_mode": "Generated",
						"required_mode": "Always",
						"render_binding": "Cover",
						"completion_effect": "Blocks step",
					},
				],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			manifest.insert(ignore_permissions=True)
		frappe.db.delete("STD Cfg Source Document", {"official_title": "Test Source"})
