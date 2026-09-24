# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.10 §8.3 / REQ-CHG-001 v1.11 §9.1A — the complete-array
funding check and reservation a Requisition authorisation makes.

- rows that share one Budget Line are totalled before availability is tested
  (BUD-SC-REQ-SAME-LINE: 20m + 30m against 40m is a 10m shortfall);
- one reservation per REQ drawdown line, even on a shared line;
- exact Money in and out, no float input, no rounding;
- same key + same payload replays, same key + changed payload is refused,
  a new key cannot duplicate an already reserved drawdown line;
- the owner call never commits — it runs inside the caller's transaction.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import (
	FUNDING_SOURCE,
	_FinanceTestBase,
)


class _ArrayTestBase(_FinanceTestBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.hopf_officer = cls._make_user("hopfarray", ("Head of Procurement Function",))

	def _rows(self, line, *pairs):
		return [
			{
				"budget_line": line,
				"amount": amount,
				"funding_source": FUNDING_SOURCE,
				"plan_source_allocation": f"TEST-PSA-{drawdown}",
				"drawdown_line_id": drawdown,
				"source_organisation_unit": f"TEST-OU-{drawdown}",
			}
			for drawdown, amount in pairs
		]

	def _check(self, allocations, *, correlation=None, caller_reference="REQ-ARRAY"):
		self._as(self.hopf_officer)
		return check_reserve.check_funding(
			plan_item="TEST-PPI-ARRAY",
			plan_version="TEST-PLN-ARRAY",
			source_set_hash="TEST-HASH-ARRAY",
			allocations=allocations,
			correlation_id=correlation or frappe.generate_hash(length=12),
			calling_module="Procurement Requisitions",
			caller_reference=caller_reference,
		)

	def _reserve(self, token, key):
		return check_reserve.reserve_funding(token=token["token"], source_set_hash="TEST-HASH-ARRAY", idempotency_key=key)

	@staticmethod
	def _title(ctx) -> str:
		"""Budget's closed error code travels as the message title (the
		convention Planning's `budget_gateway` reads)."""
		titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
		return titles[-1] if titles else ""


class TestSharedLineAggregation(_ArrayTestBase):
	def test_two_rows_on_one_line_are_totalled_before_availability(self):
		_, line = self._new_dhi_line(approved_amount=40_000_000)
		d1, d2 = frappe.generate_hash(length=10), frappe.generate_hash(length=10)
		checked = self._check(self._rows(line, (d1, "20000000.00"), (d2, "30000000.00")))

		self.assertFalse(checked["all_sufficient"])
		self.assertEqual(len(checked["lines"]), 1)
		self.assertEqual(checked["lines"][0]["required_amount"], "50000000.00")
		self.assertEqual(checked["lines"][0]["available_before"], "40000000.00")
		self.assertEqual(checked["lines"][0]["shortfall"], "10000000.00")
		# each row reports the line it shares, never an independent pass
		self.assertEqual([r["sufficient"] for r in checked["allocations"]], [False, False])

		with self.assertRaises(frappe.ValidationError) as ctx:
			self._reserve(checked, frappe.generate_hash(length=12))
		self.assertEqual(self._title(ctx), "BUDGET_INSUFFICIENT_FUNDS")
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), 0)

	def test_one_reservation_per_drawdown_line_on_a_shared_line(self):
		_, line = self._new_dhi_line(approved_amount=60_000_000)
		d1, d2 = frappe.generate_hash(length=10), frappe.generate_hash(length=10)
		checked = self._check(self._rows(line, (d1, "20000000.00"), (d2, "30000000.00")))
		self.assertTrue(checked["all_sufficient"])
		self.assertEqual(checked["lines"][0]["available_after"], "10000000.00")

		result = self._reserve(checked, frappe.generate_hash(length=12))
		mapping = {r["drawdown_line_id"]: r for r in result["reservations"]}
		self.assertEqual(set(mapping), {d1, d2})
		self.assertEqual(mapping[d1]["original_amount"], "20000000.00")
		self.assertEqual(mapping[d2]["original_amount"], "30000000.00")
		self.assertNotEqual(mapping[d1]["reservation_id"], mapping[d2]["reservation_id"])


class TestExactMoneyBoundary(_ArrayTestBase):
	def _assert_rejected(self, amount):
		_, line = self._new_dhi_line()
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._check(self._rows(line, (frappe.generate_hash(length=10), amount)))
		self.assertEqual(self._title(ctx), "BUDGET_MONEY_PRECISION_INVALID", f"{amount!r} was accepted")

	def test_a_float_amount_is_refused(self):
		self._assert_rejected(20000000.0)

	def test_excess_scale_is_refused_not_rounded(self):
		self._assert_rejected("1.005")

	def test_exponent_notation_is_refused(self):
		self._assert_rejected("1e6")

	def test_more_than_eighteen_integral_digits_is_refused(self):
		self._assert_rejected("1234567890123456789.00")

	def test_integer_and_decimal_string_are_accepted_exactly(self):
		_, line = self._new_dhi_line()
		checked = self._check(self._rows(line, (frappe.generate_hash(length=10), 5), (frappe.generate_hash(length=10), "0.10")))
		self.assertEqual(checked["lines"][0]["required_amount"], "5.10")


class TestArrayIdempotency(_ArrayTestBase):
	def test_same_key_same_payload_replays_the_original_mapping(self):
		_, line = self._new_dhi_line()
		d1 = frappe.generate_hash(length=10)
		key = frappe.generate_hash(length=12)
		first = self._reserve(self._check(self._rows(line, (d1, "1000.00"))), key)
		again = self._reserve(self._check(self._rows(line, (d1, "1000.00"))), key)
		self.assertTrue(again["reused"])
		self.assertEqual(again["reservations"][0]["reservation_id"], first["reservations"][0]["reservation_id"])

	def test_same_key_changed_payload_is_refused(self):
		_, line = self._new_dhi_line()
		d1 = frappe.generate_hash(length=10)
		key = frappe.generate_hash(length=12)
		self._reserve(self._check(self._rows(line, (d1, "1000.00"))), key)
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._reserve(self._check(self._rows(line, (d1, "2000.00"))), key)
		self.assertEqual(self._title(ctx), "BUDGET_IDEMPOTENCY_CONFLICT")

	def test_a_new_key_cannot_duplicate_a_reserved_drawdown_line(self):
		_, line = self._new_dhi_line()
		d1 = frappe.generate_hash(length=10)
		self._reserve(self._check(self._rows(line, (d1, "1000.00"))), frappe.generate_hash(length=12))
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._reserve(self._check(self._rows(line, (d1, "1000.00"))), frappe.generate_hash(length=12))
		self.assertEqual(self._title(ctx), "BUDGET_RESERVATION_CONFLICT")


class TestRunsInsideTheCallerTransaction(_ArrayTestBase):
	def test_check_and_reserve_never_commit(self):
		_, line = self._new_dhi_line()
		with patch.object(frappe.db, "commit", side_effect=AssertionError("owner call committed")):
			checked = self._check(self._rows(line, (frappe.generate_hash(length=10), "1000.00")))
			result = self._reserve(checked, frappe.generate_hash(length=12))
		self.assertTrue(result["ok"])
