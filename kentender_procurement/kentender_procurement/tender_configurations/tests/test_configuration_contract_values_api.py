# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-09 Contract Values GET/POST contract tests."""

from __future__ import annotations

import json

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


def _resolved_applicable_rows():
	"""Minimal CFG-09 set that satisfies STD-declared applicable parameters."""
	return [
		_complete_row(
			item_label="Payment schedule category model",
			value_or_obligation="Milestone payment on delivery and acceptance",
			parameter_code="IT-SCC-014",
			readiness_parameter_id="payment",
		),
		_complete_row(
			item_label="Warranty period and excluded/included support services",
			category="Support & Warranty",
			source_screen="IT Requirements",
			value_or_obligation="12 month warranty",
			parameter_code="IT-SCC-053",
			readiness_parameter_id="warranty",
		),
		_complete_row(
			item_label="Performance security percentage",
			category="Securities & Guarantees",
			source_screen="Tender Data Sheet",
			not_applicable=1,
			not_applicable_reason="Not required for this supply package",
			value_or_obligation="",
			parameter_code="IT-SCC-029",
			readiness_parameter_id="performance_security",
		),
		_complete_row(
			parameter_code="IT-SCC-011",
			readiness_parameter_id="commencement",
		),
	]


class TestConfigurationContractValuesApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		# Upstream modules used to resolve Scope / Commencement without CFG-09 topic hacks.
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"it_requirements": json.dumps(
					{
						"requirements": [
							{
								"title": "Server supply",
								"requirement_text": "Supply and install rack servers",
							}
						]
					}
				),
				"implementation_schedule": json.dumps(
					{
						"milestones": [
							{
								"name": "Delivery",
								"expected_duration_value": "90",
								"expected_duration_unit": "days",
							}
						]
					}
				),
			},
			update_modified=False,
		)

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
			self.cfg_id, {"contract_values": _resolved_applicable_rows()}
		)
		self.assertTrue(out["can_continue"], out.get("blockers"))
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

	def test_hydrate_does_not_invent_pack_sample_rows(self):
		out = save_configuration_contract_values(
			self.cfg_id, {"contract_values": [], "hydrate": 1}
		)
		labels = {r["item_label"] for r in out["contract_values"]}
		# Pack §12 sample inventions must never appear as hydrate seeds.
		self.assertNotIn("Data Residency", labels)
		self.assertNotIn("On-site Support", labels)
		self.assertNotIn("Contract Attachments", labels)
		for row in out["contract_values"]:
			self.assertNotEqual(
				(row.get("value_or_obligation") or "").strip(),
				"Production data must remain in Kenya unless otherwise approved",
			)
			if out["contract_values"]:
				self.assertTrue(
					row.get("parameter_code") or row.get("readiness_parameter_id"),
					msg=row,
				)

	def test_residency_warning_review_status(self):
		rows = _resolved_applicable_rows()
		rows.append(
			_complete_row(
				item_label="Data Residency",
				category="Security & Compliance Obligation",
				source_screen="IT Requirements",
				contract_location="Contract Schedule: Security",
				value_or_obligation="Production data must remain in Kenya",
				review_note="Review before handoff",
			)
		)
		out = save_configuration_contract_values(
			self.cfg_id,
			{"contract_values": rows},
		)
		self.assertTrue(out["can_continue"], out.get("blockers"))
		residency = next(r for r in out["contract_values"] if r["item_label"] == "Data Residency")
		self.assertEqual(residency["status"], SETUP_REVIEW)
		self.assertGreaterEqual(out["warning_count"], 1)

	def test_forbidden_keys_stripped(self):
		rows = _resolved_applicable_rows()
		rows[0] = {
			**rows[0],
			"gcc_text": "secret",
			"schema_version": "9",
			"award_decision": "x",
		}
		out = save_configuration_contract_values(
			self.cfg_id,
			{"contract_values": rows},
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

	def test_conditional_escrow_not_forced_on_ordinary_supply(self):
		out = save_configuration_contract_values(
			self.cfg_id, {"contract_values": _resolved_applicable_rows()}
		)
		self.assertTrue(out["can_continue"], out.get("blockers"))
		joined = " ".join(b.get("message") or "" for b in out["blockers"]).lower()
		self.assertNotIn("escrow", joined)
		self.assertNotIn("subcontract", joined)
		self.assertNotIn("sla", joined)
