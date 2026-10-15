# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.8, 5.12, 5.18, 5.19, boards D08-L, D33 (plan Phase 7; tracker CM8-701, CM8-703; CM-AC-46, 52; proof level L2 native): a liability Finance recognised before certification, and the
correction that follows it.

A disputed claim is still invoiced natively as a draft, so Finance holds the supplier's whole claim. Finance may post that liability (its own accounting policy) while payment stays held. When the claim is
corrected, a draft is discarded and regenerated; a posted liability stands as the one liability (a second draft would double it) and is brought down by a native credit before the corrected claim can be
certified or paid. Contract Management reads the credit; it never writes the ledger."""

from __future__ import annotations

from unittest import mock

import frappe
from frappe.utils import flt, today

from kentender_contracts.native import adapter
from kentender_contracts.services import errors, holds, payment, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class LiabilityCase(ContractCase):
	native = True
	item = world.ITEM_PLAIN  # a plain stock item: an asset item is not invoiced before it is received

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
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=self.item)
		self.case = self.t.active()
		self.t.appointed()
		self.units = tw.fresh_serials(10)
		self.arrival = self.t.arrive(self.units)["arrival"]
		self.t.inspect(self.arrival, self.units, bad=tuple(self.units[8:]))
		self.t.accept(self.arrival)  # eight accepted, two rejected

	def claim(self, reference, quantity, **kw):
		return payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("claim"), actor=self.p["david"], claim_reference=reference, invoice_date=today(),
			lines=[{"line_id": "L1", "quantity": quantity}], **kw)

	def row(self, out):
		return frappe.get_doc("Contract Invoice", out["invoice"])

	def correct(self, first, quantity=8):
		payment.request_invoice_correction(self.case, invoice=first["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p["charles"], reason="Please correct the invoice to match the eight accepted laptops.")
		return self.claim("INV-01-C", quantity, successor_of=first["invoice"], reason="Corrected to the eight accepted laptops.")

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestEarlyLiability(LiabilityCase):
	def test_a_disputed_claim_is_still_a_native_draft_made_from_the_order_and_not_from_a_receipt(self):
		first = self.claim("INV-01", 10)
		row = self.row(first)
		self.assertEqual(row.state, "Held")
		doc = frappe.get_doc("Purchase Invoice", row.native_invoice)
		self.assertEqual((doc.docstatus, doc.grand_total, doc.items[0].qty, bool(doc.items[0].purchase_receipt)), (0, 1000000, 10, False))
		self.assertFalse([1 for t in self.tasks("daniel") if t[0] == "RestoreContractOperation"], "a refused courtesy draft would not ask anyone to recover it")

	def test_finance_may_post_the_liability_while_the_claim_is_still_held_and_no_payment_can_follow(self):
		first = self.claim("INV-01", 10)
		self.t.post_accounting(first["invoice"])
		row = self.row(first)
		self.assertEqual((row.state, row.accounting_state, adapter.posted(row.native_invoice)), ("Held", "Posted", 1000000))
		exc = refusal(payment.save_finance_draft, self.case, invoice=first["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("pay"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X")
		self.assertEqual(exc.code, "CM_INVOICE", "nothing is payable before certification")
		self.assertEqual(frappe.db.get_value("Purchase Invoice", row.native_invoice, "cm_certified_amount") or 0, 0)


class TestCorrectionOfAClaim(LiabilityCase):
	def test_an_unposted_draft_is_discarded_and_the_corrected_claim_gets_its_own_from_the_receipt(self):
		first = self.claim("INV-01", 10)
		old = self.row(first).native_invoice
		old_identity = frappe.db.get_value("Purchase Invoice", old, "cm_operation_identity")
		second = self.correct(first)
		new = self.row(second)
		self.assertFalse(frappe.db.exists("Purchase Invoice", {"cm_operation_identity": old_identity}), "the superseded claim's draft is gone")
		self.assertFalse(frappe.db.exists("Contract Transaction Link", {"operation_identity": old_identity}))
		self.assertEqual(frappe.db.count("Purchase Invoice", {"supplier": world.SUPPLIER, "cm_operation_identity": ["like", f"{self.case}%"], "docstatus": 0}), 1)
		doc = frappe.get_doc("Purchase Invoice", new.native_invoice)
		self.assertEqual((doc.docstatus, doc.grand_total, bool(doc.items[0].purchase_receipt)), (0, 800000, True))
		self.assertTrue(frappe.db.exists("Contract Event", {"contract_case": self.case, "event_type": "Native draft discarded"}))

	def test_a_posted_liability_stands_as_the_one_liability_and_a_second_draft_is_not_made(self):
		first = self.claim("INV-01", 10)
		self.t.post_accounting(first["invoice"])
		original = self.row(first).native_invoice
		second = self.correct(first)
		new = self.row(second)
		self.assertEqual((new.state, new.native_invoice, new.accounting_state), ("Submitted", original, "Posted"), "the liability Finance posted is the corrected claim's liability too")
		self.assertEqual(frappe.db.count("Purchase Invoice", {"supplier": world.SUPPLIER, "cm_operation_identity": ["like", f"{self.case}%"], "docstatus": ["<", 2]}), 1, "never a payable of 1,800,000")
		self.assertEqual(frappe.db.get_value("Contract Invoice", first["invoice"], "state"), "Superseded")

	def test_the_corrected_claim_waits_for_the_native_credit_and_finance_is_asked_for_it(self):
		first = self.claim("INV-01", 10)
		self.t.post_accounting(first["invoice"])
		second = self.correct(first)
		gap = payment.liability_gap(self.case)
		self.assertEqual([(g["liability"], g["supported"], g["required"], g["credited"], g["reconciled"]) for g in gap], [(1000000, 800000, 200000, 0, False)])
		held = [h for h in holds.open_holds(self.case) if h.key.startswith("liability:")]
		self.assertEqual(len(held), 1)
		self.assertEqual((held[0].owner, sorted(held[0].blocks)), ("Finance", ["certify_invoice", "pay"]))
		self.assertIn(("ReconcileInvoiceLiability", "Reconcile the original liability: a native credit of 200,000.00 is needed.", "actionable"), self.tasks("josphat"))
		self.assertIn("SignContractCertification", {c for c, _t, state in self.tasks("charles") if state == "blocked"}, "the certification waits, and says why")
		exc = refusal(payment.sign_certification, self.case, invoice=second["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_HOLD")
		self.assertIn("native credit of 200,000.00", exc.reasons[0]["detail"]["reason"])

	def test_a_native_credit_lifts_the_hold_and_the_corrected_claim_is_certified_and_paid_800_000_once(self):
		first = self.claim("INV-01", 10)
		self.t.post_accounting(first["invoice"])
		second = self.correct(first)
		original = self.row(second).native_invoice
		world.credit_note(original, 2, "lia1")  # Finance's native credit note: the hook reads it
		gap = payment.liability_gap(self.case)[0]
		self.assertEqual((gap["credited"], gap["reconciled"]), (200000, True))
		self.assertEqual(adapter.posted(original) - adapter.credit_against(original), 800000, "liability 1,000,000 and credit 200,000 leave 800,000")
		self.assertFalse([h for h in holds.open_holds(self.case) if h.key.startswith("liability:")])
		self.assertFalse([t for t in self.tasks("josphat") if t[0] == "ReconcileInvoiceLiability"], "Finance's task is done")
		events = frappe.get_all("Contract Event", filters={"contract_case": self.case, "event_type": ["in", ["Native credit received", "Liability reconciled"]]}, pluck="event_type")
		self.assertEqual(sorted(events), ["Liability reconciled", "Native credit received"])
		self.t.certify_invoice(second["invoice"])
		self.assertEqual(flt(frappe.db.get_value("Purchase Invoice", original, "cm_certified_amount")), 800000)
		out = self.t.pay(second["invoice"], "LIA-BANK-1")
		self.assertEqual(frappe.db.get_value("Contract Invoice", second["invoice"], "state"), "Paid")
		self.assertEqual(payment.settled_amount(second["invoice"]), 800000)

	def test_a_part_credit_keeps_the_hold(self):
		first = self.claim("INV-01", 10)
		self.t.post_accounting(first["invoice"])
		second = self.correct(first)
		world.credit_note(self.row(second).native_invoice, 1, "lia2")
		gap = payment.liability_gap(self.case)[0]
		self.assertEqual((gap["credited"], gap["required"], gap["reconciled"]), (100000, 200000, False))
		self.assertTrue([h for h in holds.open_holds(self.case) if h.key.startswith("liability:")])

	def test_the_original_receipt_and_the_correction_are_both_kept_and_the_clock_runs_from_the_first(self):
		frappe.flags.kt_cm_clock = "2027-07-21 08:05:00"
		first = self.claim("INV-01", 10)
		frappe.flags.kt_cm_clock = "2027-07-21 10:00:00"
		second = self.correct(first)
		a, b = self.row(first), self.row(second)
		self.assertEqual((str(a.received_at), str(b.received_at), str(b.first_received_at)), ("2027-07-21 08:05:00", "2027-07-21 10:00:00", "2027-07-21 08:05:00"))
		self.assertEqual((a.claimed_amount, b.claimed_amount), (1000000, 800000))


class TestAssetClaim(LiabilityCase):
	item = ""  # the fixed-asset item

	def test_a_held_claim_for_assets_gets_no_draft_because_the_asset_is_made_on_receipt(self):
		out = self.claim("AST-01", 10)
		row = self.row(out)
		self.assertEqual((row.state, row.native_invoice), ("Held", None))
		self.assertFalse([t for t in self.tasks("daniel") if t[0] == "RestoreContractOperation"], "nothing was refused that anyone must recover")
		self.assertEqual(holds.open_holds(self.case), [], "and no failed operation is left holding the contract")


class TestNativeRefusals(LiabilityCase):
	def test_an_unresolved_accounting_setup_blocks_submission_and_names_the_owner(self):
		inv = self.claim("INV-OK", 8)
		self.t.certify_invoice(inv["invoice"])
		native = frappe.db.get_value("Contract Invoice", inv["invoice"], "native_invoice")
		payment.save_accounting_invoice(self.case, invoice=inv["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("ai"), actor=self.p["josphat"], posting_date=today(),
			payable_account=frappe.db.get_value("Company", world.COMPANY, "default_payable_account"), cost_centre=frappe.db.get_value("Company", world.COMPANY, "cost_center"),
			expense_account=frappe.db.get_value("Purchase Invoice Item", {"parent": native}, "expense_account"))
		with mock.patch.object(adapter, "accounting_setup_problems", return_value=[f"{world.ITEM_PLAIN}: there is no account for it."]):
			self.assertEqual(payment.accounting_setup(self.case, inv["invoice"]), [f"{world.ITEM_PLAIN}: there is no account for it."])
			exc = refusal(payment.submit_accounting_invoice, self.case, invoice=inv["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("as"), actor=self.p["josphat"])
		self.assertEqual(exc.code, "CM_RECONCILE")
		self.assertEqual((exc.detail["reason"], exc.detail["holder"]), ("The accounting setup needs review.", "Finance configuration owner"))
		self.assertEqual(self.row(inv).accounting_state, "Draft saved")

	def test_the_real_setup_of_the_test_company_has_no_problem(self):
		inv = self.claim("INV-OK", 8)
		self.assertEqual(payment.accounting_setup(self.case, inv["invoice"]), [])

	def test_a_native_refusal_comes_back_on_the_same_screen_in_plain_words(self):
		inv = self.claim("INV-OK", 8)
		self.t.certify_invoice(inv["invoice"])
		with mock.patch.object(adapter, "prepare_invoice", side_effect=frappe.ValidationError("<b>Account</b> Test Payable is disabled")):
			exc = refusal(payment.save_accounting_invoice, self.case, invoice=inv["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("ai"), actor=self.p["josphat"], posting_date=today(),
				payable_account="x", cost_centre="y", expense_account="z")
		self.assertEqual((exc.code, exc.detail["native"], exc.detail["holder"]), ("CM_RECONCILE", "Account Test Payable is disabled", "Finance configuration owner"))
