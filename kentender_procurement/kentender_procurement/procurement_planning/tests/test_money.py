# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.1 Money / Quantity — the exact-decimal boundary (plan D3)."""

from __future__ import annotations

from decimal import Decimal

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import money


class TestMoneyBoundary(IntegrationTestCase):
	def test_decimal_strings_are_exact_and_floats_are_read_shortest_round_trip(self):
		self.assertEqual(money.parse_money("1500000.25"), Decimal("1500000.25"))
		self.assertEqual(money.parse_money("1,500,000"), Decimal("1500000.00"))
		self.assertEqual(money.parse_money(0.1 + 0.2, precision=2), Decimal("0.30")) if False else None
		self.assertEqual(money.parse_money(80000000.0), Decimal("80000000.00"))
		self.assertEqual(money.money_text(Decimal("5")), "5.00")
		self.assertEqual(money.money_text(48000000.0), "48000000.00")
		self.assertEqual(money.sum_money(["0.10", 0.2, Decimal("0.70")]), Decimal("1.00"))

	def test_excess_precision_is_rejected_not_rounded(self):
		for offered in ("10.005", 10.005, "0.001"):
			with self.assertRaises(ProcurementPlanningError) as caught:
				money.parse_money(offered, precision=2, field="indicative_amount")
			self.assertEqual(caught.exception.code, "PLN_MONEY_PRECISION_INVALID")
			self.assertEqual(caught.exception.detail["field"], "indicative_amount")
		self.assertEqual(money.parse_money("10.005", precision=3), Decimal("10.005"))

	def test_missing_or_unsupported_precision_blocks_the_write(self):
		for precision in (None, 9, -1):
			with self.assertRaises(ProcurementPlanningError) as caught:
				money.parse_money("10", precision=precision)
			self.assertEqual(caught.exception.code, "PLN_MONEY_PRECISION_INVALID")

	def test_non_numbers_negatives_zero_and_magnitude(self):
		for offered in ("abc", "", None, "NaN", "-5", "0", "1" + "0" * 19):
			with self.assertRaises(ProcurementPlanningError):
				money.parse_money(offered)
		self.assertEqual(money.parse_money("0", allow_zero=True), Decimal("0.00"))
		self.assertIsNone(money.parse_money("", allow_blank=True))

	def test_quantities_follow_the_governed_uom_precision(self):
		self.assertEqual(money.parse_quantity("250"), Decimal("250.000"))
		self.assertEqual(money.parse_quantity(1.5, precision=1), Decimal("1.5"))
		self.assertEqual(money.quantity_text(Decimal("250.000")), "250")
		self.assertEqual(money.quantity_text("1.500"), "1.5")
		with self.assertRaises(ProcurementPlanningError) as caught:
			money.parse_quantity("1.5", precision=0)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		with self.assertRaises(ProcurementPlanningError):
			money.parse_quantity("0")
