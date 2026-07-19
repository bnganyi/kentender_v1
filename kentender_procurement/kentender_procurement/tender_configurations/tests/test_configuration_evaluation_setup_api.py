# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-07 Evaluation Setup GET/POST contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cstr

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.evaluation_setup import (
	MSG_EMPTY,
	MSG_FIN_RULE,
	MSG_MARKS,
	MSG_NAME,
	MSG_TECH_PASS,
	MSG_WORDING,
	get_configuration_evaluation_setup,
	save_configuration_evaluation_setup,
)


def _complete_pass_fail(**overrides):
	base = {
		"criterion_name": "Tender security submitted",
		"stage": "Preliminary",
		"evaluation_basis": "Pass/Fail",
		"source_type": "TDS",
		"bidder_facing_wording": (
			"The tender security must be submitted in the required form and amount."
		),
		"pass_fail_rule": "Must be submitted in required form and amount",
		"bidder_evidence": "Required",
		"evidence_instruction": "Provide tender security as specified in the TDS.",
	}
	base.update(overrides)
	return base


def _complete_financial(**overrides):
	base = {
		"criterion_name": "Financial comparison",
		"stage": "Financial",
		"evaluation_basis": "Lowest evaluated price",
		"source_type": "Price Schedule",
		"bidder_facing_wording": (
			"Bids will be compared using the lowest evaluated price from the Price Schedule."
		),
		"financial_evaluation_rule": (
			"Compare evaluated price including required recurrent costs."
		),
		"bidder_evidence": "Not required",
	}
	base.update(overrides)
	return base


def _complete_scored(**overrides):
	base = {
		"criterion_name": "Compute node technical compliance",
		"stage": "Technical",
		"evaluation_basis": "Scored",
		"source_type": "IT Requirement",
		"bidder_facing_wording": "Compute nodes must meet the stated technical specification.",
		"marks": "100",
		"bidder_evidence": "Required",
		"evidence_instruction": "Provide datasheets demonstrating compliance.",
	}
	base.update(overrides)
	return base


class TestConfigurationEvaluationSetupApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape(self):
		out = get_configuration_evaluation_setup(self.cfg_id)
		for key in (
			"configuration_id",
			"criteria",
			"can_continue",
			"scoring_summary",
			"options",
			"context",
			"technical_marks_total",
			"minimum_technical_score",
		):
			self.assertIn(key, out)

	def test_empty_cannot_continue(self):
		out = save_configuration_evaluation_setup(self.cfg_id, {"criteria": []})
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_EMPTY for b in out["blockers"]))

	def test_complete_criteria_can_continue(self):
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [_complete_pass_fail(), _complete_financial()],
			},
		)
		self.assertTrue(out["can_continue"])

	def test_missing_name_blocker(self):
		row = _complete_pass_fail()
		row["criterion_name"] = ""
		out = save_configuration_evaluation_setup(
			self.cfg_id, {"criteria": [row, _complete_financial()]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_NAME for b in out["blockers"]))

	def test_missing_wording_blocker(self):
		row = _complete_pass_fail()
		row["bidder_facing_wording"] = ""
		out = save_configuration_evaluation_setup(
			self.cfg_id, {"criteria": [row, _complete_financial()]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_WORDING for b in out["blockers"]))

	def test_scored_without_marks_blocker(self):
		row = _complete_scored(marks="")
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [row, _complete_financial()],
				"minimum_technical_score": "75",
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_MARKS for b in out["blockers"]))

	def test_financial_required(self):
		out = save_configuration_evaluation_setup(
			self.cfg_id, {"criteria": [_complete_pass_fail()]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_FIN_RULE for b in out["blockers"]))

	def test_scoring_summary_for_scored_technical(self):
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [_complete_scored(), _complete_financial()],
				"technical_marks_total": 100,
				"minimum_technical_score": "75",
			},
		)
		self.assertTrue(out["can_continue"])
		summary = out["scoring_summary"]
		self.assertTrue(summary["show_scoring_summary"])
		self.assertEqual(summary["allocated_technical_marks"], 100)
		self.assertEqual(cstr(summary["minimum_technical_score"]), "75")
		self.assertEqual(summary["technical_scoring_total"], 100)
		# Not stored on criteria rows
		for row in out["criteria"]:
			self.assertNotIn("technical_pass_mark", row)

	def test_tech_allocation_blocker_explains_remaining_marks(self):
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [
					_complete_scored(marks="25"),
					_complete_financial(),
				],
				"technical_marks_total": 100,
				"minimum_technical_score": "75",
			},
		)
		self.assertFalse(out["can_continue"])
		msg = next(b["message"] for b in out["blockers"] if b["code"] == "tech_total")
		self.assertEqual(
			msg,
			"Complete the remaining technical scored criteria so allocated marks equal 100.",
		)
		self.assertEqual(out["scoring_summary"]["marks_remaining"], 75)
		self.assertEqual(out["scoring_summary"]["setup_status"], "Needs attention")

	def test_minimum_technical_score_is_tender_level_only(self):
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [
					_complete_scored(criterion_name="A", marks="50"),
					_complete_scored(criterion_name="B", marks="50"),
					_complete_financial(),
				],
				"minimum_technical_score": "70",
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(cstr(out["minimum_technical_score"]), "70")
		self.assertEqual(cstr(out["scoring_summary"]["minimum_technical_score"]), "70")
		for row in out["criteria"]:
			self.assertNotIn("technical_pass_mark", row)

	def test_missing_minimum_technical_score_blocker(self):
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [_complete_scored(), _complete_financial()],
				"minimum_technical_score": "",
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_TECH_PASS for b in out["blockers"]))

	def test_legacy_per_criterion_pass_mark_is_lifted_to_blob(self):
		"""Old clients that sent pass mark on a criterion still populate tender-level field."""
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [
					_complete_scored(marks="100", technical_pass_mark="75"),
					_complete_financial(),
				],
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(cstr(out["scoring_summary"]["minimum_technical_score"]), "75")
		for row in out["criteria"]:
			self.assertNotIn("technical_pass_mark", row)

	def test_import_suggested_criteria(self):
		from kentender_procurement.tender_configurations.services.it_requirements import (
			save_configuration_requirements,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_it_requirements_api import (
			_complete_requirement,
		)

		save_configuration_requirements(
			self.cfg_id, {"requirements": [_complete_requirement()]}
		)
		before = get_configuration_evaluation_setup(self.cfg_id)
		self.assertGreaterEqual(before["import_candidate_count"], 1)
		out = save_configuration_evaluation_setup(
			self.cfg_id, {"criteria": [], "import": 1}
		)
		self.assertGreaterEqual(len(out["criteria"]), 2)
		stages = {r["stage"] for r in out["criteria"]}
		self.assertIn("Financial", stages)
		self.assertFalse(out["can_continue"])

	def test_auto_ids_increment(self):
		out = save_configuration_evaluation_setup(
			self.cfg_id,
			{
				"criteria": [
					_complete_pass_fail(criterion_name="One"),
					_complete_financial(criterion_name="Two"),
				]
			},
		)
		ids = [r["criterion_id"] for r in out["criteria"]]
		self.assertEqual(ids, ["EVAL-001", "EVAL-002"])
		self.assertEqual(out["summary"]["total_criteria"], 2)
