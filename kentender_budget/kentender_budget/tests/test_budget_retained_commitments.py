# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.13 proposal (follow-up FU-CM-59, FU-CM-04; owner decision 1, 16 October 2026): Committed is the retained amount of every Active **and Closed** commitment. Closing releases nothing.

`test_budget_close_commitment` proves the position and the closure itself. These tests prove what a Closed commitment protects and how its amount can change:

* a successor cannot reduce a line below what a Closed commitment still holds (the revision floor), and cannot omit a line whose only protection is a Closed commitment;
* the contract service can neither raise nor lower a Closed commitment: only a **correction** can lower it. A Budget Officer records it with a reason, evidence and a Contract Management reference, and a
  *different* Budget Approver decides it. Approving returns exactly the decrease to Available, leaves the reservation and every earlier event as they were, and appends one ledger event with the
  amounts before and after. Returning changes nothing. A correction is still possible after the Budget is Closed, and never raises an amount.

The reservation's unused remainder is released first, so the Closed commitment is the only thing protecting the line: a reader that counted only Active commitments would see none."""

from __future__ import annotations

import frappe
from frappe.utils import flt

from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services import budget_commitment_corrections as corrections
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_contracts import _line_position_exact
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller
from kentender_budget.tests.test_bud_chg_001_v19_usability import _V19Base
from kentender_budget.utils.version_stamp import stamped
from kentender_core.services.command_write_guard import CommandWriteError
from kentender_core.services.responsibility_errors import ResponsibilityError

DHI = "Digital health infrastructure programme"
HWD = "Digital health workforce development"


class _ClosedCommitmentBase(_V19Base):
	"""An Active allocation whose DHI line holds one KES 60m commitment, closed, with nothing else reserved."""

	def setUp(self):
		super().setUp()
		self.contract = f"CTR-RETAIN-{self.suffix}-{frappe.generate_hash(length=4)}"
		self.caller = service_caller(PRINCIPAL_CONTRACT, reference=self.contract)
		self.fy, self.budget, self.v1 = self._active()
		self.dhi, self.hwd = self._line(self.v1, DHI), self._line(self.v1, HWD)
		self.reservation = self._reserve(self.dhi, 80_000_000, ref=f"REQ-RETAIN-{self.suffix}")
		self._as("Administrator")
		converted = commit.convert_reservation(
			self.reservation, self.contract, 60_000_000, f"conv-{self.contract}", contract_event_id=f"{self.contract}:signed", contract_event_type="ContractSigned", caller=self.caller,
		)
		self.commitment = converted["commitment"]["commitment_id"]
		commit.release_reservation(self.reservation, 20_000_000, f"{self.contract}:unused", "ContractUnusedAmount", f"rel-{self.contract}", caller=self.caller)
		commit.close_commitment(
			self.commitment, commit.commitment_revision(self.commitment), {"event_id": f"{self.contract}:closed", "event_type": "ContractClosed", "final_amount": 60_000_000},
			["RECON-RETAIN"], f"close-{self.contract}", caller=self.caller,
		)

	def position(self):
		exact = _line_position_exact(self.dhi, commit._current_line_version(self.dhi))
		return {key: flt(value) for key, value in exact.items()}


class TestACorrectionOfAClosedCommitment(_ClosedCommitmentBase):
	# `self.dual` comes from the lifecycle base: one user holding both Budget Officer and Budget Approver, so it can be shown that it cannot approve its own correction
	def record(self, new_amount=45_000_000, *, user=None, **overrides):
		self._as(user or self.officer)
		payload = {
			"commitment": self.commitment, "new_amount": new_amount, "reason": "The supplier delivered less than was ordered.", "evidence": ["RECON-DECREASE", "MINUTE-17"],
			"contract_reference": f"{self.contract}:closure-correction-1", "idempotency_key": f"rec-{frappe.generate_hash(length=10)}",
		}
		payload.update(overrides)
		return corrections.record_commitment_correction(payload)

	def decide(self, correction, decision="Approve", *, user=None, reason="", key=None):
		self._as(user or self.approver)
		return corrections.decide_commitment_correction({"correction": correction, "decision": decision, "reason": reason, "idempotency_key": key or f"dec-{frappe.generate_hash(length=10)}"})

	def reservation_row(self):
		return frappe.db.get_value("Funding Reservation", self.reservation, ["remaining_amount", "original_amount", "status", "modified"], as_dict=True)

	def events(self):
		return frappe.get_all("Budget Audit Event", filters={"commitment": self.commitment}, fields=["name", "event_type", "amount", "reason", "actor", "downstream_reference", "before_available", "after_available", "modified"], order_by="creation asc")

	def title(self):
		return [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]

	# a valid correction -----------------------------------------------------------------------------------------------------------
	def test_an_approved_correction_returns_exactly_the_decrease_to_available_and_changes_nothing_else(self):
		before, reservation_before, events_before = self.position(), self.reservation_row(), self.events()
		recorded = self.record(45_000_000)
		self.assertTrue(recorded["ok"], recorded)
		correction = recorded["correction"]
		self.assertEqual((correction["status"], correction["before_amount"], correction["after_amount"], correction["decrease"]), ("Awaiting approval", 60_000_000, 45_000_000, 15_000_000))
		self.assertEqual(self.position(), before, "recording a correction moves no money")

		decided = self.decide(correction["id"])
		self.assertTrue(decided["ok"], decided)
		after = self.position()
		self.assertEqual((after["committed"], after["available"], after["reserved"], after["approved"]), (before["committed"] - 15_000_000, before["available"] + 15_000_000, before["reserved"], before["approved"]))
		self.assertEqual(decided["commitment"]["status"], "Closed")
		self.assertEqual(self.reservation_row(), reservation_before, "the reservation is never touched: the money does not go back to it")
		self.assertEqual(decided["correction"]["status"], "Approved")
		self.assertEqual((decided["correction"]["recorded_by"], decided["correction"]["decided_by"]), (self.officer, self.approver))

		# the original entries are untouched, and the correction is one new ledger event carrying who, why, with what evidence and the amounts before and after
		events_after = self.events()
		originals = {e.name: e for e in events_before}
		for event in events_after:
			if event.name in originals:
				self.assertEqual(event, originals[event.name], "an earlier ledger event was edited")
		new = [e for e in events_after if e.name not in originals]
		self.assertEqual([e.event_type for e in new], ["Commitment correction recorded", "Commitment corrected"])
		corrected = new[-1]
		self.assertEqual((corrected.amount, corrected.actor, corrected.downstream_reference, corrected.reason), (45_000_000, self.approver, f"{self.contract}:closure-correction-1", "RECON-DECREASE; MINUTE-17"))
		self.assertEqual((corrected.before_available, corrected.after_available), (40_000_000, 55_000_000))
		self.assertEqual(new[0].actor, self.officer)

	def test_a_correction_to_zero_is_allowed_and_a_second_one_can_follow_a_first(self):
		first = self.record(50_000_000)["correction"]
		self.assertTrue(self.decide(first["id"])["ok"])
		second = self.record(0, evidence=["RECON-FINAL"])["correction"]
		self.assertEqual(second["before_amount"], 50_000_000, "the second correction starts from the amount the first left")
		self.assertTrue(self.decide(second["id"])["ok"])
		self.assertEqual(self.position(), {"approved": 100_000_000, "reserved": 0, "committed": 0, "available": 100_000_000})

	# what a correction must carry ---------------------------------------------------------------------------------------------------
	def test_a_correction_without_evidence_a_contract_reference_or_a_reason_is_refused_and_records_nothing(self):
		for label, overrides, field in (
			("no evidence", {"evidence": []}, "evidence"), ("blank evidence", {"evidence": ["", "  "]}, "evidence"),
			("no contract reference", {"contract_reference": ""}, "contract_reference"), ("a short reason", {"reason": "too short"}, "reason"), ("no reason", {"reason": ""}, "reason"),
		):
			with self.subTest(label):
				result = self.record(**overrides)
				self.assertFalse(result["ok"])
				self.assertEqual(result["code"], "BUDGET_EVIDENCE_REQUIRED")
				self.assertIn(field, result["errors"])
		self.assertEqual(frappe.db.count("Commitment Correction", {"commitment": self.commitment}), 0)
		self.assertEqual(self.position()["committed"], 60_000_000)

	def test_a_correction_can_only_lower_a_closed_commitment(self):
		for label, amount in (("the same amount", 60_000_000), ("a higher amount", 61_000_000)):
			with self.subTest(label):
				result = self.record(amount)
				self.assertFalse(result["ok"])
				self.assertEqual(result["code"], "BUDGET_INVALID_STATE")
		active = self._reserve(self.dhi, 10_000_000, ref=f"REQ-RETAIN-ACT-{self.suffix}")
		contract = f"{self.contract}-ACTIVE"
		self._as("Administrator")
		converted = commit.convert_reservation(active, contract, 6_000_000, f"conv-{contract}", contract_event_id=f"{contract}:signed", contract_event_type="ContractSigned", caller=service_caller(PRINCIPAL_CONTRACT, reference=contract))
		refused = self.record(5_000_000, commitment=converted["commitment"]["commitment_id"])
		self.assertEqual((refused["ok"], refused["code"]), (False, "BUDGET_INVALID_STATE"), "an Active commitment is adjusted by its own contract, not corrected here")
		self.assertEqual(frappe.db.count("Commitment Correction", {"commitment": self.commitment}), 0)

	def test_one_correction_waits_for_approval_at_a_time(self):
		self.assertTrue(self.record(50_000_000)["ok"])
		again = self.record(40_000_000)
		self.assertEqual((again["ok"], again["code"]), (False, "BUDGET_INVALID_STATE"))
		self.assertEqual(frappe.db.count("Commitment Correction", {"commitment": self.commitment}), 1)

	# who may do what ------------------------------------------------------------------------------------------------------------------
	def test_the_person_who_recorded_a_correction_cannot_approve_it_even_holding_both_responsibilities(self):
		correction = self.record(45_000_000, user=self.dual)["correction"]
		with self.assertRaises(ResponsibilityError) as caught:
			self.decide(correction["id"], user=self.dual)
		self.assertEqual(caught.exception.code, "AUTH_SEGREGATION_BLOCKED")
		self.assertEqual(frappe.db.get_value("Commitment Correction", correction["id"], "status"), "Awaiting approval")
		self.assertEqual(self.position()["committed"], 60_000_000)
		self.assertTrue(self.decide(correction["id"], user=self.approver)["ok"], "a different Approver can decide it")

	def test_only_a_budget_officer_records_and_only_a_budget_approver_decides(self):
		with self.assertRaises(ResponsibilityError):
			self.record(45_000_000, user=self.approver)  # an Approver who is not an Officer
		correction = self.record(45_000_000)["correction"]
		with self.assertRaises(ResponsibilityError):
			self.decide(correction["id"], user=self.officer)  # an Officer who is not an Approver
		with self.assertRaises(ResponsibilityError):
			self.decide(correction["id"], user=self.nobody)
		self.assertEqual(frappe.db.get_value("Commitment Correction", correction["id"], "status"), "Awaiting approval")

	def test_a_correction_record_cannot_be_written_outside_the_budget_commands(self):
		correction = self.record(45_000_000)["correction"]
		self._as("Administrator")
		doc = frappe.get_doc("Commitment Correction", correction["id"])
		doc.after_amount = 1
		with self.assertRaises(CommandWriteError):
			doc.save(ignore_permissions=True)

	# returning, stale and replay ---------------------------------------------------------------------------------------------------------
	def test_a_returned_correction_needs_a_reason_and_changes_nothing(self):
		before, events_before = self.position(), len(self.events())
		correction = self.record(45_000_000)["correction"]
		bare = self.decide(correction["id"], "Return")
		self.assertEqual((bare["ok"], bare["code"]), (False, "BUDGET_EVIDENCE_REQUIRED"))
		returned = self.decide(correction["id"], "Return", reason="The evidence does not show the shortfall.")
		self.assertTrue(returned["ok"])
		self.assertEqual((returned["correction"]["status"], returned["correction"]["decided_by"]), ("Returned", self.approver))
		self.assertEqual(self.position(), before)
		self.assertEqual([e.event_type for e in self.events()][events_before:], ["Commitment correction recorded", "Commitment correction returned"])
		again = self.decide(correction["id"])
		self.assertEqual((again["ok"], again["code"]), (False, "BUDGET_INVALID_STATE"), "a decided correction cannot be decided again")
		self.assertTrue(self.record(45_000_000)["ok"], "a returned correction is replaced by recording a new one")

	def test_a_correction_whose_commitment_changed_since_it_was_recorded_is_refused(self):
		correction = self.record(45_000_000)["correction"]
		frappe.db.set_value("Procurement Commitment", self.commitment, "current_amount", 55_000_000)  # simulates another change landing first
		stale = self.decide(correction["id"])
		self.assertEqual((stale["ok"], stale["code"]), (False, "BUDGET_STALE_REVISION"))
		self.assertEqual(frappe.db.get_value("Commitment Correction", correction["id"], "status"), "Awaiting approval")

	def test_a_replay_of_the_same_decision_changes_nothing_more(self):
		correction = self.record(45_000_000)["correction"]
		key = f"dec-fixed-{frappe.generate_hash(length=10)}"  # unique per run: the journal persists between runs
		first = self.decide(correction["id"], key=key)
		again = self.decide(correction["id"], key=key)
		self.assertTrue(again.get("replayed"))
		self.assertEqual(again["correction"]["status"], first["correction"]["status"])
		self.assertEqual(len([e for e in self.events() if e.event_type == "Commitment corrected"]), 1)
		self.assertEqual(self.position()["committed"], 45_000_000)

	# the contract service and a closed budget ---------------------------------------------------------------------------------------------
	def test_the_contract_service_can_neither_raise_nor_lower_a_closed_commitment(self):
		before = self.position()
		for label, amount in (("an increase", 61_000_000), ("a decrease", 45_000_000), ("the same amount", 60_000_000)):
			with self.subTest(label):
				frappe.local.message_log = []
				self._as("Administrator")
				with self.assertRaises(frappe.ValidationError):
					commit.adjust_commitment(self.commitment, amount, f"{self.contract}:{label}", "ContractVariation", f"adj-{self.contract}-{label}", caller=self.caller)
				self.assertIn("BUDGET_INVALID_STATE", self.title())
		self.assertEqual(self.position(), before)
		self.assertEqual(frappe.db.get_value("Procurement Commitment", self.commitment, "current_amount"), 60_000_000)

	def test_a_correction_after_the_budget_is_closed_lowers_the_amount_and_never_raises_it(self):
		version = frappe.db.get_value("Procurement Budget Version", {"budget": self.budget, "status": "Active"}, "name")
		frappe.db.set_value("Procurement Budget Version", version, "status", "Closed")
		raised = self.record(61_000_000)
		self.assertEqual((raised["ok"], raised["code"]), (False, "BUDGET_INVALID_STATE"))
		correction = self.record(45_000_000)["correction"]
		decided = self.decide(correction["id"])
		self.assertTrue(decided["ok"], decided)
		self.assertEqual(frappe.db.get_value("Procurement Commitment", self.commitment, "current_amount"), 45_000_000)
		# the ledger event of a Closed Budget still shows the real approved amount, not zero, and the decrease goes to Available alone
		event = [e for e in self.events() if e.event_type == "Commitment corrected"][-1]
		self.assertEqual((event.before_available, event.after_available), (40_000_000, 55_000_000))
		self.assertEqual(frappe.db.get_value("Budget Audit Event", event.name, ["before_approved", "after_approved"], as_dict=True), {"before_approved": 100_000_000, "after_approved": 100_000_000})
