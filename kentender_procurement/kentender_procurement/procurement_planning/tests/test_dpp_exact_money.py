# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-03 / AUD-XC-117 (Planning half) — a Departmental Procurement Plan entry's
indicative amount and quantity are exact decimals (PLN §4.1: "never binary
float"). NaN, Infinity, excess decimals and an amount the column cannot hold are
refused with a typed error before any effect; an exact value is stored as it was
entered. Before the fix `flt()` let NaN and Infinity through the positivity test
and stored 1000000.005, which `sum_money` later rounded."""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import budget_gateway, dpp_lifecycle, needs_intake
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_dpp_lifecycle import PlanningCommandCase, key

# "9" * 30 is wider than the Decimal context: it must be the typed refusal, not a raw InvalidOperation
BAD_AMOUNTS = ("NaN", "Infinity", "-Infinity", "1000000.005", "-5", "1" + "0" * 18 + ".00", "12abc", "9" * 30)
BAD_QUANTITIES = ("NaN", "Infinity", "1.2345", "-1", "0", "1" + "0" * 12, "9" * 30)


class TestDirectRequirementIsExact(PlanningCommandCase):
	def refused(self, opened, code, **overrides):
		before = frappe.db.count("Departmental Plan Entry", {"dpp_version": opened["current_version"]})
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.add_direct(opened, **overrides)
		self.assertEqual(caught.exception.code, code)
		# nothing was written
		self.assertEqual(frappe.db.count("Departmental Plan Entry", {"dpp_version": opened["current_version"]}), before)

	def test_an_amount_that_is_not_exact_is_refused_before_any_effect(self):
		opened = self.open_alpha()
		for offered in BAD_AMOUNTS:
			with self.subTest(amount=offered):
				self.refused(opened, "PLN_MONEY_PRECISION_INVALID", indicative_amount=offered)

	def test_a_float_nan_or_infinity_from_in_process_code_is_refused_too(self):
		opened = self.open_alpha()
		for offered in (float("nan"), float("inf")):
			with self.subTest(amount=offered):
				self.refused(opened, "PLN_MONEY_PRECISION_INVALID", indicative_amount=offered)

	def test_a_blank_or_zero_amount_is_still_an_incomplete_entry(self):
		opened = self.open_alpha()
		for offered in (0, "0", "0.00"):
			with self.subTest(amount=offered):
				self.refused(opened, "PLN_ENTRY_INCOMPLETE", indicative_amount=offered)

	def test_a_quantity_that_is_not_exact_is_refused_before_any_effect(self):
		opened = self.open_alpha()
		with self.whole_number_unit(False):
			for offered in BAD_QUANTITIES:
				with self.subTest(quantity=offered):
					self.refused(opened, "PLN_ENTRY_INCOMPLETE", quantity=offered)

	def whole_number_unit(self, whole: bool):
		"""Make the fixture unit take (or not take) whole numbers only, for one call."""
		real = frappe.db.get_value
		return patch.object(
			dpp_lifecycle.frappe.db, "get_value",
			side_effect=lambda doctype, name=None, fieldname=None, *a, **k: (
				int(whole) if (doctype, fieldname) == ("UOM", "must_be_whole_number") else real(doctype, name, fieldname, *a, **k)
			),
		)

	def test_a_unit_that_takes_whole_numbers_refuses_a_fraction(self):
		opened = self.open_alpha()
		with self.whole_number_unit(True):
			self.refused(opened, "PLN_ENTRY_INCOMPLETE", quantity="1.5")

	def test_exact_values_are_stored_as_entered(self):
		opened = self.open_alpha()
		with self.whole_number_unit(False):
			added = self.add_direct(opened, indicative_amount="1000000.25", quantity="2.125")
		entry = frappe.get_doc("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added["entry_id"]})
		self.assertEqual(str(entry.indicative_amount), "1000000.25")
		self.assertEqual(float(entry.quantity), 2.125)

	def test_a_whole_quantity_is_stored_as_entered(self):
		opened = self.open_alpha()
		added = self.add_direct(opened, quantity="7")
		entry = frappe.get_doc("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added["entry_id"]})
		self.assertEqual(float(entry.quantity), 7.0)

	def test_the_amount_precision_is_the_budget_currencys_not_a_constant(self):
		opened = self.open_alpha()
		with patch.object(budget_gateway, "money_precision", return_value=0):
			self.refused(opened, "PLN_MONEY_PRECISION_INVALID", indicative_amount="1000000.25")
		with patch.object(budget_gateway, "money_precision", return_value=3):
			added = self.add_direct(opened, indicative_amount="1000000.125")
		entry = frappe.get_doc("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added["entry_id"]})
		self.assertEqual(float(entry.indicative_amount), 1000000.125)

	def test_an_edit_is_validated_the_same_way(self):
		opened = self.open_alpha()
		added = self.add_direct(opened)
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"], entry_id=added["entry_id"], values=fx.direct_values(indicative_amount="NaN"),
				expected_record_version=added["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_MONEY_PRECISION_INVALID")
		entry = frappe.get_doc("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added["entry_id"]})
		self.assertEqual(int(entry.indicative_amount), 1000000)


class TestNeedFundingIsExact(PlanningCommandCase):
	def need_entry(self):
		self._sources.stop()
		self._sources = patch.object(needs_intake, "current_accepted_sources", return_value=[fx.accepted_source()])
		self._sources.start()
		revision = patch.object(needs_intake, "current_accepted_revision_of", return_value=fx.NEED_V1)
		revision.start()
		self.addCleanup(revision.stop)
		opened = self.open_alpha()
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": fx.NEED}, "entry_id")
		return opened, entry_id

	def fund(self, opened, entry_id, amount):
		frappe.set_user(fx.AUTHOR)
		return dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=entry_id, budget_line=fx.BUDGET_LINE, indicative_amount=amount,
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)

	def test_an_amount_that_is_not_exact_is_refused_and_nothing_is_stored(self):
		opened, entry_id = self.need_entry()
		for offered in BAD_AMOUNTS + (float("nan"), float("inf")):
			with self.subTest(amount=offered):
				with self.assertRaises(ProcurementPlanningError) as caught:
					self.fund(opened, entry_id, offered)
				self.assertEqual(caught.exception.code, "PLN_MONEY_PRECISION_INVALID")
				entry = frappe.get_doc("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": entry_id})
				self.assertFalse(entry.budget_line)
				self.assertEqual(float(entry.indicative_amount or 0), 0)

	def test_an_exact_amount_is_stored_as_entered(self):
		opened, entry_id = self.need_entry()
		self.fund(opened, entry_id, "1234567.89")
		entry = frappe.get_doc("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": entry_id})
		self.assertEqual(str(entry.indicative_amount), "1234567.89")
