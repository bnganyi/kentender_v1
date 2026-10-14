# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.1 to 5.9, 14 (plan Phase 4, gate CM-G04; tracker CM8-413): the ordinary thread end to end, at the service level, with the ten-laptop story -- eight accepted and
two rejected, the two returned and replaced -- on real ERPNext (order, receipts, assets, invoices, payments through the controlled operation and the native workflow), the real core signing
facade with the Contract Management simulation provider, and the synthetic sources and funding owner.

Proof level: L2 for the native documents and the signing facade; **L1 for the source handoff and the funding owner**, which are re-run against the real providers at CM-G05. It proves the
ordinary thread and nothing about the rare branches, which later phases prove."""

from __future__ import annotations

import frappe
from frappe.model.workflow import apply_workflow

from kentender_contracts.native import payment_guard
from kentender_contracts.services import closeout, delivery, errors, formation, holds, next_steps, payment, position, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

CONTROLS = "Contract Test Environment Controls"


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestOrdinaryThread(ContractCase):
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
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		self.p = self.people

	def step_of(self, case, user):
		return next_steps.answer(work.view(case, user), headline_for=lambda lead: lead["title"])

	def test_the_ten_laptop_story_from_award_package_to_closed_contract(self):
		t = tw.Thread(self.p, tag="STORY")
		case = t.active()
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Active")
		t.appointed()
		first, second = tw.fresh_serials(10), tw.fresh_serials(2)

		# arrival, inspection, technical confirmation, acceptance: eight units meet, two do not
		arrival = t.arrive(first)["arrival"]
		self.assertEqual(self.step_of(case, self.p["peter"])["kind"], "your_turn")
		t.inspect(arrival, first, bad=tuple(first[8:]))
		accepted = t.accept(arrival)
		self.assertTrue(accepted["effective"])
		now = position.position(case)
		self.assertEqual((now["accepted"], now["lines"]["L1"]["rejected"], now["remaining"]), (8, 2, 2))
		receipt = delivery.posted_receipts(case)[0]
		self.assertEqual(sorted(frappe.get_all("Asset", filters={"purchase_receipt": receipt, "docstatus": ["<", 2]}, pluck="cm_unit_reference")), sorted(first[:8]))
		delivery.record_custody_return(case, expected_version=t.version(), idempotency_key=t.key("return"), actor=self.p["grace"], units=first[8:], evidence="Supplier gate pass GP-77")

		# the supplier claims the eight; matching supports it; procurement certifies; Finance prepares, a different person approves, an independent person confirms settlement
		held = t.claim("AFYA-0001", 9)
		self.assertEqual((held["state"], held["matching"]), ("Held", "Needs review"))
		held_row = frappe.get_doc("Contract Invoice", held["invoice"])
		self.assertIn("only 8 accepted and unclaimed", records.loads(held_row.matching_json)["rows"][0]["reasons"][0])
		self.assertEqual(refusal(payment.sign_certification, case, invoice=held["invoice"], expected_version=t.version(), idempotency_key=t.key("c"), actor=self.p["charles"]).code, "CM_INVOICE")
		payment.request_invoice_correction(case, invoice=held["invoice"], expected_version=t.version(), idempotency_key=t.key("rc"), actor=self.p["charles"], reason="Claim the eight accepted units only.")
		invoice = payment.submit_invoice(case, expected_version=t.version(), idempotency_key=t.key("claim"), actor=self.p["david"], claim_reference="AFYA-0001-R1", invoice_date=frappe.utils.today(),
			lines=[{"line_id": "L1", "quantity": 8}], successor_of=held["invoice"])
		self.assertEqual((invoice["state"], invoice["matching"]), ("Submitted", "Supported"))
		self.assertEqual(frappe.db.get_value("Contract Invoice", held["invoice"], "state"), "Superseded")
		self.assertTrue(frappe.db.get_value("Contract Invoice", held["invoice"], "received_at"), "the original receipt time is kept")
		native = frappe.db.get_value("Contract Invoice", invoice["invoice"], "native_invoice")
		self.assertEqual(frappe.db.get_value("Purchase Invoice", native, ["docstatus", "grand_total"]), (1, 800000.0))
		cert = t.certify_invoice(invoice["invoice"])
		self.assertEqual(cert["state"], "Certified")
		self.assertEqual(payment_guard.entitlement(native)["certified"], 800000.0)
		paid = t.pay(invoice["invoice"], "BANK-0001")
		self.assertEqual(paid["state"], "Paid")
		self.assertEqual(frappe.db.get_value("Purchase Invoice", native, "outstanding_amount"), 0)

		# the replacement units arrive, are accepted, claimed, certified and paid on the original entitlement
		self.assertEqual(position.position(case)["remaining"], 2)
		arrival2 = t.arrive(second, received_at="2027-07-16 09:00:00")["arrival"]
		t.inspect(arrival2, second)
		t.accept(arrival2)
		now = position.position(case)
		self.assertEqual((now["accepted"], now["remaining"], now["in_custody"]), (10, 0, 0))
		invoice2 = t.claim("AFYA-0002", 2)
		self.assertEqual(invoice2["state"], "Submitted")
		t.certify_invoice(invoice2["invoice"])
		t.pay(invoice2["invoice"], "BANK-0002")
		self.assertEqual([frappe.db.get_value("Contract Invoice", i, "state") for i in (invoice["invoice"], invoice2["invoice"])], ["Paid", "Paid"])
		self.assertEqual(sum(p["paid_amount"] for p in payment.payments(case) if p["docstatus"] == 1), 1_000_000.0, "this contract's payments, to the shilling")

		# completion: HOP is asked to issue the certificate; the Accounting Officer signs the close-out
		self.assertIn(("IssueCompletionCertificate", self.p["charles"]), {(x["command"], x["holder"]) for x in work.live(case)})
		self.assertEqual(refusal(closeout.prepare_closeout, case, expected_version=t.version(), idempotency_key=t.key("early"), actor=self.p["charles"]).code, "CM_CLOSURE")
		closeout.issue_completion_certificate(case, expected_version=t.version(), idempotency_key=t.key("completion"), actor=self.p["charles"])
		prepared = closeout.prepare_closeout(case, expected_version=t.version(), idempotency_key=t.key("prepare-closeout"), actor=self.p["charles"])
		review = records.loads(frappe.db.get_value("Contract Closeout", prepared["closeout"], "review_json"))
		self.assertEqual((review["claimed_total"], review["settled_total"], review["remaining"]), (1_000_000.0, 1_000_000.0, []))
		closed = closeout.sign_closeout(case, closeout=prepared["closeout"], expected_version=t.version(), idempotency_key=t.key("close"), actor=self.p["amina"])
		self.assertEqual(closed["state"], "Closed")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Closed")

		# the history is whole: every signature has a proof, every step an event, no hold or task is left dangling
		signatures = frappe.db.count("Contract Simulated Signature", {"fixture_namespace": "CM_TEST"})
		self.assertEqual(signatures, 2 + (1 + 3 + 1) + (1 + 3 + 1) + 1 + 1, "agreement x2; technical, report x3 and certification for each of the two deliveries; completion; close-out")
		self.assertEqual(holds.open_holds(case), [])
		live = [x for x in work.live(case) if x["holder"] in self.p.values() and x["state"] in ("actionable", "blocked")]
		self.assertEqual(live, [], "nothing is left for anyone to do on a closed contract")
		kinds = [e["type"] for e in __import__("kentender_contracts.services.events", fromlist=["history"]).history(case)]
		for expected in ("Award package received", "Sent for signature", "Agreement effective", "Arrival recorded", "Acceptance effective", "Receipt posted", "Certification signed", "Settlement confirmed", "Contract closed"):
			self.assertIn(expected, kinds)

	def test_the_finance_controls_hold_in_the_ordinary_thread(self):
		t = tw.Thread(self.p, tag="FIN")
		case = t.active()
		t.appointed()
		units = tw.fresh_serials(4)
		arrival = t.arrive(units)["arrival"]
		t.inspect(arrival, units)
		accepted = t.accept(arrival)
		signers = {s["user"] for s in records.loads(frappe.db.get_value("Contract Acceptance", accepted["acceptance"], "signers_json"))}
		inv = t.claim("FIN-1", 4)
		# an acceptance-report signer cannot certify the claim it supports
		frappe.db.set_value("Contract Acceptance", accepted["acceptance"], "signers_json", records.dumps([{**s, "user": self.p["charles"]} if s["user"] == self.p["brian"] else s for s in records.loads(frappe.db.get_value("Contract Acceptance", accepted["acceptance"], "signers_json"))]))
		self.assertEqual(refusal(payment.sign_certification, case, invoice=inv["invoice"], expected_version=t.version(), idempotency_key=t.key("c"), actor=self.p["charles"]).code, "CM_SEGREGATION")
		frappe.db.set_value("Contract Acceptance", accepted["acceptance"], "signers_json", records.dumps([{**s, "user": self.p["brian"]} if s["user"] == self.p["charles"] else s for s in records.loads(frappe.db.get_value("Contract Acceptance", accepted["acceptance"], "signers_json"))]))
		self.assertEqual(signers, {self.p["julia"], self.p["peter"], self.p["brian"]})
		self.assertEqual(refusal(payment.sign_certification, case, invoice=inv["invoice"], expected_version=t.version(), idempotency_key=t.key("c"), actor=self.p["brian"]).code, "CM_AUTHORITY")
		t.certify_invoice(inv["invoice"])
		native = frappe.db.get_value("Contract Invoice", inv["invoice"], "native_invoice")
		# nothing is payable before a Finance maker drafts it, and more than the certified amount is refused
		self.assertEqual(refusal(payment.save_finance_draft, case, invoice=inv["invoice"], expected_version=t.version(), idempotency_key=t.key("d"), actor=self.p["beatrice"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X").code, "CM_AUTHORITY")
		over = refusal(payment.save_finance_draft, case, invoice=inv["invoice"], expected_version=t.version(), idempotency_key=t.key("d"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X", amount=400001)
		self.assertEqual(over.code, "CM_HOLD")
		draft = payment.save_finance_draft(case, invoice=inv["invoice"], expected_version=t.version(), idempotency_key=t.key("d"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="FIN-BANK-1")
		self.assertEqual(refusal(payment.approve_finance_record, case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("a"), actor=self.p["beatrice"]).code, "CM_CHANGED", "not yet submitted")
		payment.submit_finance_for_approval(case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("s"), actor=self.p["josphat"])
		self.assertEqual(refusal(payment.approve_finance_record, case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("a"), actor=self.p["josphat"]).code, "CM_AUTHORITY", "the maker holds no approval responsibility")
		payment.return_finance_for_correction(case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("r"), actor=self.p["beatrice"], reason="Wrong reference.")
		self.assertEqual(frappe.db.get_value("Payment Entry", draft["payment"], "workflow_state"), "Draft")
		payment.submit_finance_for_approval(case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("s2"), actor=self.p["josphat"])
		# a payment made outside the controlled operation is refused by the native guard
		with self.assertRaises(Exception):
			apply_workflow(frappe.get_doc("Payment Entry", draft["payment"]), "Approve")
		payment.approve_finance_record(case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("a2"), actor=self.p["beatrice"])
		self.assertEqual(frappe.db.get_value("Payment Entry", draft["payment"], "docstatus"), 1)
		# a posted payment is not a settled one
		self.assertEqual(frappe.db.get_value("Contract Invoice", inv["invoice"], "state"), "Certified")
		self.assertIn("evidence", refusal(payment.record_finance_settlement, case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("st"), actor=self.p["beatrice"], effective_date="2027-07-20", evidence=" ").fields)
		settled = payment.record_finance_settlement(case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("st2"), actor=self.p["beatrice"], effective_date="2027-07-20", evidence="Bank line 44")
		self.assertEqual(settled["state"], "Paid")
		self.assertEqual(payment_guard.entitlement(native)["available"], 0)

	def test_a_contract_that_is_not_complete_cannot_be_closed(self):
		t = tw.Thread(self.p, tag="OPEN")
		case = t.active()
		exc = refusal(closeout.issue_completion_certificate, case, expected_version=t.version(), idempotency_key=t.key("x"), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_CLOSURE")
		self.assertEqual(exc.detail["remaining"][0]["kind"], "Delivery")
