# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.8, 5.12, 5.18, boards D28, D17-S (plan Phase 7; tracker CM8-704; CM-AC-13, 31, 39; proof level L2 native): payment in instalments and what settlement means.

Payments of KES 500,000 and 300,000 settle one KES 800,000 certification once; more than is left is refused; a payment Finance cancels natively reopens the amount, with the original cash and the reversal
kept apart; cash is only what attributable evidence confirmed, so a posted payment, a zero balance or a credit note is never shown as cash."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
import frappe
from frappe.utils import flt, today

from kentender_contracts.services import errors, payment, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class SettlementCase(ContractCase):
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
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		self.t.appointed()
		self.units = tw.fresh_serials(8)
		self.arrival = self.t.arrive(self.units)["arrival"]
		self.t.inspect(self.arrival, self.units)
		self.t.accept(self.arrival)  # eight accepted: KES 800,000
		self.inv = self.t.claim("SET-1", 8)["invoice"]
		self.t.certify_invoice(self.inv)
		self.t.post_accounting(self.inv)
		self.native = frappe.db.get_value("Contract Invoice", self.inv, "native_invoice")

	def draft(self, amount, reference):
		out = payment.save_finance_draft(self.case, invoice=self.inv, expected_version=self.t.version(), idempotency_key=self.t.key("draft"), actor=self.p["josphat"], mode_of_payment=world.MODE,
			paid_from=world.BANK_ACCOUNT, reference_no=reference, amount=amount)
		return out["payment"]

	def post(self, entry):
		payment.submit_finance_for_approval(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("submit"), actor=self.p["josphat"])
		payment.approve_finance_record(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("approve"), actor=self.p["beatrice"])
		return entry

	def settle(self, entry, evidence="Bank line", date=D("2027-07-23")):
		return payment.record_finance_settlement(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("settle"), actor=self.p["beatrice"], effective_date=date, evidence=evidence)

	def instalment(self, amount, reference):
		entry = self.post(self.draft(amount, reference))
		self.settle(entry, f"Bank line {reference}")
		return entry

	def position(self):
		return payment.invoice_position(self.case, self.inv)

	def state(self):
		return frappe.db.get_value("Contract Invoice", self.inv, "state")

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestInstalments(SettlementCase):
	def test_500_000_and_300_000_settle_one_800_000_certification_once(self):
		self.instalment(500000, "BANK-1")
		self.assertEqual(self.state(), "Partly paid")
		self.assertEqual({k: self.position()[k] for k in ("certified", "recorded", "cash_confirmed", "noncash", "outstanding")}, {"certified": 800000, "recorded": 500000, "cash_confirmed": 500000, "noncash": 0, "outstanding": 300000})
		self.assertIn(("SaveNativeFinanceDraft", "Prepare payment for the remaining 300,000.00.", "actionable"), self.tasks("josphat"))
		self.assertIn(("SaveNativeFinanceDraft", "Following up the remaining 300,000.00.", "waiting"), self.tasks("beatrice"))
		self.instalment(300000, "BANK-2")
		self.assertEqual(self.state(), "Paid")
		self.assertEqual({k: self.position()[k] for k in ("recorded", "cash_confirmed", "outstanding")}, {"recorded": 800000, "cash_confirmed": 800000, "outstanding": 0})
		self.assertEqual(len(frappe.get_all("Contract Settlement", filters={"invoice": self.inv, "state": "Confirmed"})), 2)
		over = refusal(payment.save_finance_draft, self.case, invoice=self.inv, expected_version=self.t.version(), idempotency_key=self.t.key("over"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X", amount=1)
		self.assertIn(over.code, ("CM_INVOICE", "CM_HOLD"), "nothing is left to pay")

	def test_more_than_is_left_is_refused_and_a_second_draft_is_never_made(self):
		self.instalment(500000, "BANK-1")
		over = refusal(payment.save_finance_draft, self.case, invoice=self.inv, expected_version=self.t.version(), idempotency_key=self.t.key("over"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X", amount=400000)
		self.assertEqual((over.code, over.detail["available"]), ("CM_HOLD", 300000))
		first = self.draft(200000, "BANK-2")
		again = self.draft(300000, "BANK-2")
		self.assertEqual(first, again, "saving again updates the maker's draft; it never makes a second")
		self.assertEqual(len([p for p in payment.payments(self.case) if p["docstatus"] == 0]), 1)

	def test_the_amount_posted_is_what_the_guard_allows_even_for_the_last_instalment(self):
		self.instalment(500000, "BANK-1")
		self.instalment(300000, "BANK-2")
		self.assertEqual(flt(frappe.db.get_value("Purchase Invoice", self.native, "outstanding_amount")), 0)


class TestWhatIsCash(SettlementCase):
	def test_a_posted_payment_is_not_cash_until_settlement_is_confirmed(self):
		entry = self.post(self.draft(800000, "BANK-1"))
		self.assertEqual({k: self.position()[k] for k in ("recorded", "unconfirmed", "cash_confirmed", "outstanding")}, {"recorded": 800000, "unconfirmed": 800000, "cash_confirmed": 0, "outstanding": 0})
		self.assertEqual(self.state(), "Certified", "a posted payment, or a zero native balance, is not a paid invoice")
		self.assertEqual(flt(frappe.db.get_value("Purchase Invoice", self.native, "outstanding_amount")), 0)
		self.settle(entry)
		self.assertEqual((self.state(), self.position()["cash_confirmed"], self.position()["unconfirmed"]), ("Paid", 800000, 0))

	def test_a_credit_note_standing_against_the_invoice_is_its_own_fact_and_never_cash(self):
		world.credit_note(self.native, 1, "set1")
		pos = self.position()
		self.assertEqual((pos["credit"], pos["cash_confirmed"], pos["noncash"], pos["outstanding"]), (100000, 0, 0, 800000))
		self.instalment(800000, "BANK-1")
		self.assertEqual({k: self.position()[k] for k in ("cash_confirmed", "credit")}, {"cash_confirmed": 800000, "credit": 100000}, "the credit is shown beside the cash, not inside it")

	def test_only_a_person_independent_of_the_payment_confirms_it(self):
		entry = self.post(self.draft(800000, "BANK-1"))
		maker_with_approval = refusal(payment.record_finance_settlement, self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("s1"), actor=self.p["josphat"], effective_date=D("2027-07-23"), evidence="x")
		self.assertEqual(maker_with_approval.code, "CM_AUTHORITY")
		self.assertIn("evidence", refusal(payment.record_finance_settlement, self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("s2"), actor=self.p["beatrice"], effective_date=D("2027-07-23"), evidence=" ").fields)


class TestReversalAndCorrection(SettlementCase):
	def test_a_payment_cancelled_natively_reopens_the_amount_and_keeps_the_cash_and_the_reversal_apart(self):
		first = self.instalment(500000, "BANK-1")
		second = self.instalment(300000, "BANK-2")
		self.assertEqual(self.state(), "Paid")
		stl = frappe.db.get_value("Contract Settlement", {"native_payment": second}, "name")
		frappe.set_user("Administrator")
		frappe.get_doc("Payment Entry", second).cancel()  # Finance reverses the entry in ERPNext Accounts
		frappe.db.commit()
		self.assertEqual(self.state(), "Partly paid")
		self.assertEqual(frappe.db.get_value("Contract Settlement", stl, "state"), "Reversed")
		self.assertEqual(frappe.db.get_value("Contract Settlement", {"native_payment": first}, "state"), "Confirmed", "the first cash stands")
		pos = self.position()
		self.assertEqual((pos["cash_confirmed"], pos["recorded"], pos["outstanding"]), (500000, 500000, 300000))
		self.assertIn(("SaveNativeFinanceDraft", "Prepare the payment again: 300,000.00 was reversed.", "actionable"), self.tasks("josphat"))
		self.assertIn(("SaveNativeFinanceDraft", "Following up the reversed payment of 300,000.00.", "waiting"), self.tasks("beatrice"))
		self.assertTrue(frappe.db.exists("Contract Event", {"contract_case": self.case, "event_type": "Settlement reversed"}))
		self.instalment(300000, "BANK-3")  # allocate again only after the reversal is reconciled
		self.assertEqual((self.state(), self.position()["cash_confirmed"]), ("Paid", 800000))
		self.assertEqual(sorted(frappe.get_all("Contract Settlement", filters={"invoice": self.inv}, pluck="state")), ["Confirmed", "Confirmed", "Reversed"])

	def test_a_settlement_is_corrected_without_touching_the_ledger_and_the_old_confirmation_stays(self):
		entry = self.post(self.draft(800000, "BANK-1"))
		original = self.settle(entry, "Bank line 44", D("2027-07-23"))["settlement"]
		out = payment.correct_finance_settlement(self.case, settlement=original, effective_date=D("2027-07-24"), evidence="Bank line 45", reason="The statement showed the next day.", expected_version=self.t.version(),
			idempotency_key=self.t.key("fix"), actor=self.p["beatrice"])
		old, new = frappe.get_doc("Contract Settlement", original), frappe.get_doc("Contract Settlement", out["settlement"])
		self.assertEqual((old.state, new.state, new.corrects, str(new.effective_date), new.amount), ("Corrected", "Confirmed", original, D("2027-07-24"), 800000))
		self.assertEqual(self.position()["cash_confirmed"], 800000, "the cash is counted once")
		self.assertEqual(flt(frappe.db.get_value("Payment Entry", entry, "paid_amount")), 800000)

	def test_a_correction_needs_a_reason_the_right_person_and_a_confirmation_that_stands(self):
		entry = self.post(self.draft(800000, "BANK-1"))
		original = self.settle(entry)["settlement"]
		self.assertIn("reason", refusal(payment.correct_finance_settlement, self.case, settlement=original, effective_date=D("2027-07-24"), evidence="x", reason=" ", expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["beatrice"]).fields)
		self.assertEqual(refusal(payment.correct_finance_settlement, self.case, settlement=original, effective_date=D("2027-07-24"), evidence="x", reason="r", expected_version=self.t.version(), idempotency_key=self.t.key("b"), actor=self.p["josphat"]).code, "CM_AUTHORITY")
		payment.correct_finance_settlement(self.case, settlement=original, effective_date=D("2027-07-24"), evidence="x", reason="r", expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["beatrice"])
		self.assertEqual(refusal(payment.correct_finance_settlement, self.case, settlement=original, effective_date=D("2027-07-25"), evidence="y", reason="r2", expected_version=self.t.version(), idempotency_key=self.t.key("d"), actor=self.p["beatrice"]).code, "CM_CHANGED",
			"the corrected confirmation is history; correct the one that stands")
