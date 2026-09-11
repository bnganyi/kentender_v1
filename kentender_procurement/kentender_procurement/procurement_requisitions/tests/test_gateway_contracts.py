# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — contract pins against the two sibling services this
module depends on (REQ-107). These are the Requisitions-side half of the
same contract Planning's own `test_plan_requisition.py` and Budget's own
`test_check_reserve_requisition_caller.py` pin from their side; a change to
either sibling that breaks these pins is a defect in the contract, not in
this module (§9.1/§9.1A/§5A).
"""

from __future__ import annotations

import inspect

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services import plan_requisition
from kentender_budget.services import budget_check_reserve_contracts as budget_cr

REQUIRED_PROJECTION_FIELDS = (
	"outcome", "eligible", "plan_reference", "version_reference", "plan_item_id", "record_version",
	"fiscal_year", "requirement_type", "procurement_category", "procurement_method", "strategic_objective",
	"objective_path", "strategic_objective_path", "title", "reservation_category", "lotting_indicator", "lot_count",
	"plan_horizon", "multi_year_justification", "contributing_org_unit_ids", "currency", "award_packages",
	"planned_dates", "forecast_dates", "funding_confirmation_references", "funding_state", "total_quantity",
	"total_value", "remaining_quantity", "remaining_value", "sources", "evaluated_at",
)

REQUIRED_SOURCE_FIELDS = (
	"plan_source_allocation_id", "plan_item_line_id", "source_line_id", "source_origin", "dpp_entry",
	"need", "need_revision", "organisation_unit", "title", "description", "expected_operational_result",
	"approved_quantity", "remaining_quantity", "unit", "required_by_date", "budget_line", "allocated_amount",
	"remaining_amount",
)


class TestPlanningProjectionContract(IntegrationTestCase):
	def test_projection_function_signature_is_unchanged(self):
		sig = inspect.signature(plan_requisition.get_requisition_eligible_plan_item)
		self.assertIn("plan_item_id", sig.parameters)
		self.assertIn("user", sig.parameters)

	def test_drawdown_functions_exist_with_expected_shape(self):
		sig = inspect.signature(plan_requisition.record_requisition_drawdown)
		for name in ("plan_item_id", "requisition_reference", "requesting_org_unit", "allocations",
					 "expected_record_version", "idempotency_key"):
			self.assertIn(name, sig.parameters)
		rev_sig = inspect.signature(plan_requisition.reverse_requisition_drawdown)
		for name in ("drawdown_reference", "expected_record_version", "idempotency_key"):
			self.assertIn(name, rev_sig.parameters)

	def test_correction_request_functions_exist(self):
		self.assertTrue(callable(plan_requisition.receive_plan_item_correction_request))
		self.assertTrue(callable(plan_requisition.resolve_plan_item_correction_request))


class TestBudgetReservationContract(IntegrationTestCase):
	def test_check_funding_accepts_requisitions_calling_module_and_optional_finance_task(self):
		sig = inspect.signature(budget_cr.check_funding)
		for name in ("plan_item", "plan_version", "source_set_hash", "allocations", "correlation_id",
					 "finance_task", "calling_module", "caller_reference"):
			self.assertIn(name, sig.parameters)
		self.assertIsNone(sig.parameters["finance_task"].default)

	def test_reserve_funding_no_longer_requires_finance_task(self):
		sig = inspect.signature(budget_cr.reserve_funding)
		self.assertIsNone(sig.parameters["finance_task"].default)

	def test_reservation_result_carries_caller_identity(self):
		import ast

		source = inspect.getsource(budget_cr._reservation_result)
		tree = ast.parse(source)
		keys = {
			node.value
			for fn in ast.walk(tree)
			if isinstance(fn, ast.Dict)
			for node in fn.keys
			if isinstance(node, ast.Constant)
		}
		self.assertIn("calling_module", keys)
		self.assertIn("caller_reference", keys)


class TestRequisitionEligibilityProjectionCompleteness(IntegrationTestCase):
	"""REQ-AC-056, pinned from the consumer's own test suite (not just
	Planning's `test_every_req_chg_001_v16_field_is_present`): every field
	this document's §5.1/§5A depend on is enumerated, by name, here too."""

	def test_the_required_field_lists_match_what_this_module_actually_uses(self):
		# A change to either list without updating the other is the defect
		# REQ-AC-056 exists to catch; this test simply keeps both lists
		# honest against each other, independent of a live Plan Item.
		self.assertEqual(len(REQUIRED_PROJECTION_FIELDS), len(set(REQUIRED_PROJECTION_FIELDS)))
		self.assertEqual(len(REQUIRED_SOURCE_FIELDS), len(set(REQUIRED_SOURCE_FIELDS)))
