# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The seam that tells Budget which reservations a contract may draw on (BUD-CHG-001 v1.14 proposal): the first owner that knows the contract answers, and with no owner that knows it the answer is None,
never yes. Budget refuses on None, so the seam itself must never turn silence into permission."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import contract_reservation_authority as seam


class Owner:
	def __init__(self, answer):
		self.answer, self.calls = answer, []

	def authorises(self, *, contract, reservation):
		self.calls.append((contract, reservation))
		return self.answer


class TestContractReservationAuthority(IntegrationTestCase):
	def test_with_no_owner_the_answer_is_none_never_yes(self):
		with seam.installed():
			self.assertIsNone(seam.authorises("C-1", "R-1"))

	def test_an_owner_that_does_not_know_the_contract_leaves_the_answer_to_the_next(self):
		silent, knows = Owner(None), Owner(True)
		with seam.installed(silent, knows):
			self.assertIs(seam.authorises("C-1", "R-1"), True)
		self.assertEqual(silent.calls, [("C-1", "R-1")])
		self.assertEqual(knows.calls, [("C-1", "R-1")])

	def test_the_first_answer_that_is_not_none_wins_even_when_it_is_no(self):
		refuses, later = Owner(False), Owner(True)
		with seam.installed(refuses, later):
			self.assertIs(seam.authorises("C-1", "R-1"), False)
		self.assertEqual(later.calls, [], "a no is not overruled by a later owner")

	def test_a_fixed_answer_names_exactly_the_reservations_given(self):
		fixed = seam.Static({"C-1": ["R-1", "R-2"]})
		self.assertIs(fixed.authorises(contract="C-1", reservation="R-2"), True)
		self.assertIs(fixed.authorises(contract="C-1", reservation="R-3"), False)
		self.assertIsNone(fixed.authorises(contract="C-2", reservation="R-1"))

	def test_installing_an_answer_puts_the_previous_one_back(self):
		before = frappe.flags.get(seam.FLAG)
		with seam.installed(Owner(True)):
			self.assertIsNotNone(frappe.flags.get(seam.FLAG))
		self.assertEqual(frappe.flags.get(seam.FLAG), before)

	def test_names_is_asked_of_an_owner_that_offers_it_and_falls_back_to_authorises_for_one_that_does_not(self):
		"""A request that draws nothing (the owner's decision of 16 October 2026, revalidation) asks whether the award names a reservation, before its agreement is effective."""

		class Names(Owner):
			def names(self, *, contract, reservation):
				return True

		plain = Owner(False)
		with seam.installed(plain):
			self.assertIs(seam.names("C-1", "R-1"), False, "an owner with no `names` answers by `authorises`")
		with seam.installed(Owner(False)), seam.installed(Names(False)):
			self.assertIs(seam.names("C-1", "R-1"), True)
			self.assertIs(seam.authorises("C-1", "R-1"), False, "naming it draws on nothing")
		with seam.installed():
			self.assertIsNone(seam.names("C-1", "R-1"), "no owner is never a yes")
