# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.17 §8.9 / §9.5 / §15.9 — the bounded Requisitions cancellation mode of `release_reservation`
(BUD-CR-AC-001, 003, 004, 006, 010 at Budget's grain).

The fixture is CR-F02's Budget half: two reservations on one Budget Line (KES 4m and KES 6m), created by one
Requisition. The real Planning, Requisitions and Tenders adapters run together in
`procurement_requisitions/tests/test_cancellation_recovery_integration.py`."""

from __future__ import annotations

from decimal import Decimal

import frappe

from kentender_budget.services import budget_cancellation_release as cancel_release
from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services.budget_cancellation_release import CancellationReleaseError, RELEASE
from kentender_budget.services.budget_contracts import _line_position_exact
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase, contract_caller, req

REFERENCE = "REQ-CR-1"
_DEFAULT = object()


class _ReleaseBase(_PrincipalBase):
	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		budgets = [name for doctype, name in cls._cleanup if doctype == "Procurement Budget"]
		if budgets:
			frappe.db.delete(RELEASE, {"budget": ("in", budgets)})
		super().tearDownClass()

	def two_on_one_line(self, reference: str = REFERENCE):
		_, line = self._new_dhi_line()
		first = self._reserve(line, 4_000_000, reference=reference, plan_item="TEST-PPI-CR")
		second = self._reserve(line, 6_000_000, reference=reference, plan_item="TEST-PPI-CR")
		self._as("Administrator")
		return line, first, second

	def spec(self, reservation: str, *, amount=None, **overrides) -> dict:
		if not frappe.db.exists("Funding Reservation", reservation):  # a reservation that is not recorded
			return {"reservation": reservation, "drawdown_line_id": "DDL-UNKNOWN", "plan_source_allocation": "", "amount": amount or "1.00", **overrides}
		doc = frappe.get_doc("Funding Reservation", reservation)
		row = {
			"reservation": reservation, "drawdown_line_id": doc.drawdown_line_id, "plan_source_allocation": doc.plan_source_allocation,
			"amount": amount if amount is not None else str(doc.original_amount),
		}
		row.update(overrides)
		return row

	def release(self, specs, *, cancellation="TDC-1", recovery="CRR-1", key=None, reference=REFERENCE, caller=_DEFAULT):
		return cancel_release.release_reservations_for_cancelled_tender(
			recovery_id=recovery, cancellation_id=cancellation, requisition_reference=reference, releases=specs,
			idempotency_key=key or self._key("cr"), caller=req(reference) if caller is _DEFAULT else caller,
		)

	def position(self, line: str) -> dict[str, Decimal]:
		return _line_position_exact(line, cancel_release._current_line_version(line))

	def code_of(self, fn, *args, **kwargs):
		with self.assertRaises(CancellationReleaseError) as caught:
			fn(*args, **kwargs)
		return caught.exception

	def events(self, reservation: str) -> int:
		return frappe.db.count("Budget Audit Event", {"reservation": reservation})


class TestCrF02TheCompleteSetIsReleasedTogether(_ReleaseBase):
	def test_both_reservations_on_one_line_release_exactly_once(self):
		line, first, second = self.two_on_one_line()
		before = self.position(line)
		self.assertEqual((before["reserved"], before["committed"]), (Decimal("10000000.00"), Decimal("0.00")))

		result = self.release([self.spec(first), self.spec(second)])

		after = self.position(line)
		self.assertEqual(result["total"], "10000000.00")
		self.assertEqual(after["reserved"], before["reserved"] - Decimal("10000000.00"))
		self.assertEqual(after["available"], before["available"] + Decimal("10000000.00"))
		self.assertEqual((after["approved"], after["committed"]), (before["approved"], before["committed"]))
		for name, amount in ((first, "4000000.00"), (second, "6000000.00")):
			doc = frappe.get_doc("Funding Reservation", name)
			self.assertEqual((doc.status, float(doc.remaining_amount), float(doc.original_amount)), ("Released", 0.0, float(amount)))
			event = frappe.get_all("Budget Audit Event", filters={"reservation": name, "event_type": "Reservation released"}, fields=["downstream_reference", "reason", "amount", "before_reserved", "after_reserved"])
			self.assertEqual(len(event), 1)
			self.assertEqual(event[0].downstream_reference, "CRR-1:TDC-1")
			self.assertIn("TenderCancelled", event[0].reason)
			self.assertEqual(float(event[0].amount), float(amount))
			self.assertGreater(float(event[0].before_reserved), float(event[0].after_reserved))
		rows = frappe.get_all(RELEASE, filters={"cancellation_id": "TDC-1"}, fields=["release_key", "reservation", "recovery_id"])
		self.assertEqual(len(rows), 2)
		self.assertEqual({r.recovery_id for r in rows}, {"CRR-1"})

	def test_a_failing_second_leg_releases_neither(self):
		line, first, second = self.two_on_one_line()
		self._as("Administrator")
		commit.convert_reservation(
			second, "CTR-CR-1", 1_000_000, self._key("conv"), contract_event_id="CTR-CR-1:signed", contract_event_type="ContractSigned", caller=contract_caller("CTR-CR-1"),
		)
		before = self.position(line)
		events_before = (self.events(first), self.events(second))
		error = self.code_of(self.release, [self.spec(first), self.spec(second)])
		self.assertEqual(error.code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertEqual(error.detail["reservation"], second)
		self.assertEqual(frappe.db.get_value("Funding Reservation", first, "status"), "Active")
		self.assertEqual(self.position(line), before)
		self.assertEqual((self.events(first), self.events(second)), events_before)
		self.assertEqual(frappe.db.count(RELEASE, {"cancellation_id": "TDC-1"}), 0)


class TestReplayAndUniqueness(_ReleaseBase):
	def test_the_same_key_returns_the_first_result_and_changes_nothing(self):
		line, first, second = self.two_on_one_line()
		key = self._key("same")
		one = self.release([self.spec(first), self.spec(second)], key=key)
		events = (self.events(first), self.events(second))
		again = self.release([self.spec(first), self.spec(second)], key=key)
		self.assertEqual(again["total"], one["total"])
		self.assertEqual((self.events(first), self.events(second)), events)

	def test_a_new_key_for_the_same_cancellation_reuses_the_release(self):
		line, first, second = self.two_on_one_line()
		self.release([self.spec(first), self.spec(second)])
		events = (self.events(first), self.events(second))
		again = self.release([self.spec(first), self.spec(second)], key=self._key("new"))
		self.assertTrue(again["all_reused"])
		self.assertEqual((self.events(first), self.events(second)), events)
		self.assertEqual(frappe.db.count(RELEASE, {"cancellation_id": "TDC-1"}), 2)

	def test_the_same_key_with_changed_facts_is_an_idempotency_conflict(self):
		line, first, second = self.two_on_one_line()
		key = self._key("clash")
		self.release([self.spec(first), self.spec(second)], key=key)
		with self.assertRaises(frappe.ValidationError) as caught:
			self.release([self.spec(first)], key=key)
		self.assertIn("idempot", str(caught.exception).lower() + "".join(m.get("title", "") for m in (frappe.local.message_log or []) if isinstance(m, dict)).lower())

	def test_a_second_cancellation_cannot_release_what_the_first_released(self):
		line, first, second = self.two_on_one_line()
		self.release([self.spec(first), self.spec(second)])
		error = self.code_of(self.release, [self.spec(first), self.spec(second)], cancellation="TDC-2", recovery="CRR-2")
		self.assertEqual(error.code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertIn("another cancellation", error.detail["cause"])


class TestWhatIsNeverReleased(_ReleaseBase):
	def test_a_reservation_released_for_another_reason_is_not_released_again(self):
		line, first, second = self.two_on_one_line()
		commit.release_reservation(first, None, f"{REFERENCE}:revoked", "ProcurementRequisitionRevoked", self._key("other"), caller=req(REFERENCE))
		error = self.code_of(self.release, [self.spec(first), self.spec(second)])
		self.assertEqual(error.code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertIn("another reason", error.detail["cause"])
		self.assertEqual(frappe.db.get_value("Funding Reservation", second, "status"), "Active")

	def test_a_converted_reservation_blocks_the_whole_set(self):
		line, first, second = self.two_on_one_line()
		commit.convert_reservation(
			first, "CTR-CR-2", 4_000_000, self._key("conv"), contract_event_id="CTR-CR-2:signed", contract_event_type="ContractSigned", caller=contract_caller("CTR-CR-2"),
		)
		error = self.code_of(self.release, [self.spec(first), self.spec(second)])
		self.assertEqual(error.code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertEqual(frappe.db.get_value("Funding Reservation", second, "status"), "Active")

	def test_a_partly_used_reservation_is_never_repaired_by_guessing(self):
		line, first, second = self.two_on_one_line()
		frappe.db.set_value("Funding Reservation", second, "remaining_amount", 5_000_000, update_modified=False)  # a test property the services cannot produce
		error = self.code_of(self.release, [self.spec(first), self.spec(second)])
		self.assertEqual(error.code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertIn("Part of the reservation", error.detail["cause"])

	def test_another_requisitions_reservation_is_refused(self):
		line, first, second = self.two_on_one_line()
		other = self._reserve(self._new_dhi_line()[1], 1_000_000, reference="REQ-OTHER-CR", plan_item="TEST-PPI-CR2")
		self._as("Administrator")
		error = self.code_of(self.release, [self.spec(first), self.spec(second), self.spec(other)])
		self.assertEqual(error.code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertEqual(error.detail["reservation"], other)
		self.assertEqual(frappe.db.get_value("Funding Reservation", first, "status"), "Active")

	def test_the_wrong_drawdown_line_or_amount_is_refused(self):
		line, first, second = self.two_on_one_line()
		self.assertEqual(self.code_of(self.release, [self.spec(first, drawdown_line_id="DDL-WRONG"), self.spec(second)]).code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertEqual(self.code_of(self.release, [self.spec(first, amount="3999999.00"), self.spec(second)]).code, "BUDGET_CANCELLATION_RECOVERY_INVALID")
		self.assertEqual(self.code_of(self.release, [self.spec("NO-SUCH-RESERVATION")]).code, "BUDGET_CANCELLATION_RECOVERY_INVALID")

	def test_a_reservation_that_changed_after_it_was_pinned_is_a_conflict(self):
		line, first, second = self.two_on_one_line()
		basis = cancel_release.get_cancellation_release_basis(
			cancellation_id="TDC-1", requisition_reference=REFERENCE, releases=[self.spec(first), self.spec(second)], caller=req(REFERENCE),
		)
		self.assertTrue(basis["supported"])
		pinned = {r["reservation"]: r["revision"] for r in basis["reservations"]}
		frappe.db.set_value("Funding Reservation", first, "status", "Needs Attention", update_modified=False)  # a revalidation outcome the services produce elsewhere
		error = self.code_of(self.release, [self.spec(first, expected_revision=pinned[first]), self.spec(second, expected_revision=pinned[second])])
		self.assertEqual(error.code, "BUDGET_CANCELLATION_RECOVERY_CONFLICT")
		self.assertEqual(frappe.db.get_value("Funding Reservation", second, "status"), "Active")


class TestTheBasisRead(_ReleaseBase):
	def test_the_basis_says_what_a_release_would_do_and_changes_nothing(self):
		line, first, second = self.two_on_one_line()
		commit.convert_reservation(
			second, "CTR-CR-3", 6_000_000, self._key("conv"), contract_event_id="CTR-CR-3:signed", contract_event_type="ContractSigned", caller=contract_caller("CTR-CR-3"),
		)
		events = (self.events(first), self.events(second))
		basis = cancel_release.get_cancellation_release_basis(
			cancellation_id="TDC-1", requisition_reference=REFERENCE, releases=[self.spec(first), self.spec(second)], caller=req(REFERENCE),
		)
		by = {r["reservation"]: r for r in basis["reservations"]}
		self.assertEqual((by[first]["verdict"], by[second]["verdict"]), ("ok", "invalid"))
		self.assertFalse(basis["supported"])
		self.assertEqual((self.events(first), self.events(second)), events)
		self.assertEqual(frappe.db.get_value("Funding Reservation", first, "status"), "Active")


class TestAClosedBudgetHistoricalHold(_ReleaseBase):
	def test_a_closed_budget_records_its_closure_and_gains_no_spending_authority(self):
		line, first, second = self.two_on_one_line()
		budget = frappe.db.get_value("Funding Reservation", first, "budget")
		version = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
		# `_close_budget` refuses while a hold remains, so a held reservation on a Closed Budget is unreachable through the services;
		# the status is set directly to reach the historical case the specification names (BUD-CR-AC-010) and put back below.
		frappe.db.set_value("Procurement Budget Version", version, "status", "Closed", update_modified=False)
		try:
			result = self.release([self.spec(first), self.spec(second)])
		finally:
			frappe.db.set_value("Procurement Budget Version", version, "status", "Active", update_modified=False)
		self.assertEqual({r["closure"] for r in result["released"]}, {"Budget Closed"})
		self.assertEqual(frappe.db.get_value("Funding Reservation", first, "status"), "Released")


class TestWhoMayCallIt(_ReleaseBase):
	def test_only_the_requisition_that_created_the_reservations_may_call_it(self):
		line, first, second = self.two_on_one_line()
		for caller in (None, contract_caller("CTR-X"), req("REQ-NOT-THIS-ONE")):
			with self.subTest(caller=caller):
				self.assert_forbidden(self.release, [self.spec(first)], caller=caller)
		self.assertEqual(frappe.db.get_value("Funding Reservation", first, "status"), "Active")
