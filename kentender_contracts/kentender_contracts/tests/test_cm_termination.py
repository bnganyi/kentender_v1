# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.7, 5.11, 5.21, 7 (CM-R-16) and boards D20, D20-P, D20-T, D39-P, D39, D39-C, D39-H (plan Phase 8; tracker CM8-807): termination and its settlement.

Terminated is neither Completed nor Settled. The financial position is generated, the Accounting Officer who did not prepare the request decides, the contract becomes Terminated only when the delivered notice's
effect is recorded, the accepted work stays accepted and payable, the commitment is reduced to the supported obligation as a durable operation, and the settlement is completed only when every remaining item is
settled or named as a surviving obligation. Its completion is its own fact, the lifecycle stays Terminated, and the commitment's closure is acknowledged separately."""

from __future__ import annotations

import frappe

from kentender_contracts.services import errors, funding_closure, holds, intents, payment, position, records, termination, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


EVIDENCE = [{"label": "Default notice and delivery proof", "file": "/private/files/default-notice.pdf"}, {"label": "Legal advice 1", "file": "/private/files/legal-1.pdf"}]


class TerminationCase(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)
		world.ensure_workflow()
		cls.addClassCleanup(world.drop_workflow)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: (setattr(frappe.flags, "kt_cm_funding_fault", None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		self.t.appointed()
		# eight of ten accepted; six invoiced and paid (600,000), two invoiced and certified, unpaid (200,000)
		units = tw.fresh_serials(8)
		arrival = self.t.arrive(units)["arrival"]
		self.t.inspect(arrival, units)
		self.t.accept(arrival)
		self.paid = self.t.claim("INV-T-1", 6)["invoice"]
		self.t.certify_invoice(self.paid)
		self.t.pay(self.paid, "TERM-BANK-1")
		self.unpaid = self.t.claim("INV-T-2", 2)["invoice"]
		self.t.certify_invoice(self.unpaid)

	def ask(self, who="charles", **kw):
		return termination.request(self.case, grounds=kw.pop("grounds", "Material non-delivery"), clause=kw.pop("clause", "Contract clause 8"), recommendation=kw.pop("recommendation", "Terminate unperformed balance"),
			evidence=kw.pop("evidence", EVIDENCE), expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p[who], **kw)

	def decide(self, decision="Approve", who="amina", reason="The grounds are established.", number=1):
		return termination.decide(self.case, termination=number, decision=decision, reason=reason, expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p[who])

	def notice(self, delivered="2027-07-02", effective="2027-07-02", who="charles", number=1, **kw):
		return termination.record_notice(self.case, termination=number, delivered_on=delivered, method=kw.pop("method", "Registered post"), reference=kw.pop("reference", "RP-0042"), effective_on=effective,
			evidence=kw.pop("evidence", [{"label": "Proof of delivery", "file": "/private/files/pod.pdf"}]), expected_version=self.t.version(), idempotency_key=self.t.key("notice"), actor=self.p[who])

	def terminate(self):
		self.ask()
		self.decide()
		return self.notice()

	def row(self, number=1):
		return termination.get(self.case, number)

	def settle_unpaid(self):
		self.t.pay(self.unpaid, "TERM-BANK-2")

	def prepare(self, classified=None, who="charles", reference="TERM-01"):
		return termination.prepare_settlement(self.case, termination=1, finance_reference=reference, classified=classified or [], expected_version=self.t.version(), idempotency_key=self.t.key("prep"), actor=self.p[who])

	def complete(self, who="amina", reason="All required settlement facts reconciled."):
		return termination.complete_settlement(self.case, termination=1, reason=reason, expected_version=self.t.version(), idempotency_key=self.t.key("done"), actor=self.p[who])

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}

	def intent(self, kind):
		return frappe.db.get_value("Contract Operation Intent", {"contract_case": self.case, "operation_kind": kind}, "state")


class TestRequest(TerminationCase):
	def test_the_financial_position_is_generated_from_the_records_not_typed(self):
		self.ask()
		found = records.loads(self.row().financial_json)
		self.assertEqual((found["accepted_value"], found["cash_paid"], found["supported_unpaid"], found["advance_balance"], found["disputed"]), (800_000, 600_000, 200_000, 0, 0))
		self.assertEqual((self.row().state, termination.basis(self.row())["clause"]), ("Requested", "Contract clause 8"))
		self.assertEqual(termination.basis(self.row())["funding"], [{"reservation": "RSV-DEMO-1", "new_total": 800_000}])
		self.assertIn(("DecideContractTermination", "Decide the termination request.", "actionable"), self.tasks("amina"))

	def test_only_a_preparer_requests_with_grounds_a_clause_evidence_and_a_recommendation(self):
		self.assertEqual(refusal(self.ask, who="stranger").code, "CM_AUTHORITY")
		self.assertIn("grounds", refusal(self.ask, grounds=" ").fields)
		self.assertIn("clause", refusal(self.ask, clause="").fields)
		self.assertIn("recommendation", refusal(self.ask, recommendation="").fields)
		self.assertIn("evidence", refusal(self.ask, evidence=[]).fields)
		self.assertFalse(frappe.db.count("Contract Termination", {"contract_case": self.case}))

	def test_one_termination_at_a_time(self):
		self.ask()
		self.assertEqual(refusal(self.ask).code, "CM_CHANGED")

	def test_a_contract_that_is_not_active_cannot_be_terminated_this_way(self):
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Closed")
		self.assertEqual(refusal(self.ask).code, "CM_CHANGED")


class TestDecision(TerminationCase):
	def test_only_the_accounting_officer_decides_never_the_person_who_prepared_it_and_the_production_profile_waits(self):
		self.ask()
		self.assertEqual(refusal(self.decide, who="charles").code, "CM_AUTHORITY")
		frappe.db.set_value("Contract Termination", self.row().name, "requested_by", self.p["amina"])
		self.assertEqual(refusal(self.decide).code, "CM_SEGREGATION")
		frappe.db.set_value("Contract Termination", self.row().name, "requested_by", self.p["charles"])
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "KE-PPADA-2015")
		out = refusal(self.decide)
		self.assertEqual((out.code, out.reasons[0]["detail"]["rule"]), ("CM_RULE", "CM-R-16"))
		self.assertEqual(self.row().state, "Requested")

	def test_a_decision_needs_a_reason_decline_and_return_are_recorded_and_a_return_is_corrected(self):
		self.ask()
		self.assertIn("reason", refusal(self.decide, reason=" ").fields)
		self.decide("Return", reason="Attach the cure-period record.")
		self.assertEqual(self.row().state, "Returned")
		self.assertIn(("RequestContractTermination", "Correct the termination request.", "actionable"), self.tasks("charles"))
		self.ask(correcting=1, recommendation="Terminate the unperformed balance after the cure period")
		self.assertEqual((self.row().state, termination.basis(self.row())["draft"], frappe.db.count("Contract Termination", {"contract_case": self.case})), ("Requested", 2, 1))
		self.decide("Decline", reason="The cure period has not ended.")
		self.assertEqual((self.row().state, records.loads(self.row().decision_json)["reason"]), ("Declined", "The cure period has not ended."))
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Active")
		self.ask()  # a declined termination does not stop a later, better supported one
		self.assertEqual(self.row(2).state, "Requested")

	def test_approval_asks_the_head_of_procurement_to_deliver_the_notice_and_changes_nothing_yet(self):
		self.ask()
		self.decide()
		self.assertEqual((self.row().state, frappe.db.get_value("Contract Case", self.case, "lifecycle")), ("Approved", "Active"))
		self.assertIn(("RecordTerminationNotice", "Deliver the termination notice.", "actionable"), self.tasks("charles"))
		self.assertTrue({t for t in self.tasks("amina") if t[0] == "RecordTerminationNotice" and t[2] == "waiting"})


class TestEffect(TerminationCase):
	def test_the_recorded_delivery_makes_the_contract_terminated_and_the_accepted_work_stays(self):
		out = self.terminate()
		self.assertTrue(out["effective"])
		self.assertEqual((self.row().state, frappe.db.get_value("Contract Case", self.case, "lifecycle")), ("Effective", "Terminated"))
		now = position.position(self.case)["lines"]["L1"]
		self.assertEqual((now["accepted"], now["ordered"]), (8, 10))  # the quantities already accepted are preserved
		self.assertEqual(records.loads(self.row().financial_json)["supported_obligation"], 800_000)
		self.assertEqual(records.loads(self.row().notice_json)["reference"], "RP-0042")

	def test_the_commitment_is_reduced_to_the_supported_obligation_not_to_the_certified_invoices(self):
		self.terminate()
		from kentender_contracts.simulation import funding

		self.assertEqual(funding.Provider().position(self.case)["amount"], 800_000)
		self.assertEqual(self.intent("Funding adjustment"), "Succeeded")
		self.assertFalse(holds.blocking(self.case, "pay"))

	def test_a_failed_reduction_is_pending_holds_spending_and_is_restored_without_asking_again(self):
		frappe.flags.kt_cm_funding_fault = "fail"
		self.terminate()
		self.assertEqual(self.intent("Funding adjustment"), "Uncertain")
		self.assertTrue(holds.blocking(self.case, "new_spending") and holds.blocking(self.case, "pay"))
		frappe.flags.kt_cm_funding_fault = None
		termination.carry_out_effects(self.case, self.p["daniel"])
		termination.carry_out_effects(self.case, self.p["daniel"])
		self.assertEqual(self.intent("Funding adjustment"), "Succeeded")
		self.assertEqual(frappe.db.count("Contract Simulated Funding", {"contract": self.case, "outcome": "Adjusted"}), 1)

	def test_the_notice_needs_its_evidence_and_a_termination_cannot_take_effect_before_it_was_delivered(self):
		self.ask()
		self.decide()
		self.assertEqual(refusal(self.notice, who="stranger").code, "CM_AUTHORITY")
		self.assertIn("method", refusal(self.notice, method=" ").fields)
		self.assertIn("evidence", refusal(self.notice, evidence=[]).fields)
		self.assertIn("effective_on", refusal(self.notice, delivered="2027-07-05", effective="2027-07-02").fields)
		self.assertEqual(self.row().state, "Approved")

	def test_a_later_effective_date_waits_for_its_own_record(self):
		self.ask()
		self.decide()
		out = self.notice(delivered="2027-07-02", effective="2027-07-09")
		self.assertFalse(out["effective"])
		self.assertEqual((self.row().state, frappe.db.get_value("Contract Case", self.case, "lifecycle")), ("Notice delivered", "Active"))
		self.assertIn(("RecordTerminationEffect", "Record that the termination took effect.", "scheduled"), self.tasks("charles"))
		self.assertEqual(refusal(termination.record_effect, self.case, termination=1, expected_version=self.t.version(), idempotency_key=self.t.key("e"), actor=self.p["charles"]).code, "CM_HOLD")
		frappe.flags.kt_cm_clock = "2027-07-09 09:00:00"
		termination.record_effect(self.case, termination=1, expected_version=self.t.version(), idempotency_key=self.t.key("e2"), actor=self.p["charles"])
		self.assertEqual((self.row().state, frappe.db.get_value("Contract Case", self.case, "lifecycle")), ("Effective", "Terminated"))

	def test_a_terminated_contract_takes_no_new_delivery_but_the_accepted_work_is_still_claimed_certified_and_paid(self):
		self.terminate()
		self.assertEqual(refusal(self.t.arrive, tw.fresh_serials(1)).code, "CM_CHANGED")
		self.settle_unpaid()  # Finance settles what was certified before the termination
		self.assertEqual(frappe.db.get_value("Contract Invoice", self.unpaid, "state"), "Paid")
		extra = self.t.claim("INV-T-3", 1)["invoice"]  # a claim is still taken (not refused for the lifecycle); all eight accepted units are claimed already, so it is held as unsupported
		self.assertEqual(frappe.db.get_value("Contract Invoice", extra, "state"), "Held")


class TestSettlement(TerminationCase):
	def test_the_settlement_is_generated_from_the_reconciliation_and_completed_only_when_nothing_unclassified_remains(self):
		self.terminate()
		recon = termination.reconciliation(self.case, self.row())
		self.assertEqual([r["kind"] for r in recon["remaining"]], ["Liability"])  # 200,000 is supported and unpaid
		self.assertEqual((recon["supported_obligation"], recon["unperformed_balance"], recon["budget_decrease"]), (800_000, 200_000, "Acknowledged"))
		self.prepare()
		out = refusal(self.complete)
		self.assertEqual(out.code, "CM_CLOSURE")
		self.assertEqual(out.detail["remaining"][0]["kind"], "Liability")
		self.settle_unpaid()
		self.assertEqual(termination.reconciliation(self.case, self.row())["remaining"], [])
		self.complete()
		self.assertEqual((self.row().state, frappe.db.get_value("Contract Case", self.case, "lifecycle")), ("Settled", "Terminated"))  # never Completed
		done = records.loads(self.row().settlement_json)
		self.assertEqual((done["finance_reference"], done["completed_by"]), ("TERM-01", self.p["amina"]))

	def test_the_settlement_needs_the_finance_reference_and_the_clause_of_each_survivor(self):
		self.terminate()
		self.assertIn("finance_reference", refusal(self.prepare, reference=" ").fields)
		self.assertIn("classified", refusal(self.prepare, classified=[{"kind": "Liability", "ref": "supported unpaid", "basis": " "}]).fields)
		self.assertEqual(refusal(self.prepare, who="stranger").code, "CM_AUTHORITY")

	def test_an_unclassified_debt_blocks_completion_and_a_named_survivor_with_its_clause_does_not(self):
		self.terminate()
		self.settle_unpaid()
		dispute = self.t.claim("INV-T-D", 1)["invoice"]  # a claim the contract does not support stays in dispute
		self.assertEqual(frappe.db.get_value("Contract Invoice", dispute, "state"), "Held")
		recon = termination.reconciliation(self.case, self.row())
		self.assertEqual([r["kind"] for r in recon["remaining"]], ["Dispute"])
		self.prepare()
		self.assertEqual(refusal(self.complete).code, "CM_CLOSURE")
		self.prepare(classified=[{"kind": "Dispute", "ref": "claims in dispute", "basis": "Contract clause 14 (disputes survive termination)"}])
		self.complete()
		self.assertEqual(self.row().state, "Settled")

	def test_the_officer_who_prepared_the_settlement_does_not_complete_it(self):
		self.terminate()
		self.settle_unpaid()
		self.prepare()
		frappe.db.set_value("Contract Termination", self.row().name, "settlement_json", records.dumps({**records.loads(self.row().settlement_json), "prepared_by": self.p["amina"]}))
		self.assertEqual(refusal(self.complete).code, "CM_SEGREGATION")
		self.assertEqual(refusal(self.complete, who="charles").code, "CM_AUTHORITY")

	def test_completing_requests_the_commitment_closure_which_is_acknowledged_separately(self):
		self.terminate()
		self.settle_unpaid()
		self.prepare()
		self.complete()
		self.assertEqual(funding_closure.status(self.case), "Acknowledged")
		self.assertEqual(self.intent("Funding closure"), "Succeeded")
		from kentender_contracts.simulation import funding

		self.assertTrue(funding.Provider().position(self.case)["closed"])
		self.assertEqual(funding.Provider().position(self.case)["amount"], 800_000)  # closing changes status, not the amount

	def test_a_closure_the_owner_has_not_acknowledged_is_pending_and_holds_the_release_of_funds(self):
		self.terminate()
		self.settle_unpaid()
		self.prepare()
		frappe.flags.kt_cm_funding_fault = "fail"
		self.complete()
		self.assertEqual((self.row().state, funding_closure.status(self.case)), ("Settled", "Pending"))
		self.assertTrue(holds.blocking(self.case, "release_funds") and holds.blocking(self.case, "mark_financially_finalised"))
		frappe.flags.kt_cm_funding_fault = None
		termination.carry_out_effects(self.case, self.p["daniel"])
		termination.carry_out_effects(self.case, self.p["daniel"])
		self.assertEqual(funding_closure.status(self.case), "Acknowledged")
		self.assertEqual(frappe.db.count("Contract Simulated Funding", {"contract": self.case, "outcome": "Closed"}), 1)
