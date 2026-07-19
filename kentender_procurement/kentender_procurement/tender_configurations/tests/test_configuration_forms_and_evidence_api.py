# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-08 Forms & Evidence GET/POST contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.forms_and_evidence import (
	MSG_CONDITION,
	MSG_EMPTY,
	MSG_INSTRUCTION,
	MSG_NAME,
	MSG_NA_REASON,
	get_configuration_forms_and_evidence,
	save_configuration_forms_and_evidence,
)


def _complete_mandatory(**overrides):
	base = {
		"item_name": "Form of Tender",
		"category": "Standard Form",
		"source": "STD",
		"requirement": "Mandatory",
		"bidder_instruction": "Bidder must complete and sign the Form of Tender.",
		"accepted_response_format": "Form",
	}
	base.update(overrides)
	return base


def _complete_conditional(**overrides):
	base = {
		"item_name": "Tender Security",
		"category": "Tender Security",
		"source": "TDS",
		"requirement": "Conditional",
		"condition_text": "Required where the TDS specifies tender security.",
		"condition_source": "TDS",
		"bidder_instruction": "Provide tender security in the form stated in the TDS.",
		"accepted_response_format": "PDF attachment",
	}
	base.update(overrides)
	return base


class TestConfigurationFormsAndEvidenceApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape(self):
		out = get_configuration_forms_and_evidence(self.cfg_id)
		for key in (
			"configuration_id",
			"submission_items",
			"can_continue",
			"guidance",
			"options",
			"context",
			"summary",
		):
			self.assertIn(key, out)

	def test_empty_cannot_continue(self):
		out = save_configuration_forms_and_evidence(self.cfg_id, {"submission_items": []})
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_EMPTY for b in out["blockers"]))

	def test_complete_items_can_continue(self):
		out = save_configuration_forms_and_evidence(
			self.cfg_id,
			{"submission_items": [_complete_mandatory(), _complete_conditional()]},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["summary"]["mandatory_items"], 1)
		self.assertEqual(out["summary"]["conditional_items"], 1)

	def test_missing_name_blocker(self):
		row = _complete_mandatory()
		row["item_name"] = ""
		out = save_configuration_forms_and_evidence(
			self.cfg_id, {"submission_items": [row]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_NAME for b in out["blockers"]))

	def test_mandatory_without_instruction_blocker(self):
		row = _complete_mandatory()
		row["bidder_instruction"] = ""
		out = save_configuration_forms_and_evidence(
			self.cfg_id, {"submission_items": [row]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_INSTRUCTION for b in out["blockers"]))

	def test_conditional_without_condition_blocker(self):
		row = _complete_conditional()
		row["condition_text"] = ""
		out = save_configuration_forms_and_evidence(
			self.cfg_id, {"submission_items": [row]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_CONDITION for b in out["blockers"]))

	def test_not_applicable_requires_reason(self):
		out = save_configuration_forms_and_evidence(
			self.cfg_id,
			{
				"submission_items": [
					_complete_mandatory(
						requirement="Not Applicable",
						not_applicable_reason="",
						bidder_instruction="",
					)
				]
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_NA_REASON for b in out["blockers"]))

	def test_import_standard_forms(self):
		out = save_configuration_forms_and_evidence(
			self.cfg_id, {"submission_items": [], "import": 1}
		)
		self.assertGreaterEqual(len(out["submission_items"]), 4)
		ids = [r["item_id"] for r in out["submission_items"]]
		self.assertTrue(all(i.startswith("FE-") for i in ids))
		names = {r["item_name"] for r in out["submission_items"]}
		self.assertIn("Form of Tender", names)
		# Conditional tender-security draft needs condition+instruction (seeded) — can continue
		self.assertTrue(out["can_continue"])

	def test_auto_ids_increment(self):
		out = save_configuration_forms_and_evidence(
			self.cfg_id,
			{
				"submission_items": [
					_complete_mandatory(item_name="One"),
					_complete_conditional(item_name="Two"),
				]
			},
		)
		ids = [r["item_id"] for r in out["submission_items"]]
		self.assertEqual(ids, ["FE-001", "FE-002"])

	def test_forbidden_keys_stripped(self):
		out = save_configuration_forms_and_evidence(
			self.cfg_id,
			{
				"submission_items": [
					_complete_mandatory(
						bidder_upload="secret.pdf",
						schema_version="9",
						rule_id="R-1",
					)
				]
			},
		)
		row = out["submission_items"][0]
		self.assertNotIn("bidder_upload", row)
		self.assertNotIn("schema_version", row)
		self.assertNotIn("rule_id", row)
