# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §5.14 — exact Money and whole-number Each, pure
(REQ19-AC-071, REQ-SC-PRECISION)."""

from __future__ import annotations

import unittest
from decimal import Decimal

from kentender_procurement.procurement_requisitions.services import precision
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError


class TestMoney(unittest.TestCase):
	def test_exact_strings_ints_and_decimals_round_trip(self):
		self.assertEqual(precision.money_text(precision.parse_money("20000000.00")), "20000000.00")
		self.assertEqual(precision.money_text(precision.parse_money(5)), "5.00")
		self.assertEqual(precision.money_text(precision.parse_money(Decimal("0.10"))), "0.10")
		self.assertEqual(precision.money_text(precision.parse_money("123456789012345678.99")), "123456789012345678.99")

	def test_refused_without_rounding(self):
		for bad in (20000000.0, "1.005", "1e6", "NaN", "Infinity", "-1.00", "0", "", None, True, "1234567890123456789.00", "1,000.00"):
			with self.subTest(bad=bad):
				with self.assertRaises(ProcurementRequisitionsError) as caught:
					precision.parse_money(bad, field="Requested value")
				self.assertEqual(caught.exception.code, "REQ_MONEY_PRECISION_INVALID")

	def test_zero_only_where_allowed(self):
		self.assertEqual(precision.parse_money("0.00", allow_zero=True), Decimal("0.00"))

	def test_display(self):
		self.assertEqual(precision.display_money("50000000"), "KES 50,000,000.00")


class TestQuantity(unittest.TestCase):
	def test_whole_numbers_only(self):
		self.assertEqual(precision.quantity_text(precision.parse_quantity("250")), "250")
		self.assertEqual(precision.quantity_text(precision.parse_quantity(100)), "100")
		for bad in ("1.5", 1.0, "0", "-3", "abc", None, "1e3"):
			with self.subTest(bad=bad):
				with self.assertRaises(ProcurementRequisitionsError) as caught:
					precision.parse_quantity(bad)
				self.assertEqual(caught.exception.code, "REQ_QUANTITY_PRECISION_INVALID")

	def test_planning_quantity_accepts_an_integral_decimal_string_only(self):
		self.assertEqual(precision.planning_quantity("250"), Decimal(250))
		self.assertEqual(precision.planning_quantity("100.000"), Decimal(100))
		with self.assertRaises(ProcurementRequisitionsError):
			precision.planning_quantity("0.5")

	def test_display(self):
		self.assertEqual(precision.display_quantity("250"), "250 Each")
