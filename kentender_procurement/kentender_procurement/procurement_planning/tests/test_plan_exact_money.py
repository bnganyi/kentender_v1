# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-115 — Planning's affordability and method-limit decisions are exact
decimal sums with no epsilon (PLN §4.1: "never binary float"). The sums that
used to be 184132482.07000002 and 500000.00000000006 must meet their limits."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import budget_gateway, financial_basis, money, profiles, readiness

LINE_PARTS = ("44872648.85", "28586332.99", "80884095.33", "29789404.90")
LIMIT_PARTS = ("242653.82", "201170.23", "56175.95")


def _allocation(amount: str, line: str = "BL-1"):
	# a stored Currency comes back from the database as a float
	return SimpleNamespace(indicative_amount=float(amount), budget_line=line)


class TestExactPlanningSums(IntegrationTestCase):
	def test_the_naive_float_sums_really_are_noisy(self):
		for parts, exact in ((LINE_PARTS, 184132482.07), (LIMIT_PARTS, 500000.0)):
			total = 0.0
			for part in parts:
				total += float(part)  # the accumulation the services used
			self.assertNotEqual(total, exact)

	def test_line_totals_are_exact_decimals_that_meet_the_approved_amount(self):
		rows = [_allocation(p) for p in LINE_PARTS]
		with patch.object(readiness.frappe, "get_all", side_effect=[["ITEM-1"], rows]):
			totals = readiness.line_totals("VERSION-1")
		self.assertEqual(totals, {"BL-1": Decimal("184132482.07")})
		self.assertFalse(money.exceeds(totals["BL-1"], 184132482.07))

	def test_item_value_is_an_exact_decimal(self):
		with patch.object(readiness, "_allocations", return_value=[_allocation(p) for p in LIMIT_PARTS]):
			self.assertEqual(readiness.item_value("ITEM-1"), Decimal("500000.00"))

	def test_a_value_exactly_at_the_method_maximum_is_within_it(self):
		method = {
			"found": True,
			"conditions": [{"condition_id": "CAP", "kind": "Known fact", "mandatory": 1, "minimum_amount": 0, "maximum_amount": 500000.0}],
		}
		with patch.object(readiness, "_allocations", return_value=[_allocation(p) for p in LIMIT_PARTS]):
			value = readiness.item_value("ITEM-1")
		outcome = profiles.method_conditions(method, procurement_category="Goods", planned_value=value)
		self.assertTrue(outcome["admissible"])
		self.assertEqual(outcome["results"][0]["result"], "Met")

	def test_a_cent_over_the_method_maximum_is_still_refused(self):
		method = {"found": True, "conditions": [{"condition_id": "CAP", "kind": "Known fact", "mandatory": 1, "minimum_amount": 0, "maximum_amount": 500000.0}]}
		outcome = profiles.method_conditions(method, procurement_category="Goods", planned_value=Decimal("500000.01"))
		self.assertFalse(outcome["admissible"])

	def test_low_value_cumulative_cap_is_exact(self):
		reference = {"available": True, "threshold_matrix": [{"procurement_category": "Services", "procurement_method": "Low Value Procurement", "max_amount": 500000.0}]}
		items = [
			SimpleNamespace(name="I1", plan_item_id="PI-1", title="Cleaning", procurement_category="Services"),
			SimpleNamespace(name="I2", plan_item_id="PI-2", title="Cleaning", procurement_category="Services"),
			SimpleNamespace(name="I3", plan_item_id="PI-3", title="Cleaning", procurement_category="Services"),
		]
		amounts = dict(zip(("I1", "I2", "I3"), LIMIT_PARTS, strict=True))
		with (
			patch.object(readiness.frappe, "get_all", return_value=items),
			patch.object(readiness, "_allocations", side_effect=lambda name: [_allocation(amounts[name])]),
		):
			self.assertEqual(readiness.low_value_cumulative_breaches("VERSION-1", reference), [])

	def test_comparison_helpers_have_no_epsilon(self):
		self.assertTrue(money.exceeds("100.01", "100.00"))
		self.assertTrue(money.exceeds(100.0000000001, 100.0))
		self.assertFalse(money.exceeds(Decimal("100.00"), 100.0))
		self.assertTrue(money.same_amount(100.004, 100.0, precision=2))
		self.assertFalse(money.same_amount("100.01", "100.00"))


class TestCurrencyBasisIsNotDefaulted(IntegrationTestCase):
	"""AUD-XC-133 (Planning side) — the currency and precision come from the
	Budget's statement or context, never from a literal."""

	def test_a_decision_statement_supplies_currency_and_precision(self):
		self.assertEqual(financial_basis.currency_basis({"currency": "UGX", "currency_precision": 0}), ("UGX", 0))

	def test_a_display_statement_uses_the_precision_captured_with_the_version(self):
		basis = SimpleNamespace(precision=3)
		self.assertEqual(financial_basis.currency_basis({"currency": "KWD"}, basis), ("KWD", 3))

	def test_a_missing_currency_or_precision_blocks_instead_of_defaulting(self):
		for statement in ({}, {"currency": "KES"}, {"currency_precision": 2}, {"currency": "KES", "currency_precision": 9}):
			with self.subTest(statement=statement):
				with self.assertRaises(ProcurementPlanningError) as caught:
					financial_basis.currency_basis(statement)
				self.assertEqual(caught.exception.code, "PLN_MONEY_PRECISION_INVALID")

	def test_the_plan_currency_is_the_budgets_currency(self):
		with patch("kentender_budget.api.budget_api.resolve_budget_context", return_value={"budget": {"currency": "UGX"}}):
			self.assertEqual(budget_gateway.budget_currency("FY"), "UGX")

	def test_a_missing_budget_currency_blocks_instead_of_defaulting_to_kes(self):
		for context in ({}, {"budget": {"currency": ""}}, None):
			with self.subTest(context=context):
				with patch("kentender_budget.api.budget_api.resolve_budget_context", return_value=context):
					with self.assertRaises(ProcurementPlanningError) as caught:
						budget_gateway.budget_currency("FY")
				self.assertEqual(caught.exception.code, "PLN_REFERENCE_UNAVAILABLE")
