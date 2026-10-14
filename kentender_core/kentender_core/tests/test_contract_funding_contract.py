# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The funding seam (CM-CHG-001 v0.8 plan D5, D7): the owner is asked through a published interface, is idempotent on the operation identity, and with no owner the caller is told so."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import contract_funding_contract as seam


class Owner:
	def __init__(self, refuse=False):
		self.held, self.refuse, self.calls = {}, refuse, 0

	def lookup(self, *, identity):
		return self.held.get(identity)

	def convert(self, *, identity, contract, allocations, amount):
		self.calls += 1
		if self.refuse:
			raise seam.Refused("The reservation was released.")
		return self.held.setdefault(identity, {"reference": f"COM-{len(self.held) + 1}", "amount": amount})


class TestContractFundingSeam(IntegrationTestCase):
	def use(self, *owners):
		frappe.flags.kt_contract_funding_providers = list(owners)
		self.addCleanup(lambda: setattr(frappe.flags, "kt_contract_funding_providers", None))

	def test_a_provider_must_offer_both_functions(self):
		self.assertEqual(seam.missing_functions(Owner()), [])
		self.assertEqual(seam.missing_functions(object()), ["lookup", "convert"])

	def test_conversion_is_idempotent_on_the_operation_identity(self):
		owner = Owner()
		self.use(owner)
		first = seam.convert("CM|agreement 1|1|Funding conversion|k", contract="CM-1", allocations=[{"amount": 5}], amount=5)
		again = seam.convert("CM|agreement 1|1|Funding conversion|k", contract="CM-1", allocations=[{"amount": 5}], amount=5)
		self.assertEqual(first, again)
		self.assertEqual(seam.lookup("CM|agreement 1|1|Funding conversion|k"), first)
		self.assertIsNone(seam.lookup("CM|other"))

	def test_a_refusal_is_the_owners_and_with_no_owner_the_caller_is_told_so(self):
		self.use(Owner(refuse=True))
		with self.assertRaises(seam.Refused):
			seam.convert("x", contract="CM-1", allocations=[], amount=1)
		self.use()
		with self.assertRaises(seam.Unavailable):
			seam.convert("x", contract="CM-1", allocations=[], amount=1)
		self.assertIsNone(seam.lookup("x"))
