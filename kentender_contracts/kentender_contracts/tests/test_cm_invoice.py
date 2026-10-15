# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.8, 5.19, boards D18, D08 (plan Phase 7; tracker CM8-701; CM-AC-11, 12): the supplier's claim.

A claim is recorded once, with the instant it was received, and compared with what the contract supports: the price, the tax treatment, the accepted unclaimed quantity, earlier claims, the receipt that carries
the units and the amount still open. Each difference is recorded with its kind, its reason and who must act on it. A correction is a linked successor: the original is kept and its receipt time survives. An
apparent duplicate is held for Finance review, never refused or deleted, and a duplicate that Finance sets aside keeps no entitlement."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today

from kentender_contracts.services import errors, payment, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class InvoiceCase(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p = self.people
		self.t = tw.Thread(self.p, tag="INV")
		self.case = self.t.active()
		self.t.appointed()
		self.units = tw.fresh_serials(10)
		self.arrival = self.t.arrive(self.units)["arrival"]
		self.t.inspect(self.arrival, self.units, bad=tuple(self.units[8:]))
		self.t.accept(self.arrival)  # eight accepted, two rejected

	def claim(self, reference, quantity=8, *, date=None, rate=None, tax_included=None, successor_of="", reason=""):
		line = {"line_id": "L1", "quantity": quantity, "rate": rate}
		if tax_included is not None:
			line["tax_included"] = tax_included
		return payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("claim"), actor=self.p["david"], claim_reference=reference, invoice_date=date or today(),
			lines=[line], successor_of=successor_of, reason=reason)

	def row(self, out):
		return frappe.get_doc("Contract Invoice", out["invoice"])

	def findings(self, out):
		return records.loads(self.row(out).matching_json)["findings"]

	def tasks(self, who, state=("actionable", "blocked", "waiting")):
		return {(x["command"].split(":")[0], x["title"]) for x in work.live(self.case) if x["holder"] == self.p[who] and x["state"] in state}


class TestMatching(InvoiceCase):
	def test_a_claim_of_what_was_accepted_is_submitted_with_no_finding(self):
		out = self.claim("INV-OK")
		row = self.row(out)
		self.assertEqual((row.state, row.claimed_amount, self.findings(out)), ("Submitted", 800000, []))

	def test_a_quantity_difference_is_held_with_its_reason_and_the_head_of_procurement_to_act(self):
		out = self.claim("INV-QTY", 10)
		self.assertEqual(self.row(out).state, "Held")
		self.assertEqual(self.findings(out), [{"kind": "Quantity", "reason": "10 claimed but only 8 accepted and unclaimed.", "holder": "Head of procurement function", "line_id": "L1"}])
		self.assertIn(("RequestInvoiceCorrection", "Review the invoice: it does not match what the contract supports."), self.tasks("charles"))

	def test_a_price_difference_and_a_tax_difference_are_each_named(self):
		out = self.claim("INV-PRICE", rate=110000, tax_included=0)
		kinds = {f["kind"]: f for f in self.findings(out)}
		self.assertEqual(sorted(kinds), ["Price", "Tax"])
		self.assertIn("The price 110,000.00 differs from the contract price 100,000.00.", kinds["Price"]["reason"])
		self.assertIn("exclusive of tax", kinds["Tax"]["reason"])
		self.assertEqual({f["holder"] for f in self.findings(out)}, {"Head of procurement function"})

	def test_a_claim_over_the_amount_still_open_names_the_remaining_amount(self):
		out = self.claim("INV-OVER", 8, rate=150000)
		self.assertIn("Remaining amount", [f["kind"] for f in self.findings(out)])
		self.assertTrue(records.loads(self.row(out).matching_json)["exceeds_remaining"])

	def test_an_earlier_claim_holds_its_quantity_so_the_next_sees_only_what_is_left(self):
		self.claim("INV-A", 5)
		out = self.claim("INV-B", 5, date=add_days(today(), -1))
		self.assertEqual([f["reason"] for f in self.findings(out)], ["5 claimed but only 3 accepted and unclaimed."])


class TestCorrection(InvoiceCase):
	def test_a_correction_is_a_linked_successor_and_the_original_receipt_time_survives(self):
		frappe.flags.kt_cm_clock = "2027-07-21 08:05:00"
		first = self.claim("INV-01", 10)
		frappe.flags.kt_cm_clock = "2027-07-21 10:00:00"
		payment.request_invoice_correction(self.case, invoice=first["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p["charles"], reason="Please correct the invoice to match the eight accepted laptops.")
		second = self.claim("INV-01-C", 8, successor_of=first["invoice"], reason="Corrected to the eight accepted laptops.")
		original, successor = self.row(first), self.row(second)
		self.assertEqual((original.state, successor.state, successor.successor_of), ("Superseded", "Submitted", original.name))
		self.assertEqual((str(original.received_at), str(successor.received_at)), ("2027-07-21 08:05:00", "2027-07-21 10:00:00"))
		self.assertEqual(str(successor.first_received_at), "2027-07-21 08:05:00", "the clock of the claim runs from the first receipt, never from the correction")
		self.assertEqual(str(original.first_received_at), "2027-07-21 08:05:00")
		self.assertEqual(records.loads(original.lines_json)[0]["quantity"], 10, "the original claim is kept as it was")

	def test_a_correction_of_a_claim_that_is_not_held_is_refused(self):
		ok = self.claim("INV-OK")
		self.assertEqual(refusal(self.claim, "INV-OK2", 8, successor_of=ok["invoice"]).code, "CM_CHANGED")


class TestDuplicate(InvoiceCase):
	def test_the_same_invoice_number_is_held_for_finance_review_not_refused_and_the_head_of_procurement_is_not_asked(self):
		first = self.claim("INV-DUP", 4)
		second = self.claim("inv-dup", 4, date=add_days(today(), -1))
		row = self.row(second)
		self.assertEqual((row.state, records.loads(row.matching_json)["duplicate_of"]), ("Held", first["invoice"]))
		self.assertEqual([f["kind"] for f in self.findings(second)][:1], ["Duplicate"])
		self.assertEqual(self.findings(second)[0]["holder"], "Finance")
		self.assertIn(("ResolveInvoiceDuplicate", "Review the invoice: it appears to repeat another."), self.tasks("josphat"))
		self.assertFalse([1 for c, _t in self.tasks("charles") if c == "RequestInvoiceCorrection"])

	def test_the_same_lines_on_the_same_date_are_an_apparent_duplicate_and_another_day_is_not(self):
		self.claim("INV-ONE", 2)
		same_day = self.claim("INV-TWO", 2)
		other_day = self.claim("INV-THREE", 2, date=add_days(today(), -2))
		self.assertTrue(records.loads(self.row(same_day).matching_json)["duplicate_of"])
		self.assertEqual((self.row(other_day).state, records.loads(self.row(other_day).matching_json)["duplicate_of"]), ("Submitted", ""))

	def test_finance_sets_a_duplicate_aside_and_it_keeps_no_entitlement_and_is_not_deleted(self):
		first = self.claim("INV-DUP", 4)
		second = self.claim("INV-DUP", 4, date=add_days(today(), -1))
		out = payment.resolve_duplicate(self.case, invoice=second["invoice"], disposition="Duplicate", reason="Same supplier invoice sent twice.", expected_version=self.t.version(), idempotency_key=self.t.key("res"), actor=self.p["josphat"])
		self.assertEqual(self.row(second).state, "Set aside")
		self.assertTrue(frappe.db.exists("Contract Invoice", second["invoice"]))
		third = self.claim("INV-OTHER", 4, date=add_days(today(), -3))
		self.assertEqual(self.row(third).state, "Submitted", "what the set-aside copy held is open again")
		self.assertFalse(self.tasks("josphat", ("actionable",)) & {("ResolveInvoiceDuplicate", "Review the invoice: it appears to repeat another.")})

	def test_finance_clears_a_claim_that_is_not_a_duplicate_and_it_goes_on_to_certification(self):
		self.claim("INV-ONE", 4)
		second = self.claim("INV-ONE", 4, date=add_days(today(), -1))
		payment.resolve_duplicate(self.case, invoice=second["invoice"], disposition="Not a duplicate", reason="A second delivery's invoice with a reused number.", expected_version=self.t.version(), idempotency_key=self.t.key("res"), actor=self.p["josphat"])
		row = self.row(second)
		self.assertEqual((row.state, bool(row.native_invoice)), ("Submitted", True))
		self.assertIn(("SignContractCertification", "Review the invoice and sign the certification."), self.tasks("charles"))

	def test_only_finance_resolves_it_and_only_a_held_duplicate_and_with_a_reason(self):
		self.claim("INV-DUP", 4)
		second = self.claim("INV-DUP", 4, date=add_days(today(), -1))
		self.assertEqual(refusal(payment.resolve_duplicate, self.case, invoice=second["invoice"], disposition="Duplicate", reason="x", expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["charles"]).code, "CM_AUTHORITY")
		self.assertIn("reason", refusal(payment.resolve_duplicate, self.case, invoice=second["invoice"], disposition="Duplicate", reason=" ", expected_version=self.t.version(), idempotency_key=self.t.key("b"), actor=self.p["josphat"]).fields)
		plain = self.claim("INV-PLAIN", 4, date=add_days(today(), -4))
		self.assertEqual(refusal(payment.resolve_duplicate, self.case, invoice=plain["invoice"], disposition="Duplicate", reason="x", expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["josphat"]).code, "CM_CHANGED")
