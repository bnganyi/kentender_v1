# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §9 — the owner contracts this module depends on, pinned
from the consumer's side (REQ19-AC-056/057/069). A signature change in
Planning or Budget fails here before it reaches a live authorisation."""

from __future__ import annotations

import ast
import inspect
import unittest

from kentender_budget.services import budget_check_reserve_contracts as budget_cr
from kentender_procurement.procurement_planning.services import outcome_event, plan_requisition


def _params(fn) -> set[str]:
	return set(inspect.signature(fn).parameters)


class TestPlanningContracts(unittest.TestCase):
	def test_the_one_canonical_drawdown_command_takes_the_whole_authorisation_context(self):
		params = _params(plan_requisition.authorise_requisition_drawdown)
		self.assertTrue({"plan_item_id", "requisition_reference", "requisition_version", "correlation_id", "allocations", "expected_record_version", "idempotency_key"} <= params)
		self.assertNotIn("requesting_org_unit", params)
		self.assertFalse(hasattr(plan_requisition, "record_requisition_drawdown"))

	def test_published_reads_used_instead_of_planning_tables(self):
		self.assertEqual(_params(plan_requisition.list_requisition_drawdowns), {"requisition_reference", "user"})
		self.assertEqual(_params(plan_requisition.correction_request_facts), {"correction_request", "requisition_reference"})

	def test_the_outcome_event_schema_is_v1(self):
		self.assertEqual(outcome_event.SCHEMA_VERSION, 1)
		self.assertEqual(outcome_event.HOOK, "kt_plan_item_correction_outcome_consumers")
		source = inspect.getsource(outcome_event.build)
		for field in ("event_id", "schema_version", "producer_sequence", "correction_request_id", "requesting_requisition_id", "requesting_requisition_version_id", "plan_item_id", "requested_plan_version_id", "requested_plan_item_version_id", "outcome", "reason", "correcting_plan_version_id", "replacement_lineage", "actor", "decision_at", "item_hold_state", "unresolved_request_count", "eligibility_revision"):
			self.assertIn(f'"{field}"', source, field)


class TestBudgetContracts(unittest.TestCase):
	def test_check_funding_takes_the_complete_array_with_caller_identity(self):
		self.assertTrue({"plan_item", "plan_version", "source_set_hash", "allocations", "correlation_id", "calling_module", "caller_reference"} <= _params(budget_cr.check_funding))

	def test_reservation_results_carry_the_drawdown_line(self):
		tree = ast.parse(inspect.getsource(budget_cr._reservation_result))
		keys = {k.value for node in ast.walk(tree) if isinstance(node, ast.Dict) for k in node.keys if isinstance(k, ast.Constant)}
		self.assertTrue({"reservation_id", "reservation_code", "drawdown_line_id", "original_amount", "caller_reference"} <= keys)
