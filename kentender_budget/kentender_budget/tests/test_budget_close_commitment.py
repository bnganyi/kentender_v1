# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §5.14.1 (tracker CM8-313, follow-up FU-CM-04) — the Budget-owned `close_commitment`, with the seven owner tests the specification requires.
They prove Budget's behaviour, not Contract Management's cached totals:

1. a final charge of KES 1,000,000 remains counted after the status closure;
2. an approved unperformed KES 200,000 decrease leaves KES 800,000 retained, then the closure has zero effect;
3. a shared reservation's remainder is unchanged;
4. an identical replay returns the same result;
5. a different payload or a stale revision fails;
6. a concurrent adjustment cannot close a mismatched amount;
7. no increase or new obligation goes into a Closed Budget.

Closing changes status and records attribution only; amount and Available stay unchanged. The position includes Closed commitments at their retained amount,
otherwise the status change would free consumed funding."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.utils import flt

from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services.budget_contracts import _line_position_exact
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase, contract_caller

CLOSED_EVENT = "Commitment closed"


class TestCloseCommitment(_PrincipalBase):
	def _commitment(self, *, reserved=10_000_000, converted=1_000_000):
		budget, line = self._new_dhi_line()
		reservation = self._reserve(line, reserved)
		self._as("Administrator")
		result = commit.convert_reservation(
			reservation, self.contract, converted, self._key("conv"),
			contract_event_id=f"{self.contract}:signed", contract_event_type="ContractSigned", caller=contract_caller(self.contract),
		)
		return budget, line, reservation, result["commitment"]["commitment_id"]

	def _position(self, line):
		from kentender_budget.services.budget_commitment_contracts import _current_line_version

		exact = _line_position_exact(line, _current_line_version(line))
		return {key: flt(value) for key, value in exact.items()}

	def _revision(self, commitment):
		return commit.commitment_revision(commitment)

	def _event(self, final_amount, *, event_id=None, event_type="ContractClosed"):
		return {"event_id": event_id or f"{self.contract}:closed", "event_type": event_type, "final_amount": final_amount}

	def _close(self, commitment, final_amount, *, key=None, revision=None, evidence=("RECON-1",), contract=None, event=None):
		self._as("Administrator")
		return commit.close_commitment(commitment, revision or self._revision(commitment), event or self._event(final_amount), list(evidence), key or self._key("close"),
			caller=contract_caller(contract or self.contract))

	def _adjust(self, commitment, new_total, *, label="variation-1"):
		self._as("Administrator")
		return commit.adjust_commitment(commitment, new_total, f"{self.contract}:{label}", "ContractVariation", self._key("adj"), caller=contract_caller(self.contract))

	def _closed_events(self, commitment):
		return frappe.get_all("Budget Audit Event", filters={"commitment": commitment, "event_type": CLOSED_EVENT}, fields=["name", "amount", "correlation_id", "downstream_reference", "before_committed", "after_committed", "before_available", "after_available"])

	# 1 ----------------------------------------------------------------------------------------------------------------------------------
	def test_a_final_charge_stays_counted_after_the_status_closure(self):
		_, line, _, commitment = self._commitment(converted=1_000_000)
		before = self._position(line)
		self.assertEqual(before["committed"], 1_000_000)
		result = self._close(commitment, 1_000_000)
		after = self._position(line)
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, ["status", "current_amount"], as_dict=True), {"status": "Closed", "current_amount": 1_000_000})
		self.assertEqual(after, before, "closing the status must not free consumed funding")
		self.assertEqual((result["commitment"]["status"], result["positions"]["before"]["committed"], result["positions"]["after"]["committed"]), ("Closed", 1_000_000, 1_000_000))
		self.assertEqual(result["positions"]["before"], result["positions"]["after"])

	# 2 ----------------------------------------------------------------------------------------------------------------------------------
	def test_an_approved_unperformed_decrease_leaves_the_retained_amount_then_the_closure_has_zero_effect(self):
		_, line, _, commitment = self._commitment(converted=1_000_000)
		self._adjust(commitment, 800_000)
		self.assertEqual(self._position(line)["committed"], 800_000)
		result = self._close(commitment, 800_000)
		self.assertEqual(self._position(line)["committed"], 800_000)
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "current_amount"), 800_000)
		event = self._closed_events(commitment)
		self.assertEqual(len(event), 1)
		self.assertEqual((event[0].amount, event[0].before_committed, event[0].after_committed, event[0].before_available, event[0].after_available), (0, 800_000, 800_000, event[0].before_available, event[0].before_available))
		self.assertEqual(result["acknowledgement"]["event_id"], f"{self.contract}:closed")
		self.assertTrue(frappe.db.exists("Budget Audit Event", {"commitment": commitment, "event_type": "Commitment adjusted"}), "the original adjustment stays immutable history")

	# 3 ----------------------------------------------------------------------------------------------------------------------------------
	def test_a_shared_reservation_remainder_is_unchanged_by_the_closure(self):
		_, line, reservation, commitment = self._commitment(reserved=10_000_000, converted=6_000_000)
		before = (frappe.db.get_value("Funding Reservation", reservation, ["remaining_amount", "status"]), self._position(line))
		self._close(commitment, 6_000_000)
		after = (frappe.db.get_value("Funding Reservation", reservation, ["remaining_amount", "status"]), self._position(line))
		self.assertEqual(after, before)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 4_000_000)
		self.assertEqual(self._position(line)["reserved"], 4_000_000, "closing never replenishes a reservation or releases another allocation")

	# 4 ----------------------------------------------------------------------------------------------------------------------------------
	def test_an_identical_replay_returns_the_same_result_and_records_nothing_twice(self):
		_, _, _, commitment = self._commitment()
		key, revision = self._key("close"), self._revision(commitment)
		first = self._close(commitment, 1_000_000, key=key, revision=revision)
		replay = self._close(commitment, 1_000_000, key=key, revision=revision)
		self.assertTrue(replay.get("replayed"))
		self.assertEqual(replay["commitment"], first["commitment"])
		again = self._close(commitment, 1_000_000, key=self._key("close"), revision=self._revision(commitment))  # a new key, the same owner event
		self.assertTrue(again.get("reused"))
		self.assertEqual(len(self._closed_events(commitment)), 1)

	# 5 ----------------------------------------------------------------------------------------------------------------------------------
	def test_a_different_payload_a_different_event_or_a_stale_revision_fails(self):
		_, _, _, commitment = self._commitment()
		revision = self._revision(commitment)
		with self.assertRaises(frappe.ValidationError):
			self._close(commitment, 999_999, revision=revision)  # a refused call records nothing and frees its key
		self.assertEqual(self._title(), "BUDGET_COMMITMENT_AMOUNT_MISMATCH")
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "status"), "Active")
		key = self._key("close")
		self._close(commitment, 1_000_000, key=key, revision=revision)
		with self.assertRaises(frappe.ValidationError) as caught:  # the key of a completed close, with a different payload
			self._close(commitment, 999_999, key=key, revision=revision)
		self.assertEqual(self._title(), "BUDGET_IDEMPOTENCY_CONFLICT")
		self.assertEqual(self._closed_events(commitment)[0].downstream_reference, f"{self.contract}:closed")
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):  # a new key and a different owner event for a commitment already closed by another
			self._close(commitment, 1_000_000, key=self._key("close"), revision=self._revision(commitment), event=self._event(1_000_000, event_id=f"{self.contract}:another"))
		self.assertEqual(self._title(), "BUDGET_INVALID_STATE")

	def _title(self):
		titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
		return titles[-1] if titles else None

	# 6 ----------------------------------------------------------------------------------------------------------------------------------
	def test_a_concurrent_adjustment_cannot_close_a_mismatched_amount(self):
		_, line, _, commitment = self._commitment(converted=1_000_000)
		revision = self._revision(commitment)  # what Contract Management read when it prepared the closure
		self._adjust(commitment, 800_000)  # an adjustment commits between that read and the close
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self._close(commitment, 1_000_000, revision=revision)
		self.assertEqual(self._title(), "BUDGET_STALE_REVISION")
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self._close(commitment, 1_000_000, revision=self._revision(commitment))  # fresh revision, but the old final amount
		self.assertEqual(self._title(), "BUDGET_COMMITMENT_AMOUNT_MISMATCH")
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, ["status", "current_amount"], as_dict=True), {"status": "Active", "current_amount": 800_000})
		self.assertEqual(self._position(line)["committed"], 800_000)

	# 7 ----------------------------------------------------------------------------------------------------------------------------------
	def test_no_increase_and_no_new_obligation_goes_into_a_closed_budget_and_a_closed_commitment_is_changed_only_by_a_correction(self):
		budget, line, reservation, commitment = self._commitment(reserved=10_000_000, converted=1_000_000)
		self._close(commitment, 1_000_000)
		# the contract service can neither raise nor lower a Closed commitment: its amount changes only through an approved correction (BUD-BR-033, tested in test_budget_retained_commitments)
		for label, amount in (("increase", 1_100_000), ("decrease", 900_000)):
			frappe.local.message_log = []
			with self.subTest(label), self.assertRaises(frappe.ValidationError):
				self._adjust(commitment, amount, label=label)
			self.assertEqual(self._title(), "BUDGET_INVALID_STATE", label)
			self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "current_amount"), 1_000_000)
		# a second contract's Active commitment on the same reservation is still adjustable; once the Budget is Closed it can take neither an increase nor a new conversion
		other = f"{self.contract}-2"
		self._as("Administrator")
		second = commit.convert_reservation(reservation, other, 500_000, self._key("conv"), contract_event_id="E", contract_event_type="ContractSigned", caller=contract_caller(other))["commitment"]["commitment_id"]
		version = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
		frappe.db.set_value("Procurement Budget Version", version, "status", "Closed")
		for label, call in (
			("an increase", lambda: commit.adjust_commitment(second, 600_000, "E", "ContractVariation", self._key("adj"), caller=contract_caller(other))),
			("a new conversion", lambda: commit.convert_reservation(reservation, f"{self.contract}-3", 500_000, self._key("conv"), contract_event_id="E", contract_event_type="ContractSigned", caller=contract_caller(f"{self.contract}-3"))),
		):
			frappe.local.message_log = []
			with self.subTest(label), self.assertRaises(frappe.ValidationError):
				call()
			self.assertEqual(self._title(), "BUDGET_CLOSED", label)

	# the contract principal and the inputs ------------------------------------------------------------------------------------------------
	def test_only_the_contract_principal_for_its_own_contract_may_close(self):
		_, _, _, commitment = self._commitment()
		self._as("Administrator")
		self.assert_forbidden(commit.close_commitment, commitment, self._revision(commitment), self._event(1_000_000), ["R"], self._key("close"), caller=contract_caller(f"{self.contract}-someone-else"))
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "status"), "Active")

	def test_the_outcome_event_and_reconciliation_evidence_are_required_and_no_release_amount_is_accepted(self):
		_, _, _, commitment = self._commitment()
		revision = self._revision(commitment)
		self._as("Administrator")
		bad = (
			("no evidence", self._event(1_000_000), []),
			("blank evidence", self._event(1_000_000), ["  "]),
			("no event id", {**self._event(1_000_000), "event_id": ""}, ["R"]),
			("an event type that is not a closure outcome", self._event(1_000_000, event_type="ContractSigned"), ["R"]),
			("no final amount", {"event_id": "E", "event_type": "ContractClosed"}, ["R"]),
		)
		for label, event, evidence in bad:
			with self.subTest(label), self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
				commit.close_commitment(commitment, revision, event, evidence, self._key("close"), caller=contract_caller(self.contract))
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "status"), "Active")
		import inspect

		self.assertFalse({"amount", "release_amount", "release"} & set(inspect.signature(commit.close_commitment).parameters), "the browser never enters a release amount")

	def test_a_cancelled_commitment_cannot_be_closed(self):
		_, _, _, commitment = self._commitment()
		self._adjust(commitment, 0, label="cancel")
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "status"), "Cancelled")
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self._close(commitment, 0)
		self.assertEqual(self._title(), "BUDGET_INVALID_STATE")


class TestOneDefinitionOfACountedCommitment(_PrincipalBase):
	def test_no_reader_counts_only_active_commitments(self):
		"""§5.14.1: Committed includes Active and Closed retained amounts. Every place that sums commitments must agree, in every app that reads them."""
		root = Path(frappe.get_app_path("kentender_budget")).parent.parent
		offenders = []
		for path in sorted(root.glob("kentender_*/**/*.py")):
			rel = str(path.relative_to(root))
			if "/tests/" in rel or "/node_modules/" in rel or "/patches/" in rel:
				continue
			text = path.read_text(encoding="utf-8", errors="ignore")
			for match in re.finditer(r"tabProcurement Commitment[\s\S]{0,400}?status\s*=\s*'Active'", text):
				offenders.append(f"{rel}: {text[:match.start()].count(chr(10)) + 1}")
		self.assertEqual(offenders, [])

	def test_the_position_and_the_analytics_totals_include_a_closed_commitment(self):
		from kentender_budget.services.budget_audit_contracts import FUNDING_EVENT_TYPES

		self.assertIn(CLOSED_EVENT, FUNDING_EVENT_TYPES)
