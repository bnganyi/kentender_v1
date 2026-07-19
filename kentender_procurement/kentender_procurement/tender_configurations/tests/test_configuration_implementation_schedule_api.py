# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-04 Implementation Schedule GET/POST contract tests (column-clarity amendment)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.implementation_schedule import (
	APPROACH_PHASED,
	APPROACH_SINGLE,
	MSG_EMPTY_PHASED,
	MSG_NAME,
	get_configuration_implementation_schedule,
	save_configuration_implementation_schedule,
)


def _complete_milestone(**overrides):
	base = {
		"name": "Project Kick-off and Detailed Work Plan",
		"description": "Mobilise the delivery team and agree the detailed work plan.",
		"expected_duration": "2 weeks",
		"start_trigger": "Contract signing and notice to proceed",
		"key_deliverable": "Approved implementation work plan",
		"deliverable_description": "Detailed work plan covering mobilisation and baseline schedule.",
		"acceptance_method": "PE confirms approved work plan",
		"evidence_expected": "Signed work plan approval",
	}
	base.update(overrides)
	return base


def _complete_single(**overrides):
	base = {
		"expected_delivery_duration": "6 months",
		"delivery_trigger": "Contract signing and notice to proceed",
		"key_deliverables": (
			"Fully supplied, installed, configured, tested, documented, and handed-over IT solution"
		),
		"acceptance_method": (
			"Procuring Entity confirms delivery, installation, testing, training, "
			"documentation, and operational readiness."
		),
		"evidence_expected": "Completion report, test results, training records, and handover certificate.",
		"notes_to_bidders": "",
	}
	base.update(overrides)
	return base


class TestConfigurationImplementationScheduleApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape(self):
		out = get_configuration_implementation_schedule(self.cfg_id)
		for key in (
			"configuration_id",
			"delivery_approach",
			"milestones",
			"single_delivery",
			"available_requirements",
			"next_milestone_id",
			"can_continue",
			"has_progress",
			"blockers",
			"column_contract",
			"options",
			"guidance",
		):
			self.assertIn(key, out)
		self.assertEqual(out["delivery_approach"], APPROACH_PHASED)
		self.assertEqual(out["next_milestone_id"], "MS-001")
		self.assertIn("days", out["options"]["duration_unit"])
		self.assertIn("weeks", out["options"]["duration_unit"])
		self.assertIn("Acceptance Method", out["column_contract"]["columns"])
		self.assertIn("Setup Status", out["column_contract"]["columns"])
		self.assertNotIn("Acceptance", out["column_contract"]["columns"])

	def test_empty_phased_cannot_continue(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{"delivery_approach": APPROACH_PHASED, "milestones": []},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_EMPTY_PHASED for b in out["blockers"]))

	def test_complete_milestone_can_continue(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [_complete_milestone()],
			},
		)
		self.assertTrue(out["can_continue"])
		row = out["milestones"][0]
		self.assertEqual(row["milestone_id"], "MS-001")
		self.assertEqual(row["setup_status_label"], "Complete")
		self.assertEqual(row["acceptance_method_display"], "PE confirms approved work plan")
		blob = frappe.as_json(
			{"a": row["acceptance_method_display"], "b": row["key_deliverable"]}
		).lower()
		self.assertNotIn("missing", blob)
		self.assertNotIn("acceptance defined", blob)

	def test_missing_name_blocker(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [_complete_milestone(name="")],
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_NAME for b in out["blockers"]))

	def test_diagnostic_phrase_rejected_as_acceptance_method(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [_complete_milestone(acceptance_method="Acceptance defined")],
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(
			any("acceptance method" in b["message"].lower() for b in out["blockers"])
		)

	def test_table_shows_content_not_status_in_method_column(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [_complete_milestone(acceptance_method="")],
			},
		)
		row = out["milestones"][0]
		self.assertEqual(row["setup_status_label"], "Needs attention")
		self.assertEqual(row["acceptance_method_display"], "—")
		self.assertNotIn("missing", row["acceptance_method_display"].lower())
		self.assertEqual(row["action_label"], "Fix")

	def test_single_turnkey_complete(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_SINGLE,
				"single_delivery": _complete_single(),
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["delivery_approach"], APPROACH_SINGLE)
		self.assertEqual(out["single_delivery"]["setup_status_label"], "Complete")

	def test_single_incomplete_blockers(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_SINGLE,
				"single_delivery": {"expected_delivery_duration": "6 months"},
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertGreater(len(out["blockers"]), 0)

	def test_approach_switch_preserves_drafts(self):
		save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [_complete_milestone()],
			},
		)
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_SINGLE,
				"single_delivery": _complete_single(),
			},
		)
		self.assertEqual(out["delivery_approach"], APPROACH_SINGLE)
		self.assertTrue(out["can_continue"])
		# Phased milestones retained in payload when not overwritten
		out2 = save_configuration_implementation_schedule(
			self.cfg_id,
			{"delivery_approach": APPROACH_PHASED},
		)
		self.assertEqual(out2["delivery_approach"], APPROACH_PHASED)
		self.assertEqual(len(out2["milestones"]), 1)
		self.assertEqual(out2["milestones"][0]["milestone_id"], "MS-001")
		self.assertTrue(out2["single_delivery"]["expected_delivery_duration"])

	def test_auto_ids_increment(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [
					_complete_milestone(name="One"),
					_complete_milestone(name="Two"),
				],
			},
		)
		ids = [r["milestone_id"] for r in out["milestones"]]
		self.assertEqual(ids, ["MS-001", "MS-002"])

	def test_duration_value_and_unit(self):
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [
					_complete_milestone(
						expected_duration="",
						expected_duration_value="4",
						expected_duration_unit="weeks",
					)
				],
			},
		)
		row = out["milestones"][0]
		self.assertEqual(row["expected_duration_value"], "4")
		self.assertEqual(row["expected_duration_unit"], "weeks")
		self.assertEqual(row["expected_duration"], "4 weeks")
		self.assertTrue(out["can_continue"])

	def test_related_requirement_ids_from_cfg03(self):
		from kentender_procurement.tender_configurations.services.it_requirements import (
			save_configuration_requirements,
		)

		save_configuration_requirements(
			self.cfg_id,
			{
				"requirements": [
					{
						"title": "Compute Node Performance",
						"category_label": "Technical Requirement",
						"treatment_label": "Mandatory",
						"bidder_response_format": "Yes/No confirmation",
						"bidder_response_instruction": "Confirm compliance.",
						"evidence_requirement": "Evidence required",
						"evidence_instruction": "Datasheet required",
						"delivery_confirmation_method": "Commissioning test report",
					}
				]
			},
		)
		out = save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [
					_complete_milestone(related_requirement_ids=["REQ-001"]),
				],
			},
		)
		row = out["milestones"][0]
		self.assertEqual(row["related_requirement_ids"], ["REQ-001"])
		self.assertTrue(row["related_requirement_refs"])
		self.assertEqual(row["related_requirement_refs"][0]["code"], "REQ-001")
		self.assertEqual(row["related_requirement_refs"][0]["name"], "Compute Node Performance")
		avail = get_configuration_implementation_schedule(self.cfg_id)["available_requirements"]
		self.assertTrue(any(r["code"] == "REQ-001" for r in avail))
