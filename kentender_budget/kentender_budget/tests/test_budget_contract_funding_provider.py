# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.14 (tracker CM8-507): Budget answers the contract funding seam.

Contract Management's operation identity is the idempotency anchor: converting twice converts once, `lookup` reads what an identity already did, an allocation that does not add up converts nothing,
and a Budget refusal is a definitive refusal that leaves no partial conversion behind."""

from __future__ import annotations

import frappe

from kentender_budget.services import contract_funding_provider as owner
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase
from kentender_core.services import contract_funding_contract as seam


class TestContractFundingProvider(_PrincipalBase):
	def setUp(self):
		super().setUp()
		frappe.flags.kt_contract_funding_providers = [owner.Provider()]
		self.addCleanup(lambda: setattr(frappe.flags, "kt_contract_funding_providers", None))
		self.identity = f"{self.contract}|agreement 1|1|Funding conversion|effective"

	def _reservation(self, amount=10_000_000):
		budget, line = self._new_dhi_line()
		reservation = self._reserve(line, amount)
		self._as("Administrator")
		return reservation

	def test_it_converts_each_allocation_once_and_a_retry_returns_the_same_commitment(self):
		reservation = self._reservation()
		first = seam.convert(self.identity, contract=self.contract, allocations=[{"reservation": reservation, "amount": 1_000_000}], amount=1_000_000)
		again = seam.convert(self.identity, contract=self.contract, allocations=[{"reservation": reservation, "amount": 1_000_000}], amount=1_000_000)
		self.assertEqual((first, again), (again, first))
		self.assertEqual(frappe.db.count("Procurement Commitment", {"contract": self.contract}), 1)
		self.assertEqual(frappe.db.get_value("Procurement Commitment", {"contract": self.contract}, "current_amount"), 1_000_000)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 9_000_000)

	def test_lookup_reads_what_an_identity_already_did_and_nothing_else(self):
		reservation = self._reservation()
		self.assertIsNone(seam.lookup(self.identity))
		done = seam.convert(self.identity, contract=self.contract, allocations=[{"reservation": reservation, "amount": 400_000}], amount=400_000)
		self.assertEqual(seam.lookup(self.identity), done)
		self.assertIsNone(seam.lookup(self.identity + "-other"))

	def test_allocations_that_do_not_add_up_convert_nothing(self):
		reservation = self._reservation()
		for allocations, amount in (([], 1000), ([{"reservation": reservation, "amount": 900}], 1000), ([{"reservation": "", "amount": 1000}], 1000), ([{"reservation": reservation, "amount": 0}], 0)):
			with self.assertRaises(seam.Refused):
				seam.convert(self.identity, contract=self.contract, allocations=allocations, amount=amount)
		self.assertEqual(frappe.db.count("Procurement Commitment", {"contract": self.contract}), 0)

	def test_a_budget_refusal_is_definitive_and_leaves_no_partial_conversion(self):
		small, big = self._reservation(500_000), self._reservation(10_000_000)
		frappe.db.savepoint("before_conversion")  # what Contract Management's operation does on a refusal: the whole attempt is undone
		with self.assertRaises(seam.Refused) as caught:
			seam.convert(self.identity, contract=self.contract, allocations=[{"reservation": big, "amount": 600_000}, {"reservation": small, "amount": 600_000}], amount=1_200_000)
		self.assertIn("exceeds the remaining reservation", str(caught.exception))
		frappe.db.rollback(save_point="before_conversion")
		self.assertEqual(frappe.db.count("Procurement Commitment", {"contract": self.contract}), 0, "the first allocation did not stay converted")

	def test_a_shared_award_converts_each_reservation_it_draws_on(self):
		first, second = self._reservation(), self._reservation()
		done = seam.convert(self.identity, contract=self.contract, allocations=[{"reservation": first, "amount": 700_000}, {"reservation": second, "amount": 300_000}], amount=1_000_000)
		self.assertEqual(done["amount"], 1_000_000)
		self.assertEqual(len(done["reference"].split(", ")), 2)
		self.assertEqual(sorted(frappe.get_all("Procurement Commitment", filters={"contract": self.contract}, pluck="current_amount")), [300_000, 700_000])
