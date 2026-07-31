# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-09 STD-declared contract parameter readiness (structured keys only)."""

from __future__ import annotations

import unittest

from kentender_procurement.tender_configurations.services.contract_parameter_readiness import (
	assert_applicable_contract_parameters_resolved,
	resolve_contract_parameters,
)
from kentender_procurement.tender_configurations.services.preview_presentation import (
	assert_scc_values_complete,
	render_scc_section,
)


def _bound_row(parameter_id: str, parameter_code: str, **overrides):
	base = {
		"item_label": overrides.pop("item_label", parameter_id),
		"category": "SCC Value",
		"parameter_code": parameter_code,
		"readiness_parameter_id": parameter_id,
		"value_or_obligation": "",
	}
	base.update(overrides)
	return base


def _server_supply_context(**overrides):
	base = {
		"std_version": "",
		"contract_values": [
			_bound_row(
				"payment",
				"IT-SCC-014",
				item_label="Payment schedule category model",
				value_or_obligation="Milestone payment on delivery and acceptance",
			),
			_bound_row(
				"warranty",
				"IT-SCC-053",
				item_label="Warranty period",
				category="Support & Warranty",
				value_or_obligation="12 month warranty on hardware",
			),
			_bound_row(
				"performance_security",
				"IT-SCC-029",
				item_label="Performance security percentage",
				category="Securities & Guarantees",
				not_applicable=1,
				not_applicable_reason="Framework supply under existing PE security policy",
			),
		],
		"tds": {},
		"requirements": [
			{"title": "Rack-mount servers", "requirement_text": "Supply and install 20 servers"}
		],
		"milestones": [
			{
				"name": "Delivery",
				"expected_duration_value": "90",
				"expected_duration_unit": "days",
			}
		],
		"single_delivery": {},
		"delivery_approach": "Phased Delivery",
	}
	base.update(overrides)
	return base


class TestContractParameterReadiness(unittest.TestCase):
	def test_server_supply_does_not_require_conditional_topics(self):
		ctx = _server_supply_context()
		report = resolve_contract_parameters(**ctx)
		self.assertTrue(report["can_continue"], report["blockers"])
		na_ids = {p["parameter_id"] for p in report["not_applicable"]}
		self.assertIn("software_escrow", na_ids)
		self.assertIn("subcontracting", na_ids)
		self.assertIn("sla", na_ids)
		block = assert_scc_values_complete(
			ctx["contract_values"],
			tds=ctx["tds"],
			requirements=ctx["requirements"],
			milestones=ctx["milestones"],
		)
		self.assertIsNone(block)

	def test_does_not_match_rows_by_free_text_label(self):
		"""A row named Payment without STD binding must not satisfy IT-SCC-014."""
		ctx = _server_supply_context(
			contract_values=[
				{
					"item_label": "Payment schedule",
					"category": "SCC Value",
					"value_or_obligation": "40% delivery / 60% acceptance",
				},
				_bound_row(
					"warranty",
					"IT-SCC-053",
					value_or_obligation="12 months",
				),
				_bound_row(
					"performance_security",
					"IT-SCC-029",
					not_applicable=1,
					not_applicable_reason="N/A",
				),
			]
		)
		report = resolve_contract_parameters(**ctx)
		self.assertTrue(any(u["parameter_id"] == "payment" for u in report["unresolved"]))

	def test_escrow_required_only_when_applicability_enabled(self):
		ctx = _server_supply_context(tds={"software_escrow_required": "Yes"})
		report = resolve_contract_parameters(**ctx)
		self.assertFalse(report["can_continue"])
		self.assertTrue(any(u["parameter_id"] == "software_escrow" for u in report["unresolved"]))
		msg = next(u["message"] for u in report["unresolved"] if u["parameter_id"] == "software_escrow")
		self.assertEqual(msg, "Source code escrow terms are missing.")

		ctx["contract_values"] = list(ctx["contract_values"]) + [
			_bound_row(
				"software_escrow",
				"IT-SCC-035",
				value_or_obligation="Escrow deposit within 30 days of contract signing",
			)
		]
		report2 = resolve_contract_parameters(**ctx)
		self.assertTrue(report2["can_continue"], report2["blockers"])

	def test_sla_not_required_without_support_signal(self):
		ctx = _server_supply_context()
		report = resolve_contract_parameters(**ctx)
		self.assertNotIn("sla", {u["parameter_id"] for u in report["unresolved"]})

	def test_sla_required_when_requirements_enable_it(self):
		ctx = _server_supply_context(
			requirements=[
				{
					"title": "Managed support",
					"requirement_text": "Service Level Agreement (SLA) P1 response 4 hours",
				}
			]
		)
		report = resolve_contract_parameters(**ctx)
		self.assertFalse(report["can_continue"])
		self.assertTrue(any(u["parameter_id"] == "sla" for u in report["unresolved"]))

	def test_performance_security_resolved_by_cfg09_not_applicable(self):
		ctx = _server_supply_context()
		report = resolve_contract_parameters(**ctx)
		perf = next(r for r in report["resolved"] if r["parameter_id"] == "performance_security")
		self.assertEqual(perf["resolution"], "not_applicable")

	def test_performance_security_resolved_by_tds_not_applicable(self):
		ctx = _server_supply_context(
			contract_values=[
				r
				for r in _server_supply_context()["contract_values"]
				if r.get("readiness_parameter_id") != "performance_security"
			],
			tds={"performance_security_required": "Not applicable"},
		)
		report = resolve_contract_parameters(**ctx)
		self.assertTrue(report["can_continue"], report["blockers"])
		perf = next(r for r in report["resolved"] if r["parameter_id"] == "performance_security")
		self.assertEqual(perf["resolution"], "not_applicable")

	def test_performance_security_blocks_when_missing(self):
		ctx = _server_supply_context(
			contract_values=[
				r
				for r in _server_supply_context()["contract_values"]
				if r.get("readiness_parameter_id") != "performance_security"
			],
			tds={},
		)
		report = resolve_contract_parameters(**ctx)
		self.assertFalse(report["can_continue"])
		block = assert_applicable_contract_parameters_resolved(
			ctx["contract_values"],
			tds=ctx["tds"],
			requirements=ctx["requirements"],
			milestones=ctx["milestones"],
		)
		self.assertIsNotNone(block)
		self.assertEqual(block.get("message"), "Performance security value is missing.")

	def test_governing_law_does_not_invent_jurisdiction_text(self):
		ctx = _server_supply_context()
		report = resolve_contract_parameters(**ctx)
		for row in report["resolved"]:
			if row["parameter_id"] == "governing_law":
				self.assertNotIn("Laws of Kenya", row.get("value") or "")
		# With no bound STD clauses, governing law must not be silently invented as resolved.
		gov_resolved = [
			r for r in report["resolved"] if r["parameter_id"] == "governing_law"
		]
		self.assertEqual(gov_resolved, [])

	def test_commencement_resolved_from_single_turnkey_schedule(self):
		ctx = _server_supply_context(
			milestones=[],
			delivery_approach="Single Turnkey Delivery",
			single_delivery={
				"expected_delivery_duration": "1 months",
				"expected_duration_value": "1",
				"expected_duration_unit": "months",
				"delivery_trigger": "Contract signing and notice to proceed",
				"key_deliverables": "Installation of servers",
				"acceptance_method": "Commissioning test report",
				"evidence_expected": "99.9% uptime",
			},
		)
		report = resolve_contract_parameters(**ctx)
		commencement = next(
			r for r in report["resolved"] if r["parameter_id"] == "commencement"
		)
		self.assertEqual(commencement["resolution"], "authoritative_module")
		self.assertIn("Single turnkey", commencement["value"])

	def test_payment_blocker_is_succinct(self):
		ctx = _server_supply_context(
			contract_values=[
				r
				for r in _server_supply_context()["contract_values"]
				if r.get("readiness_parameter_id") != "payment"
			]
		)
		report = resolve_contract_parameters(**ctx)
		pay = next(u for u in report["unresolved"] if u["parameter_id"] == "payment")
		self.assertEqual(pay["message"], "Payment schedule value is missing.")
		self.assertLess(len(pay["message"]), 80)

	def test_categories_are_not_missing_topic_keys(self):
		block = assert_scc_values_complete(
			[],
			tds={"performance_security_required": "No"},
			requirements=[{"title": "Servers"}],
			milestones=[
				{"name": "Go-live", "expected_duration_value": "6", "expected_duration_unit": "months"}
			],
		)
		msg = (block or {}).get("message") or ""
		self.assertNotIn("Support & Warranty", msg)
		self.assertNotIn("missing topics:", msg)
		self.assertNotIn("Laws of Kenya", msg)

	def test_placeholder_value_still_blocks(self):
		block = assert_scc_values_complete(
			[
				_bound_row(
					"payment",
					"IT-SCC-014",
					value_or_obligation="As specified",
				)
			],
			tds={"performance_security_required": "No"},
			requirements=[{"title": "Servers"}],
			milestones=[
				{"name": "Go-live", "expected_duration_value": "6", "expected_duration_unit": "months"}
			],
		)
		self.assertIsNotNone(block)
		msg = (block.get("message") or "").lower()
		self.assertTrue(
			"placeholder" in msg or "payment schedule value is missing" in msg,
			msg,
		)

	def test_render_scc_with_resolved_server_supply(self):
		ctx = _server_supply_context()
		html, err = render_scc_section(
			ctx["contract_values"],
			tds=ctx["tds"],
			requirements=ctx["requirements"],
			milestones=ctx["milestones"],
		)
		self.assertIsNone(err)
		self.assertIn("Payment schedule", html)


if __name__ == "__main__":
	unittest.main()
