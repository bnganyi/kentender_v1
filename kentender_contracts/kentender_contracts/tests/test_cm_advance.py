# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.8, 5.11, 5.12, CM-R-07, boards D29, D29-H, D29-R (plan Phase 7; tracker CM8-705; CM-AC-14, 41; proof level L2 native): an advance follows its own route.

Only where the issued terms provide it, after signature, within the clause and the profile's cap, against a verified guarantee for the advance amount, certified by procurement without any acceptance, paid by
Finance as a native payment against the order (no more than was certified) and confirmed by an independent person. It is recovered on later invoices at the issued rate and set against them natively:
cash of 100,000 + 720,000 + 180,000 = 1,000,000 and the advance is consumed once."""

from __future__ import annotations

import frappe
from frappe.utils import flt, today

from kentender_contracts.native import adapter
from kentender_contracts.services import advance, errors, holds, payment, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class AdvanceCase(ContractCase):
	native = True
	advance = True

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
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], advance=self.advance)
		self.case = self.t.active()
		self.t.appointed()

	# -- steps ------------------------------------------------------------------------------------------------------------------------
	def guarantee(self, amount=100000, beneficiary="Ministry of Health", expires="2027-08-31", issued="2027-06-01"):
		out = advance.record_guarantee(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("g"), actor=self.p["josphat"], issuer="Test Bank", beneficiary=beneficiary, reference="TEST-AG-01",
			amount=amount, issued_on=issued, expires_on=expires)
		return out["security"]

	def verify(self, security):
		return advance.verify_guarantee(self.case, security=security, expected_version=self.t.version(), idempotency_key=self.t.key("v"), actor=self.p["charles"], confirmation_reference="TEST-AG-CONF-01", received_on="2027-07-02")

	def claim(self, amount=100000, reference="ADV-01"):
		return advance.prepare_advance(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("adv"), actor=self.p["david"], claim_reference=reference, amount=amount)["advance"]

	def certify(self, row):
		return advance.sign_advance_certification(self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("cert"), actor=self.p["charles"])

	def pay_advance(self, row, amount=None):
		out = payment.save_advance_payment(self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("pay"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT,
			reference_no="ADV-BANK-1", amount=amount)
		payment.submit_finance_for_approval(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("sub"), actor=self.p["josphat"])
		payment.approve_finance_record(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("app"), actor=self.p["beatrice"])
		return out["payment"]

	def settle(self, entry, evidence="Bank line ADV"):
		return payment.record_finance_settlement(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("settle"), actor=self.p["beatrice"], effective_date="2027-07-05", evidence=evidence)

	def paid_advance(self):
		row = self.claim()
		self.verify(self.guarantee())
		self.certify(row)
		entry = self.pay_advance(row)
		self.settle(entry)
		return row, entry

	def goods(self, count, bad=()):
		units = tw.fresh_serials(count)
		arrival = self.t.arrive(units)["arrival"]
		self.t.inspect(arrival, units, bad=tuple(units[i] for i in bad))
		self.t.accept(arrival)
		return units

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestTheClaim(AdvanceCase):
	def test_the_issued_clause_is_read_from_the_terms_not_assumed(self):
		terms = records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": self.case, "state": "Effective"}, "terms_json"))
		found = advance.clause(terms)
		self.assertEqual((found["percent"], found["amount"], found["recovery_per_unit"], found["recovery_line"]), (10, 100000, 10000, "L1"))

	def test_an_advance_is_claimed_for_at_most_the_clause_and_only_once(self):
		self.assertEqual(refusal(advance.prepare_advance, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["david"], claim_reference="ADV-01", amount=110000).code, "CM_INVOICE")
		self.assertIn("claim_reference", refusal(advance.prepare_advance, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("b"), actor=self.p["david"], claim_reference=" ", amount=100000).fields)
		row = self.claim()
		self.assertEqual(frappe.db.get_value("Contract Advance", row, ["state", "amount", "percent"], as_dict=True), {"state": "Prepared", "amount": 100000, "percent": 10})
		self.assertEqual(refusal(advance.prepare_advance, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["david"], claim_reference="ADV-02", amount=1000).code, "CM_DUPLICATE")

	def test_a_clause_above_the_cap_the_law_allows_is_refused_whatever_the_terms_say(self):
		from unittest import mock

		found = {**advance.clause(records.loads(frappe.db.get_value("Contract Agreement Version", {"contract_case": self.case, "state": "Effective"}, "terms_json"))), "percent": 25.0, "amount": 250000.0}
		with mock.patch.object(advance, "clause", return_value=found):
			exc = refusal(advance.prepare_advance, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["david"], claim_reference="ADV-01", amount=250000)
		self.assertEqual((exc.code, exc.detail["rule"]), ("CM_RULE", "CM-R-07"))
		self.assertIn("20%", exc.detail["reason"])

	def test_only_the_suppliers_representative_claims_it(self):
		self.assertEqual(refusal(advance.prepare_advance, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["charles"], claim_reference="ADV-01", amount=100000).code, "CM_SEGREGATION")

	def test_a_claim_names_the_guarantee_still_to_record_when_none_stands(self):
		self.claim()
		self.assertIn(("RecordContractSecurity", "Record the advance guarantee.", "actionable"), self.tasks("josphat"))
		self.assertIn(("SignAdvanceCertification", "Review the advance and its guarantee.", "blocked"), self.tasks("charles"))


class TestNoAdvanceInTheTerms(AdvanceCase):
	advance = False

	def test_a_contract_whose_terms_provide_no_advance_refuses_a_claim_and_a_guarantee(self):
		exc = refusal(advance.prepare_advance, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["david"], claim_reference="ADV-01", amount=100000)
		self.assertEqual((exc.code, exc.detail["rule"]), ("CM_RULE", "CM-R-07"))
		self.assertEqual(refusal(advance.record_guarantee, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("b"), actor=self.p["josphat"], issuer="Test Bank", beneficiary="Ministry of Health",
			reference="X", amount=1, issued_on="2027-07-01", expires_on="2027-08-31").code, "CM_RULE")


class TestTheGuarantee(AdvanceCase):
	def test_certification_waits_for_a_verified_guarantee_with_a_named_holder(self):
		row = self.claim()
		held = [h for h in holds.open_holds(self.case) if h.key == "ADVANCE_GUARANTEE_NOT_VERIFIED"]
		self.assertEqual((len(held), held[0].reason, held[0].owner, sorted(held[0].blocks)), (1, "The advance guarantee has not been verified.", "Finance advance custodian", ["certify_advance"]))
		exc = refusal(advance.sign_advance_certification, self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_HOLD")
		self.verify(self.guarantee())
		self.assertFalse([h for h in holds.open_holds(self.case) if h.key == "ADVANCE_GUARANTEE_NOT_VERIFIED"])
		self.assertIn(("SignAdvanceCertification", "Review the advance and its guarantee.", "actionable"), self.tasks("charles"))

	def test_a_guarantee_for_less_than_the_advance_the_wrong_beneficiary_or_an_expired_one_is_not_verified(self):
		self.claim()
		small = self.guarantee(amount=50000)
		self.assertIn("confirmation_reference", refusal(self.verify, small).fields)
		wrong = self.guarantee(beneficiary="Another Entity")
		self.assertIn("The beneficiary is Another Entity", refusal(self.verify, wrong).fields["confirmation_reference"])
		old = self.guarantee(expires="2027-07-01")
		self.assertIn("expired", refusal(self.verify, old).fields["confirmation_reference"])

	def test_a_replacement_supersedes_an_unverified_instrument_and_the_earlier_is_kept(self):
		first = self.guarantee(amount=50000)
		second = self.guarantee()
		self.assertEqual((frappe.db.get_value("Contract Security", first, "state"), frappe.db.get_value("Contract Security", second, "state")), ("Superseded", "Recorded"))

	def test_only_the_custodian_records_and_only_procurement_verifies(self):
		self.assertEqual(refusal(advance.record_guarantee, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["julia"], issuer="Test Bank", beneficiary="Ministry of Health",
			reference="X", amount=100000, issued_on="2027-07-01", expires_on="2027-08-31").code, "CM_AUTHORITY")
		sec = self.guarantee()
		self.assertEqual(refusal(advance.verify_guarantee, self.case, security=sec, expected_version=self.t.version(), idempotency_key=self.t.key("b"), actor=self.p["josphat"], confirmation_reference="C", received_on="2027-07-02").code, "CM_AUTHORITY")


class TestPayingAndRecovering(AdvanceCase):
	def test_an_advance_is_certified_without_any_acceptance_paid_natively_and_confirmed_by_an_independent_person(self):
		row = self.claim()
		self.verify(self.guarantee())
		self.certify(row)
		order = records.loads(frappe.db.get_value("Contract Advance", row, "clause_json")) and frappe.db.get_value("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Purchase order"}, "result_reference")
		self.assertEqual(flt(frappe.db.get_value("Purchase Order", order, "cm_advance_certified")), 100000)
		self.assertEqual(frappe.db.get_value("Contract Advance", row, "state"), "Certified")
		self.assertIn(("SaveNativeFinanceDraft", "Prepare the advance payment.", "actionable"), self.tasks("josphat"))
		over = refusal(payment.save_advance_payment, self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("over"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X", amount=100001)
		self.assertEqual((over.code, over.detail["available"]), ("CM_HOLD", 100000))
		entry = self.pay_advance(row)
		self.assertEqual((frappe.db.get_value("Payment Entry", entry, "docstatus"), flt(frappe.db.get_value("Purchase Order", order, "advance_paid"))), (1, 100000))
		self.assertEqual(frappe.db.get_value("Contract Advance", row, "state"), "Certified", "a posted payment is not a settled one")
		self.assertEqual(refusal(payment.record_finance_settlement, self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("s0"), actor=self.p["josphat"], effective_date="2027-07-05", evidence="x").code, "CM_AUTHORITY")
		self.settle(entry)
		self.assertEqual(frappe.db.get_value("Contract Advance", row, "state"), "Paid")
		self.assertEqual(advance.position(self.case), {"advance": row, "certified": 100000, "paid": 100000, "recovered": 0, "outstanding": 100000})

	def test_a_native_advance_beyond_the_certified_amount_is_refused_by_the_guard_on_every_route(self):
		row = self.claim()
		self.verify(self.guarantee())
		self.certify(row)
		order = frappe.db.get_value("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Purchase order"}, "result_reference")
		draft = adapter.advance_draft(order, world.identity("adv excess", "Native payment"), amount=150000, mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="EXCESS")
		frappe.db.commit()
		from kentender_contracts.native import payment_guard

		with payment_guard.native_operation("test"):
			with self.assertRaises(errors.ContractError) as caught:
				frappe.get_doc("Payment Entry", draft).submit()
		self.assertEqual(caught.exception.code, "CM_HOLD")
		self.assertIn("more than the supported advance", caught.exception.detail["reason"])

	def test_cash_of_100000_720000_and_180000_makes_one_million_and_the_advance_is_consumed_once(self):
		row, entry = self.paid_advance()
		self.goods(8)  # eight accepted: KES 800,000
		first = self.t.claim("ADV-INV-1", 8)["invoice"]
		invoice = frappe.get_doc("Contract Invoice", first)
		plan = advance.recovery_plan(self.case, invoice)
		self.assertEqual({k: plan[k] for k in ("paid", "rate", "units", "recovery", "cash", "remaining")}, {"paid": 100000, "rate": 10000, "units": 8, "recovery": 80000, "cash": 720000, "remaining": 20000})
		self.t.certify_invoice(first)
		cert = frappe.db.get_value("Contract Certification", {"invoice": first, "state": "Signed"}, "matching_json")
		self.assertEqual(records.loads(cert)["advance_recovery"]["recovery"], 80000, "the signer's recovery is frozen with the certification")
		self.t.pay(first, "ADV-BANK-2")
		pos = payment.invoice_position(self.case, first)
		self.assertEqual({k: pos[k] for k in ("certified", "recorded", "cash_confirmed", "noncash", "advance_recovery", "outstanding")}, {"certified": 800000, "recorded": 720000, "cash_confirmed": 720000, "noncash": 80000, "advance_recovery": 80000, "outstanding": 0})
		self.assertEqual(frappe.db.get_value("Contract Invoice", first, "state"), "Paid", "cash 720,000 and the advance recovery 80,000 settle the 800,000")
		self.assertEqual(advance.position(self.case)["recovered"], 80000)
		self.goods(2)  # the last two units: KES 200,000
		second = self.t.claim("ADV-INV-2", 2)["invoice"]
		plan2 = advance.recovery_plan(self.case, frappe.get_doc("Contract Invoice", second))
		self.assertEqual({k: plan2[k] for k in ("recovery", "cash", "remaining")}, {"recovery": 20000, "cash": 180000, "remaining": 0}, "the advance is not recovered a second time")
		self.t.certify_invoice(second)
		self.t.pay(second, "ADV-BANK-3")
		cash = sum(flt(a) for a in frappe.get_all("Contract Settlement", filters={"contract_case": self.case, "state": "Confirmed"}, pluck="amount"))
		self.assertEqual(cash, 1000000, "100,000 + 720,000 + 180,000")
		self.assertEqual(advance.position(self.case), {"advance": row, "certified": 100000, "paid": 100000, "recovered": 100000, "outstanding": 0})
		self.assertEqual(payment.invoice_position(self.case, second)["noncash"], 20000)

	def test_an_invoice_before_the_advance_is_paid_recovers_nothing_and_a_late_one_cannot_recover_more_than_is_left(self):
		self.claim()
		self.goods(8)
		inv = self.t.claim("ADV-INV-0", 8)["invoice"]
		self.assertIsNone(advance.recovery_plan(self.case, frappe.get_doc("Contract Invoice", inv)), "no advance has been paid, so there is nothing to recover")

	def test_the_recovery_is_set_against_the_native_invoice_and_reduces_what_is_payable(self):
		self.paid_advance()
		self.goods(8)
		inv = self.t.claim("ADV-INV-1", 8)["invoice"]
		self.t.certify_invoice(inv)
		self.t.post_accounting(inv)
		native = frappe.db.get_value("Contract Invoice", inv, "native_invoice")
		row = frappe.db.get_value("Purchase Invoice", native, ["grand_total", "total_advance", "outstanding_amount", "docstatus"], as_dict=True)
		self.assertEqual((row.docstatus, row.grand_total, row.total_advance, row.outstanding_amount), (1, 800000, 80000, 720000))
		over = refusal(payment.save_finance_draft, self.case, invoice=inv, expected_version=self.t.version(), idempotency_key=self.t.key("o"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X", amount=800000)
		self.assertEqual((over.code, over.detail["available"]), ("CM_HOLD", 720000), "the cash payable is what is left after the recovery")
