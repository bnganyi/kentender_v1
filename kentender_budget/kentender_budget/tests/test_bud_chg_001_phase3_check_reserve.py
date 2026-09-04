# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §8.2/§9.1 — check_funding/reserve_funding/convert_reservation
arithmetic and concurrency rules (§16.1 "Finance and arithmetic" rule group:
BUD-BR-009-016; BUD-AC-011-021).
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.services import budget_commitment_contracts as commitment_svc
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import (
	FUNDING_SOURCE,
	_BudgetLifecycleTestBase,
)


class _FinanceTestBase(_BudgetLifecycleTestBase):
	"""Adds a Finance Confirmation Officer (the real capability check_funding/
	reserve_funding require — distinct from Budget Officer/Approver) on top
	of the shared lifecycle scaffolding."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.finance_officer = cls._make_user("finance", ("Finance Confirmation Officer",))

	def _new_dhi_line(self, *, approved_amount=100_000_000) -> tuple[str, str]:
		"""One fresh Active baseline's DHI line — returns (budget, budget_line)."""
		budget, version = self._create_active_baseline(dhi_amount=approved_amount, hwd_amount=1)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line")
		return budget, line


class TestCheckFundingNonMutating(_FinanceTestBase):
	def test_check_funding_changes_no_state(self):
		"""BUD-AC-012 — check_funding returns exact current positions and
		changes no state."""
		_, line = self._new_dhi_line()
		self._as(self.finance_officer)
		before_count = frappe.db.count("Funding Reservation", {"budget_line": line})

		result = check_reserve.check_funding(
			plan_item="TEST-PPI-1",
			plan_version="TEST-PLN-1",
			finance_task="TEST-FNT-1",
			source_set_hash="TEST-HASH-1",
			allocations=[{"budget_line": line, "amount": 40_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-1"}],
			correlation_id=frappe.generate_hash(length=12),
		)
		self.assertTrue(result["all_sufficient"])
		self.assertEqual(result["allocations"][0]["available_before"], 100_000_000)
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), before_count)


class TestSingleSourceReservation(_FinanceTestBase):
	def test_single_source_confirmation_leaves_exact_position(self):
		"""BUD-AC-013 — single-source confirmation creates one full idempotent
		reservation and the exact 100m - 80m = 20m position."""
		_, line = self._new_dhi_line()
		self._as(self.finance_officer)
		token = check_reserve.check_funding(
			plan_item="TEST-PPI-2", plan_version="TEST-PLN-2", finance_task="TEST-FNT-2", source_set_hash="TEST-HASH-2",
			allocations=[{"budget_line": line, "amount": 80_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-2"}],
			correlation_id=frappe.generate_hash(length=12),
		)
		result = check_reserve.reserve_funding(
			token=token["token"], finance_task="TEST-FNT-2", source_set_hash="TEST-HASH-2", idempotency_key="TEST-IDEM-2"
		)
		self.assertTrue(result["ok"])
		self.assertFalse(result["reused"])
		self.assertEqual(len(result["reservations"]), 1)
		from kentender_budget.services.budget_contracts import get_budget_line_position

		pos = get_budget_line_position(line)["positions"]
		self.assertEqual(pos["approved"], 100_000_000)
		self.assertEqual(pos["reserved"], 80_000_000)
		self.assertEqual(pos["available"], 20_000_000)


class TestCombinedSourceAtomicity(_FinanceTestBase):
	def test_combined_source_confirmation_creates_both_reservations_atomically(self):
		"""BUD-AC-014 — combined-source confirmation creates all reservations
		atomically or none."""
		budget, version = self._create_active_baseline(dhi_amount=100_000_000, hwd_amount=60_000_000)
		dhi = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line")
		hwd = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "HWD test line"}, "budget_line")
		self._as(self.finance_officer)
		token = check_reserve.check_funding(
			plan_item="TEST-PPI-3", plan_version="TEST-PLN-3", finance_task="TEST-FNT-3", source_set_hash="TEST-HASH-3",
			allocations=[
				{"budget_line": dhi, "amount": 72_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-3A"},
				{"budget_line": hwd, "amount": 48_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-3B"},
			],
			correlation_id=frappe.generate_hash(length=12),
		)
		result = check_reserve.reserve_funding(
			token=token["token"], finance_task="TEST-FNT-3", source_set_hash="TEST-HASH-3", idempotency_key="TEST-IDEM-3"
		)
		self.assertTrue(result["ok"])
		self.assertEqual(len(result["reservations"]), 2)
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": ["in", [dhi, hwd]], "status": "Active"}), 2)


class TestShortfallRejection(_FinanceTestBase):
	def test_shortfall_creates_no_reservation(self):
		"""BUD-AC-015 — a shortfall returns the exact failing allocation and
		creates no partial reservation."""
		_, line = self._new_dhi_line(approved_amount=100_000_000)
		self._as(self.finance_officer)
		# Pre-reserve 30m, leaving 70m available.
		token1 = check_reserve.check_funding(
			plan_item="TEST-PPI-4", plan_version="TEST-PLN-4", finance_task="TEST-FNT-4A", source_set_hash="TEST-HASH-4A",
			allocations=[{"budget_line": line, "amount": 30_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-4A"}],
			correlation_id=frappe.generate_hash(length=12),
		)
		check_reserve.reserve_funding(token=token1["token"], finance_task="TEST-FNT-4A", source_set_hash="TEST-HASH-4A", idempotency_key="TEST-IDEM-4A")

		# Now request 80m against only 70m available — 10m short.
		token2 = check_reserve.check_funding(
			plan_item="TEST-PPI-4", plan_version="TEST-PLN-4", finance_task="TEST-FNT-4B", source_set_hash="TEST-HASH-4B",
			allocations=[{"budget_line": line, "amount": 80_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-4B"}],
			correlation_id=frappe.generate_hash(length=12),
		)
		self.assertFalse(token2["all_sufficient"])
		self.assertEqual(token2["allocations"][0]["shortfall"], 10_000_000)

		before = frappe.db.count("Funding Reservation", {"budget_line": line})
		with self.assertRaises(frappe.ValidationError):
			check_reserve.reserve_funding(token=token2["token"], finance_task="TEST-FNT-4B", source_set_hash="TEST-HASH-4B", idempotency_key="TEST-IDEM-4B")
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), before)


class TestDuplicateCorrelationIdempotency(_FinanceTestBase):
	def test_duplicate_correlation_returns_original_reservation(self):
		"""BUD-AC-016 — concurrent confirmation commands cannot oversubscribe
		a line; a duplicate correlation returns the original effective result."""
		_, line = self._new_dhi_line()
		self._as(self.finance_officer)
		correlation_id = frappe.generate_hash(length=12)
		token = check_reserve.check_funding(
			plan_item="TEST-PPI-5", plan_version="TEST-PLN-5", finance_task="TEST-FNT-5", source_set_hash="TEST-HASH-5",
			allocations=[{"budget_line": line, "amount": 50_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-5"}],
			correlation_id=correlation_id,
		)
		first = check_reserve.reserve_funding(token=token["token"], finance_task="TEST-FNT-5", source_set_hash="TEST-HASH-5", idempotency_key=correlation_id)
		second = check_reserve.reserve_funding(token=token["token"], finance_task="TEST-FNT-5", source_set_hash="TEST-HASH-5", idempotency_key=correlation_id)
		self.assertFalse(first["reused"])
		self.assertTrue(second["reused"])
		self.assertEqual(first["reservations"][0]["reservation_id"], second["reservations"][0]["reservation_id"])
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), 1)

	def test_same_plan_source_allocation_different_correlation_conflicts(self):
		"""§13 BUDGET_RESERVATION_CONFLICT — not a raw DB constraint error."""
		_, line = self._new_dhi_line()
		self._as(self.finance_officer)
		token1 = check_reserve.check_funding(
			plan_item="TEST-PPI-6", plan_version="TEST-PLN-6", finance_task="TEST-FNT-6A", source_set_hash="TEST-HASH-6A",
			allocations=[{"budget_line": line, "amount": 10_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-SHARED-6"}],
			correlation_id=frappe.generate_hash(length=12),
		)
		check_reserve.reserve_funding(token=token1["token"], finance_task="TEST-FNT-6A", source_set_hash="TEST-HASH-6A", idempotency_key="TEST-IDEM-6A")

		token2 = check_reserve.check_funding(
			plan_item="TEST-PPI-6", plan_version="TEST-PLN-6", finance_task="TEST-FNT-6B", source_set_hash="TEST-HASH-6B",
			allocations=[{"budget_line": line, "amount": 10_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-SHARED-6"}],
			correlation_id=frappe.generate_hash(length=12),
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			check_reserve.reserve_funding(token=token2["token"], finance_task="TEST-FNT-6B", source_set_hash="TEST-HASH-6B", idempotency_key="TEST-IDEM-6B")
		self.assertIn("different effective reservation", str(ctx.exception))


class TestPartialConversion(_FinanceTestBase):
	def test_partial_conversion_leaves_exact_position(self):
		"""BUD-AC-019 — partial conversion of an 80m reservation to a 60m
		commitment leaves 20m reserved, 60m committed and 20m available on
		the 100m line."""
		_, line = self._new_dhi_line()
		self._as(self.finance_officer)
		token = check_reserve.check_funding(
			plan_item="TEST-PPI-7", plan_version="TEST-PLN-7", finance_task="TEST-FNT-7", source_set_hash="TEST-HASH-7",
			allocations=[{"budget_line": line, "amount": 80_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-7"}],
			correlation_id=frappe.generate_hash(length=12),
		)
		reserve_result = check_reserve.reserve_funding(token=token["token"], finance_task="TEST-FNT-7", source_set_hash="TEST-HASH-7", idempotency_key="TEST-IDEM-7")
		reservation_id = reserve_result["reservations"][0]["reservation_id"]

		commitment_svc.convert_reservation(reservation=reservation_id, contract="TEST-CTR-7", amount=60_000_000, idempotency_key="TEST-CONV-7")

		from kentender_budget.services.budget_contracts import get_budget_line_position

		pos = get_budget_line_position(line)["positions"]
		self.assertEqual(pos["reserved"], 20_000_000)
		self.assertEqual(pos["committed"], 60_000_000)
		self.assertEqual(pos["available"], 20_000_000)


class TestClosedBudgetRejectsNewReservations(_FinanceTestBase):
	def test_check_funding_on_closed_line_raises_budget_closed(self):
		"""BUD-BR-023 — a Closed Budget admits no new reservations, with the
		specific BUDGET_CLOSED code (not a generic not-eligible error)."""
		budget, version = self._create_active_baseline(dhi_amount=10_000_000, hwd_amount=1)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line")

		frappe.set_user("Administrator")
		fiscal_year = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		frappe.db.set_value("Fiscal Year", fiscal_year, "year_end_date", "2000-01-01", update_modified=False)
		frappe.db.set_value(
			"Procurement Budget Version",
			version,
			{"status": "Closed", "closed_by": "Administrator", "closed_at": frappe.utils.now_datetime()},
			update_modified=False,
		)

		self._as(self.finance_officer)
		with self.assertRaises(frappe.ValidationError) as ctx:
			check_reserve.check_funding(
				plan_item="TEST-PPI-8", plan_version="TEST-PLN-8", finance_task="TEST-FNT-8", source_set_hash="TEST-HASH-8",
				allocations=[{"budget_line": line, "amount": 1_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-8"}],
				correlation_id=frappe.generate_hash(length=12),
			)
		self.assertIn("Closed", str(ctx.exception))
