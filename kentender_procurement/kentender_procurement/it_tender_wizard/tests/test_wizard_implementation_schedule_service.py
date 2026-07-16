# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-SCHED-001 — Implementation Schedule composer service contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.services.wizard_implementation_schedule_service import (
	IMPLEMENTATION_SCHEDULE_STEP_CODE,
	_validate_acceptance_criteria,
	_validate_milestone_order,
	_ensure_schedule_doc,
	compute_schedule_completion,
	get_implementation_schedule,
	save_implementation_schedule,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import (
	_ensure_implementation_schedule,
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


class TestWizardImplementationScheduleService(IntegrationTestCase):
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

	def test_get_implementation_schedule_returns_phases_and_context(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual(payload["title"], "Data Center Hardware Refresh")
		self.assertEqual(payload["procuring_entity"]["name"], "National Treasury")
		self.assertIn("phases", payload)
		self.assertTrue(payload["phases"])
		self.assertIn("completion", payload)
		self.assertEqual(payload["selected_phase_code"], "PHASE_2")
		self.assertEqual(payload["implementation_model"], "PHASED")

	def test_get_returns_tender_number_for_context_strip(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		# Context strip "Tender Ref" must expose the tender number, not the internal
		# configuration id (ITW-06 context strip fix).
		self.assertEqual(payload["tender_number"], "NT/T/ICT/2024-009")

	def test_save_single_turnkey_persists_dedicated_fields_and_preserves_phases(self) -> None:
		before = get_implementation_schedule(SEED_CODE)
		phase_codes = [row["phase_code"] for row in before["phases"]]
		turnkey = {
			"expected_delivery_duration": "6 Months",
			"delivery_trigger": "Contract signing and notice to proceed",
			"key_deliverables": "Installed, configured, tested, documented, and handed-over solution.",
			"unified_acceptance_criteria": "Procuring entity confirms complete delivery and commissioning.",
			"evidence_required": "Completion report, test results, training records, handover certificate.",
			"carry_forward_decision": "YES",
		}

		result = save_implementation_schedule(
			SEED_CODE,
			{
				"implementation_model": "SINGLE_TURNKEY",
				"single_turnkey": turnkey,
			},
		)

		self.assertEqual(result["implementation_model"], "SINGLE_TURNKEY")
		self.assertEqual(result["single_turnkey"], turnkey)
		self.assertEqual([row["phase_code"] for row in result["phases"]], phase_codes)
		self.assertEqual(result["completion"]["total_phases"], 1)
		self.assertEqual(result["completion"]["completed_phases"], 1)

		restored = save_implementation_schedule(SEED_CODE, {"implementation_model": "PHASED"})
		self.assertEqual(restored["implementation_model"], "PHASED")
		self.assertEqual([row["phase_code"] for row in restored["phases"]], phase_codes)

	def test_save_single_turnkey_rejects_missing_required_field(self) -> None:
		with self.assertRaisesRegex(frappe.ValidationError, "Unified acceptance criteria"):
			save_implementation_schedule(
				SEED_CODE,
				{
					"implementation_model": "SINGLE_TURNKEY",
					"single_turnkey": {
						"expected_delivery_duration": "6 Months",
						"delivery_trigger": "Contract signing",
						"key_deliverables": "Complete installed solution",
						"unified_acceptance_criteria": "",
						"evidence_required": "Handover certificate",
						"carry_forward_decision": "YES",
					},
				},
			)

	def test_get_returns_field_sources_with_editable_template_metadata(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		phase = next(row for row in payload["phases"] if row["phase_code"] == "PHASE_1")
		sources = phase.get("field_sources") or {}
		self.assertIn("duration_label", sources)
		self.assertEqual(sources["duration_label"]["source_type"], "TEMPLATE")
		self.assertEqual(sources["duration_label"]["source_label"], "Standard IT Schedule Template")
		self.assertTrue(sources["duration_label"]["editable"])
		self.assertFalse(sources["duration_label"]["locked"])
		self.assertEqual(sources["phase_code"]["locked"], True)
		self.assertEqual(sources["start_trigger"]["source_type"], "DERIVED")

	def test_get_returns_nested_milestones_per_phase(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		phase_2 = next(row for row in payload["phases"] if row["phase_code"] == "PHASE_2")
		self.assertTrue(phase_2["milestones"])
		types = {row["milestone_type"] for row in phase_2["milestones"]}
		self.assertIn("TESTING", types)
		self.assertIn("INTEGRATION", types)

	def test_seed_001_schedule_is_partially_complete_with_phase_3_gap(self) -> None:
		_ensure_implementation_schedule(SEED_CODE, {"instance_code": SEED_CODE})
		payload = get_implementation_schedule(SEED_CODE)
		completion = payload["completion"]
		self.assertEqual(completion["total_phases"], 3)
		self.assertLess(completion["completed_phases"], 3)
		self.assertGreater(completion["gaps"]["missing_acceptance_criteria"], 0)
		phase_3 = next(row for row in payload["phases"] if row["phase_code"] == "PHASE_3")
		self.assertNotEqual(phase_3["status"], "COMPLETE")
		oa = next(row for row in phase_3["milestones"] if row["milestone_type"] == "OPERATIONAL_ACCEPTANCE")
		self.assertEqual(oa["acceptance_label"], "Missing Criteria")

	def test_save_persists_drawer_fields_for_selected_phase(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		target = next(row for row in payload["phases"] if row["phase_code"] == "PHASE_2")
		target["key_deliverable_summary"] = "Integrated solution with signed SIT/UAT evidence and closure report."
		target["description"] = "Updated phase description from drawer save."
		target["carry_forward_to_contract"] = 1
		result = save_implementation_schedule(
			SEED_CODE,
			{"selected_phase_id": "PHASE_2", "selected_phase": target},
		)
		saved = next(row for row in result["phases"] if row["phase_code"] == "PHASE_2")
		self.assertIn("signed SIT/UAT evidence", saved["key_deliverable_summary"])
		self.assertIn("Updated phase description", saved["description"])
		self.assertEqual(saved["carry_forward_to_contract"], 1)

	def test_save_persists_selected_phase_milestone_fields(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		target = next(row for row in payload["phases"] if row["phase_code"] == "PHASE_2")
		milestone = next(row for row in target["milestones"] if row.get("acceptance_required"))
		milestone["acceptance_criteria_text"] = "Updated acceptance criteria from drawer."
		result = save_implementation_schedule(
			SEED_CODE,
			{"selected_phase_id": "PHASE_2", "selected_phase": target},
		)
		saved = next(row for row in result["phases"] if row["phase_code"] == "PHASE_2")
		saved_milestone = next(row for row in saved["milestones"] if row["milestone_code"] == milestone["milestone_code"])
		self.assertEqual(saved_milestone["acceptance_criteria_text"], "Updated acceptance criteria from drawer.")

	def test_validate_milestone_order_rejects_go_live_before_testing(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			_validate_milestone_order(
				[
					{
						"milestone_code": "BAD-GOLIVE",
						"milestone_type": "GO_LIVE",
						"display_order": 1,
					},
					{
						"milestone_code": "BAD-TEST",
						"milestone_type": "TESTING",
						"display_order": 5,
					},
				]
			)

	def test_validate_acceptance_criteria_rejects_missing_required_criteria(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			_validate_acceptance_criteria(
				[
					{
						"milestone_code": "PH3-OA",
						"acceptance_required": 1,
						"acceptance_criteria_text": "",
					}
				]
			)

	def test_save_rejects_go_live_before_testing(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		phases = payload["phases"]
		milestones = []
		for phase in phases:
			milestones.extend(phase["milestones"])
		for row in milestones:
			if row["milestone_type"] == "GO_LIVE":
				row["display_order"] = 1
			if row["milestone_type"] == "TESTING":
				row["display_order"] = 9
		with self.assertRaises(frappe.ValidationError):
			save_implementation_schedule(
				SEED_CODE,
				{"phases": phases, "milestones": milestones},
			)

	def test_save_rejects_missing_acceptance_criteria_when_required(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		phases = payload["phases"]
		milestones = []
		for phase in phases:
			milestones.extend(phase["milestones"])
		for row in milestones:
			if row["milestone_code"] == "PH3-OA":
				row["acceptance_required"] = 1
				row["acceptance_criteria_text"] = ""
		with self.assertRaises(frappe.ValidationError):
			save_implementation_schedule(
				SEED_CODE,
				{"phases": phases, "milestones": milestones},
			)

	def test_seed_003_schedule_is_complete(self) -> None:
		_ensure_implementation_schedule(SEED_COMPLETE_CODE, {"instance_code": SEED_COMPLETE_CODE})
		payload = get_implementation_schedule(SEED_COMPLETE_CODE)
		self.assertEqual(payload["completion"]["completed_phases"], payload["completion"]["total_phases"])
		self.assertEqual(payload["completion"]["gaps"]["missing_acceptance_criteria"], 0)
		phase_3 = next(row for row in payload["phases"] if row["phase_code"] == "PHASE_3")
		self.assertEqual(phase_3["status"], "COMPLETE")

	def test_save_complete_schedule_updates_step_status(self) -> None:
		payload = get_implementation_schedule(SEED_CODE)
		phases = []
		milestones = []
		for phase in payload["phases"]:
			complete_phase = dict(phase)
			if not complete_phase.get("key_deliverable_summary"):
				complete_phase["key_deliverable_summary"] = (
					f"Completed deliverables for {complete_phase['phase_code']}."
				)
			phases.append(complete_phase)
			for milestone in phase["milestones"]:
				complete_milestone = dict(milestone)
				if int(complete_milestone.get("acceptance_required") or 0) and not complete_milestone.get(
					"acceptance_criteria_text"
				):
					complete_milestone["acceptance_criteria_text"] = (
						f"Acceptance criteria for {complete_milestone['milestone_code']}."
					)
				milestones.append(complete_milestone)
		save_implementation_schedule(SEED_CODE, {"phases": phases, "milestones": milestones})
		step_status = frappe.db.get_value(
			"Wizard Step Instance",
			{"tender_std_instance": SEED_CODE, "step_code": IMPLEMENTATION_SCHEDULE_STEP_CODE},
			"status",
		)
		self.assertEqual(step_status, "COMPLETE")

	def test_compute_schedule_completion_counts_incomplete_phases(self) -> None:
		result = compute_schedule_completion(
			[
				{
					"phase_code": "PHASE_1",
					"status": "INCOMPLETE",
					"milestones": [{"status": "INCOMPLETE"}],
				}
			]
		)
		self.assertEqual(result["completed_phases"], 0)
		self.assertEqual(result["total_phases"], 1)

	def test_ensure_schedule_doc_is_idempotent(self) -> None:
		schedule_name = frappe.db.get_value(
			"Tender STD Implementation Schedule",
			{"tender_std_instance": SEED_CODE},
		)
		if schedule_name:
			frappe.delete_doc("Tender STD Implementation Schedule", schedule_name, force=True)
		first = _ensure_schedule_doc(SEED_CODE)
		second = _ensure_schedule_doc(SEED_CODE)
		self.assertEqual(first.name, second.name)
		self.assertEqual(
			frappe.db.count("Tender STD Implementation Schedule", {"tender_std_instance": SEED_CODE}),
			1,
		)

	def test_get_implementation_schedule_is_idempotent_when_doc_missing(self) -> None:
		schedule_name = frappe.db.get_value(
			"Tender STD Implementation Schedule",
			{"tender_std_instance": SEED_CODE},
		)
		if schedule_name:
			frappe.delete_doc("Tender STD Implementation Schedule", schedule_name, force=True)
		first = get_implementation_schedule(SEED_CODE)
		second = get_implementation_schedule(SEED_CODE)
		self.assertEqual(first["configuration_id"], second["configuration_id"])
		self.assertEqual(
			frappe.db.count("Tender STD Implementation Schedule", {"tender_std_instance": SEED_CODE}),
			1,
		)
