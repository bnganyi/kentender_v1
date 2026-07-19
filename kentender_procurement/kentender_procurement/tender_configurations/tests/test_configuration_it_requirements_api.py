# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-03 IT Requirements GET/POST contract tests (column-clarity amendment)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.it_requirements import (
	MSG_DELIVERY_METHOD,
	MSG_EMPTY,
	MSG_TITLE,
	get_configuration_requirements,
	save_configuration_requirements,
)


def _complete_requirement(**overrides):
	base = {
		"title": "Compute Node Performance",
		"description": (
			"Bidder must propose compute nodes that meet the stated processor, "
			"memory, storage, and redundancy requirements."
		),
		"category_label": "Technical Requirement",
		"treatment_label": "Mandatory",
		"bidder_response_format": "Yes/No confirmation",
		"bidder_response_instruction": "Bidder must confirm compliance with the stated compute specification.",
		"evidence_requirement": "Evidence required",
		"evidence_instruction": "Manufacturer datasheet required",
		"delivery_confirmation_method": "Commissioning test report",
	}
	base.update(overrides)
	return base


class TestConfigurationItRequirementsApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape(self):
		out = get_configuration_requirements(self.cfg_id)
		for key in (
			"configuration_id",
			"requirements",
			"next_requirement_id",
			"can_continue",
			"has_progress",
			"blockers",
			"column_contract",
			"options",
			"guidance",
		):
			self.assertIn(key, out)
		self.assertEqual(out["next_requirement_id"], "REQ-001")
		self.assertIn("Delivery Confirmation Method", out["column_contract"]["columns"])
		self.assertIn("Setup Status", out["column_contract"]["columns"])
		self.assertNotIn("Acceptance", out["column_contract"]["columns"])

	def test_empty_cannot_continue(self):
		out = save_configuration_requirements(self.cfg_id, {"requirements": []})
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_EMPTY for b in out["blockers"]))

	def test_complete_requirement_can_continue(self):
		out = save_configuration_requirements(
			self.cfg_id, {"requirements": [_complete_requirement()]}
		)
		self.assertTrue(out["can_continue"])
		row = out["requirements"][0]
		self.assertEqual(row["requirement_id"], "REQ-001")
		self.assertEqual(row["setup_status_label"], "Complete")
		self.assertEqual(row["delivery_confirmation_method_display"], "Commissioning test report")
		self.assertEqual(
			row["bidder_response_instruction_display"],
			"Bidder must confirm compliance with the stated compute specification.",
		)
		self.assertEqual(row["evidence_instruction_display"], "Manufacturer datasheet required")
		# Instruction columns must not show diagnostic phrases
		blob = frappe.as_json(
			{
				"a": row["delivery_confirmation_method_display"],
				"b": row["bidder_response_instruction_display"],
				"c": row["evidence_instruction_display"],
			}
		).lower()
		self.assertNotIn("missing", blob)
		self.assertNotIn("acceptance defined", blob)

	def test_missing_title_blocker(self):
		out = save_configuration_requirements(
			self.cfg_id, {"requirements": [_complete_requirement(title="")]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_TITLE for b in out["blockers"]))

	def test_delivery_method_required(self):
		out = save_configuration_requirements(
			self.cfg_id,
			{"requirements": [_complete_requirement(delivery_confirmation_method="")]},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_DELIVERY_METHOD for b in out["blockers"]))

	def test_diagnostic_phrase_rejected_as_delivery_method(self):
		out = save_configuration_requirements(
			self.cfg_id,
			{
				"requirements": [
					_complete_requirement(delivery_confirmation_method="Acceptance defined")
				]
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(
			any("delivery confirmation method" in b["message"].lower() for b in out["blockers"])
		)

	def test_informational_with_not_required_method(self):
		out = save_configuration_requirements(
			self.cfg_id,
			{
				"requirements": [
					_complete_requirement(
						title="Existing System Context",
						treatment_label="Informational",
						bidder_response_format="Not required",
						bidder_response_instruction="",
						evidence_requirement="No evidence required",
						evidence_instruction="",
						delivery_confirmation_method="Not required",
					)
				]
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["requirements"][0]["action_label"], "Review")
		self.assertEqual(
			out["requirements"][0]["delivery_confirmation_method_display"], "Not required"
		)

	def test_table_shows_content_not_status_in_method_column(self):
		out = save_configuration_requirements(
			self.cfg_id,
			{
				"requirements": [
					_complete_requirement(
						title="Redundant Power Supply Units",
						bidder_response_instruction="Bidder must confirm compliance",
						evidence_instruction="Datasheet required",
						delivery_confirmation_method="",
					)
				]
			},
		)
		row = out["requirements"][0]
		self.assertEqual(row["setup_status_label"], "Needs attention")
		self.assertEqual(row["delivery_confirmation_method_display"], "—")
		self.assertNotIn("missing", row["delivery_confirmation_method_display"].lower())
		self.assertEqual(row["action_label"], "Fix")
		self.assertTrue(row["issue_summary"])

	def test_forbidden_keys_ignored(self):
		out = save_configuration_requirements(
			self.cfg_id,
			{
				"requirements": [
					_complete_requirement(
						std_version_hash="secret-hash",
						binding_id="bind-1",
						marks="99",
					)
				]
			},
		)
		self.assertTrue(out["can_continue"])
		blob = frappe.as_json(out).lower()
		self.assertNotIn("secret-hash", blob)

	def test_auto_ids_increment(self):
		out = save_configuration_requirements(
			self.cfg_id,
			{
				"requirements": [
					_complete_requirement(title="One"),
					_complete_requirement(title="Two"),
				]
			},
		)
		ids = [r["requirement_id"] for r in out["requirements"]]
		self.assertEqual(ids, ["REQ-001", "REQ-002"])
