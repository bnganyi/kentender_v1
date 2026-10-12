# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 D1 / AUD-XC-012 — Procurement Requisitions as the only
check_funding/reserve_funding caller (the Requisitions service principal, not
a session role), calling_module/caller_reference recorded from the principal,
and the relaxed per-allocation
uniqueness (reserve after release; two independent callers on one allocation;
same-caller double-authorise still refused).
"""

from __future__ import annotations

import frappe
from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.services import budget_commitment_contracts as commitment_svc
from kentender_budget.services.budget_service_principal import PRINCIPAL_REQUISITIONS, service_caller
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import (
	FUNDING_SOURCE,
	_FinanceTestBase,
	owner_ou,
)
from kentender_core.services.command_write_guard import fixture_insert


def _req(reference: str):
	return service_caller(PRINCIPAL_REQUISITIONS, reference=reference)


class _RequisitionCallerTestBase(_FinanceTestBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.hopf_officer = cls._make_user("hopf", ("Head of Procurement Function",))
		cls.budget_officer_only = cls._make_user("budgetofficeronly", ("Budget Officer",))


class TestCheckReserveCallerGate(_RequisitionCallerTestBase):
	def test_the_requisitions_principal_may_check_and_reserve(self):
		_, line = self._new_dhi_line()
		self._as(self.hopf_officer)
		token = check_reserve.check_funding(
			plan_item="TEST-PPI-REQ-1",
			plan_version="TEST-PLN-REQ-1",
			source_set_hash="TEST-HASH-REQ-1",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": 10_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-REQ-1"}],
			correlation_id=frappe.generate_hash(length=12),
			caller=_req("REQ-TEST-1"),
		)
		self.assertTrue(token["all_sufficient"])
		result = check_reserve.reserve_funding(
			token=token["token"], source_set_hash="TEST-HASH-REQ-1", idempotency_key="TEST-IDEM-REQ-1", caller=_req("REQ-TEST-1")
		)
		self.assertTrue(result["ok"])
		self.assertFalse(result["reused"])
		row = result["reservations"][0]
		self.assertEqual(row["calling_module"], "Procurement Requisitions")
		self.assertEqual(row["caller_reference"], "REQ-TEST-1")

	def test_finance_confirmation_officer_session_is_refused(self):
		"""AUD-XC-012 — a session role is not a Budget caller; a Finance
		Confirmation Officer cannot place a hold, with or without declaring a
		caller."""
		_, line = self._new_dhi_line()
		self._as(self.finance_officer)
		with self.assertRaises(frappe.PermissionError):
			check_reserve.check_funding(
				plan_item="TEST-PPI-REQ-2", plan_version="TEST-PLN-REQ-2", source_set_hash="TEST-HASH-REQ-2",
				allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": 10_000_000, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-REQ-2"}],
				correlation_id=frappe.generate_hash(length=12), finance_task="TEST-FNT-REQ-2",
			)
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), 0)

	def test_a_session_without_the_principal_is_refused_whatever_its_role(self):
		_, line = self._new_dhi_line()
		self._as(self.budget_officer_only)
		with self.assertRaises(frappe.PermissionError):
			check_reserve.check_funding(
				plan_item="TEST-PPI-REQ-3", plan_version="TEST-PLN-REQ-3", source_set_hash="TEST-HASH-REQ-3",
				allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": 1, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-REQ-3"}],
				correlation_id=frappe.generate_hash(length=12),
			)

	def test_a_check_with_no_finance_task_must_reserve_with_none_too(self):
		_, line = self._new_dhi_line()
		self._as(self.hopf_officer)
		token = check_reserve.check_funding(
			plan_item="TEST-PPI-REQ-4", plan_version="TEST-PLN-REQ-4", source_set_hash="TEST-HASH-REQ-4",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": 1, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "TEST-PSA-REQ-4"}],
			correlation_id=frappe.generate_hash(length=12), caller=_req("REQ-TEST-4"),
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			check_reserve.reserve_funding(
				token=token["token"], source_set_hash="TEST-HASH-REQ-4", idempotency_key="TEST-IDEM-REQ-4", finance_task="UNEXPECTED", caller=_req("REQ-TEST-4")
			)
		self.assertIn("expired or no longer matches", str(ctx.exception))


class TestReservationUniquenessRelaxed(_RequisitionCallerTestBase):
	def _reserve(self, *, line, amount, allocation, correlation, caller_reference):
		self._as(self.hopf_officer)
		token = check_reserve.check_funding(
			plan_item="TEST-PPI-REQ-U", plan_version="TEST-PLN-REQ-U", source_set_hash=f"HASH-{correlation}",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": amount, "funding_source": FUNDING_SOURCE, "plan_source_allocation": allocation}],
			correlation_id=correlation, caller=_req(caller_reference),
		)
		return check_reserve.reserve_funding(
			token=token["token"], source_set_hash=f"HASH-{correlation}", idempotency_key=correlation, caller=_req(caller_reference)
		)

	def test_reserve_after_release_on_the_same_allocation_succeeds(self):
		_, line = self._new_dhi_line()
		allocation = "TEST-PSA-REL-1"
		first = self._reserve(line=line, amount=5_000_000, allocation=allocation, correlation=frappe.generate_hash(12), caller_reference="REQ-REL-1")
		reservation_id = first["reservations"][0]["reservation_id"]
		self._as(self.hopf_officer)
		commitment_svc.release_reservation(
			reservation=reservation_id, amount=None, downstream_event_id="TEST-EVT-REL-1",
			downstream_event_type="TestRevocation", idempotency_key="TEST-REL-IDEM-1", caller=_req("REQ-REL-1"),
		)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation_id, "status"), "Released")
		second = self._reserve(line=line, amount=5_000_000, allocation=allocation, correlation=frappe.generate_hash(12), caller_reference="REQ-REL-2")
		self.assertTrue(second["ok"])
		self.assertNotEqual(second["reservations"][0]["reservation_id"], reservation_id)

	def test_two_different_callers_may_each_reserve_the_same_allocation(self):
		_, line = self._new_dhi_line()
		allocation = "TEST-PSA-TWO-1"
		first = self._reserve(line=line, amount=5_000_000, allocation=allocation, correlation=frappe.generate_hash(12), caller_reference="REQ-TWO-A")
		second = self._reserve(line=line, amount=5_000_000, allocation=allocation, correlation=frappe.generate_hash(12), caller_reference="REQ-TWO-B")
		self.assertTrue(first["ok"])
		self.assertTrue(second["ok"])
		self.assertNotEqual(first["reservations"][0]["reservation_id"], second["reservations"][0]["reservation_id"])

	def test_same_caller_reference_double_authorise_is_still_refused(self):
		_, line = self._new_dhi_line()
		allocation = "TEST-PSA-DUP-1"
		self._reserve(line=line, amount=5_000_000, allocation=allocation, correlation=frappe.generate_hash(12), caller_reference="REQ-DUP-1")
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._reserve(line=line, amount=5_000_000, allocation=allocation, correlation=frappe.generate_hash(12), caller_reference="REQ-DUP-1")
		self.assertIn("different effective reservation from the same caller", str(ctx.exception))

	def test_a_bypass_duplicate_insert_no_longer_raises_integrity_error(self):
		"""Confirms the unique index (REQ-CHG-001 v1.6 D1) is actually gone."""
		_, line = self._new_dhi_line()
		budget = frappe.db.get_value("Procurement Budget Line", line, "budget")
		version = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
		allocation = "TEST-PSA-BYPASS-1"
		for i in range(2):
			fixture_insert(frappe.get_doc(
				{
					"doctype": "Funding Reservation",
					"generated_reference": f"RSV-TEST-BYPASS-{i}",
					"budget": budget,
					"budget_version_at_creation": version,
					"budget_line": line,
					"status": "Active",
					"plan_item": "TEST-PLAN-ITEM-BYPASS",
					"plan_source_allocation": allocation,
					"original_amount": 1,
					"remaining_amount": 1,
					"currency": "KES",
					"correlation_id": f"TEST-BYPASS-{i}",
				}
			))
