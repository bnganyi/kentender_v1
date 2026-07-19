# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-09 Contract Values GET/POST contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.contract_values import (
	MSG_EMPTY,
	MSG_LABEL,
	MSG_SOURCE,
	MSG_VALUE,
	SETUP_NEEDS_ATTENTION,
	SETUP_REVIEW,
	get_configuration_contract_values,
	save_configuration_contract_values,
)


def _complete_row(**overrides):
	base = {
		"item_label": "Delivery Period",
		"category": "SCC Value",
		"source_screen": "Implementation Schedule",
		"contract_location": "SCC / Delivery Schedule",
		"value_or_obligation": "90 calendar days from notice to proceed",
		"editable_here": 1,
	}
	base.update(overrides)
	return base


class TestConfigurationContractValuesApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape(self):
		out = get_configuration_contract_values(self.cfg_id)
		for key in (
			"configuration_id",
			"contract_values",
			"can_continue",
			"guidance",
			"options",
			"context",
			"tabs",
		):
			self.assertIn(key, out)

	def test_empty_cannot_continue(self):
		out = save_configuration_contract_values(self.cfg_id, {"contract_values": []})
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_EMPTY for b in out["blockers"]))

	def test_complete_row_can_continue(self):
		out = save_configuration_contract_values(
			self.cfg_id, {"contract_values": [_complete_row()]}
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["blocker_count"], 0)
		self.assertEqual(out["contract_values"][0]["contract_value_id"], "CV-001")
		self.assertEqual(out["contract_values"][0]["status"], "Complete")

	def test_missing_label_blocker(self):
		out = save_configuration_contract_values(
			self.cfg_id,
			{"contract_values": [_complete_row(item_label="")]},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_LABEL for b in out["blockers"]))

	def test_missing_value_blocker(self):
		out = save_configuration_contract_values(
			self.cfg_id,
			{"contract_values": [_complete_row(value_or_obligation="")]},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_VALUE for b in out["blockers"]))

	def test_missing_source_needs_attention(self):
		out = save_configuration_contract_values(
			self.cfg_id,
			{
				"contract_values": [
					_complete_row(
						item_label="Warranty Period",
						source_screen="",
						value_or_obligation="12 months",
					)
				]
			},
		)
		row = out["contract_values"][0]
		self.assertEqual(row["status"], SETUP_NEEDS_ATTENTION)
		self.assertTrue(any(b["message"] == MSG_SOURCE for b in out["blockers"]))

	def test_hydrate_suggests_upstream_drafts(self):
		out = save_configuration_contract_values(
			self.cfg_id, {"contract_values": [], "hydrate": 1}
		)
		self.assertGreaterEqual(len(out["contract_values"]), 4)
		ids = [r["contract_value_id"] for r in out["contract_values"]]
		self.assertTrue(all(i.startswith("CV-") for i in ids))
		labels = {r["item_label"] for r in out["contract_values"]}
		self.assertIn("Performance Security", labels)

	def test_residency_warning_review_status(self):
		out = save_configuration_contract_values(
			self.cfg_id,
			{
				"contract_values": [
					_complete_row(
						item_label="Data Residency",
						category="Security & Compliance Obligation",
						source_screen="IT Requirements",
						contract_location="Contract Schedule: Security",
						value_or_obligation="Production data must remain in Kenya",
						review_note="Review before handoff",
					)
				]
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["contract_values"][0]["status"], SETUP_REVIEW)
		self.assertGreaterEqual(out["warning_count"], 1)

	def test_forbidden_keys_stripped(self):
		out = save_configuration_contract_values(
			self.cfg_id,
			{
				"contract_values": [
					{
						**_complete_row(),
						"gcc_text": "secret",
						"schema_version": "9",
						"award_decision": "x",
					}
				]
			},
		)
		row = out["contract_values"][0]
		self.assertNotIn("gcc_text", row)
		self.assertNotIn("schema_version", row)
		self.assertNotIn("award_decision", row)

	def test_auto_ids_increment(self):
		out = save_configuration_contract_values(
			self.cfg_id,
			{
				"contract_values": [
					_complete_row(item_label="A"),
					_complete_row(item_label="B", category="Delivery Obligation"),
				]
			},
		)
		ids = [r["contract_value_id"] for r in out["contract_values"]]
		self.assertEqual(ids, ["CV-001", "CV-002"])
