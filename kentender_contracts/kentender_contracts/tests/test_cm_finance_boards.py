# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 10 boards D08-L, D17-H, D28 (C, F, V), D29 (H, R), D33-U, D09 (T, AUD) (plan Phase 7; tracker CM8-706): the screens each person gets at each Finance and advance step.

The server builds each board for the viewer at their step; with `CM_CAPTURE_BOARDS=1` each is written as a fixture for the structural fidelity gate."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
from unittest import mock

import frappe
from frappe.utils import today

from kentender_contracts.boards import router
from kentender_contracts.native import adapter
from kentender_contracts.services import advance, holds, payment
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


class FinanceBoards(ContractCase):
	native = True
	item = ""
	advance = False

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
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=self.item, advance=self.advance)
		self.case = self.t.active()
		self.t.appointed()

	def screen(self, who, expected, **kw):
		board = router.board_for(self.case, self.p[who], **kw)
		self.assertEqual(board["id"], expected, f"{who}: {board.get('title')}")
		return tw.capture(board)

	def goods(self, count, bad=()):
		units = tw.fresh_serials(count)
		arrival = self.t.arrive(units)["arrival"]
		self.t.inspect(arrival, units, bad=tuple(units[i] for i in bad))
		self.t.accept(arrival)

	def instalment(self, inv, amount, reference):
		out = payment.save_finance_draft(self.case, invoice=inv, expected_version=self.t.version(), idempotency_key=self.t.key("d"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no=reference, amount=amount)
		payment.submit_finance_for_approval(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("s"), actor=self.p["josphat"])
		payment.approve_finance_record(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["beatrice"])
		return out["payment"]

	def settle(self, entry):
		return payment.record_finance_settlement(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("st"), actor=self.p["beatrice"], effective_date=D("2027-07-23"), evidence=f"Bank line {entry}")


class TestPartlyPaid(FinanceBoards):
	def test_a_partly_paid_invoice_its_next_payment_its_full_settlement_and_a_reversal(self):
		self.goods(8)
		inv = self.t.claim("D28-1", 8)["invoice"]
		self.t.certify_invoice(inv)
		self.t.post_accounting(inv)
		first = self.instalment(inv, 500000, "PART-1")
		self.settle(first)
		julia = self.screen("julia", "D28", tab="Invoices")
		facts = dict(julia["regions"][0]["b"][0]["items"])
		self.assertEqual((facts["Certified"], facts["Cash confirmed"], facts["Noncash adjustment"], facts["Outstanding"], facts["Invoice"]), ("KES 800,000", "KES 500,000", "KES 0", "KES 300,000", "Partly paid"))
		self.assertEqual(julia["regions"][1]["b"][0]["rows"][0][:3], [first, "KES 500,000", "!Confirmed"])
		maker = self.screen("josphat", "D09-F")
		self.assertEqual((maker["p"], maker["next"]["k"]), ("Submit payment for approval", "turn"))
		self.assertIn("remaining 300,000", maker["next"]["h"])
		second = self.instalment(inv, 300000, "PART-2")
		self.settle(second)
		done = self.screen("julia", "D28-C", tab="Invoices")
		self.assertEqual(dict(done["regions"][0]["b"][0]["items"])["Outstanding"], "KES 0")
		self.assertEqual(len(done["regions"][1]["b"][0]["rows"]), 2, "both settlements are kept")
		frappe.set_user("Administrator")
		frappe.get_doc("Payment Entry", second).cancel()
		frappe.db.commit()
		reversed_ = self.screen("julia", "D28-V", tab="Invoices")
		rows = reversed_["regions"][1]["b"][0]["rows"]
		self.assertEqual([r[2] for r in rows], ["!Confirmed", "!Reversed"])
		self.assertEqual(reversed_["regions"][1]["b"][1]["k"], "links")
		self.assertEqual(dict(reversed_["regions"][0]["b"][0]["items"])["Outstanding"], "KES 300,000")

	def test_the_technical_reader_and_the_auditor_see_the_follow_up_with_no_next_step_and_no_action(self):
		self.goods(8)
		inv = self.t.claim("D09-1", 8)["invoice"]
		self.t.certify_invoice(inv)
		for who, name in (("daniel", "D09-T"), ("naomi", "D09-AUD")):
			board = router.board_for(self.case, self.p[who], tab="Invoices")
			self.assertEqual((board["id"], board.get("next"), board.get("p", ""), board.get("s2", [])), ("D09", None, "", []), who)
			tw.capture(board, name)


class TestEarlyLiabilityBoards(FinanceBoards):
	item = world.ITEM_PLAIN

	def test_the_corrected_claim_waits_for_the_credit_on_d08_l_and_then_on_d08_c(self):
		self.goods(8, bad=())
		first = self.t.claim("D08L-1", 10)["invoice"]
		self.t.post_accounting(first)
		payment.request_invoice_correction(self.case, invoice=first, expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p["charles"], reason="Please correct the invoice to match the eight accepted laptops.")
		second = payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("fix"), actor=self.p["david"], claim_reference="D08L-1-R", invoice_date=today(), lines=[{"line_id": "L1", "quantity": 8}], successor_of=first)["invoice"]
		board = self.screen("charles", "D08-L")
		self.assertEqual((board["p"], board.get("s2", []), board["next"]["k"]), ("", [], "blk"))
		text = frappe.as_json(board["regions"])
		for needle in ("Original claim", "Corrected claim", "KES 1,000,000", "KES 200,000", "Not established", "KES 800,000"):
			self.assertIn(needle, text)
		world.credit_note(frappe.db.get_value("Contract Invoice", second, "native_invoice"), 2, "d08l")
		after = self.screen("charles", "D08-C")
		self.assertEqual(after["p"], "Sign certification")


class TestAccountingSetupAndHold(FinanceBoards):
	def test_an_unresolved_accounting_setup_blocks_submission_on_d33_u(self):
		self.goods(8)
		inv = self.t.claim("D33-1", 8)["invoice"]
		self.t.certify_invoice(inv)
		with mock.patch.object(adapter, "accounting_setup_problems", return_value=["CM-TEST-LAPTOP-FA: the asset category has no account for this company."]):
			board = self.screen("josphat", "D33-U")
		self.assertEqual((board["p"], board.get("s2", []), board["next"]["k"]), ("", [], "blk"))
		self.assertEqual(board["next"]["h"], "The accounting setup needs review.")

	def test_a_held_payment_shows_d17_h_to_the_approver(self):
		self.goods(8)
		inv = self.t.claim("D17H-1", 8)["invoice"]
		self.t.certify_invoice(inv)
		self.t.post_accounting(inv)
		out = payment.save_finance_draft(self.case, invoice=inv, expected_version=self.t.version(), idempotency_key=self.t.key("d"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="HOLD-1")
		payment.submit_finance_for_approval(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("s"), actor=self.p["josphat"])
		held = holds.Hold(key="TEST-HOLD", kind="Correction", reason="Certification missing", blocks=frozenset({"pay"}), owner="Head of procurement function", clearing="The certification is signed")
		with mock.patch.object(holds, "open_holds", return_value=[held]):
			board = self.screen("beatrice", "D17-H")
		self.assertEqual((board["p"], board.get("s2", []), board["next"]["h"]), ("", [], "This payment is on hold."))
		self.assertIn("Certification missing", frappe.as_json(board["regions"]))


class TestAdvanceBoards(FinanceBoards):
	advance = True

	def test_the_advance_review_waits_on_the_guarantee_then_is_signed_and_recovered_on_the_first_invoice(self):
		row = advance.prepare_advance(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("adv"), actor=self.p["david"], claim_reference="ADV-01", amount=100000)["advance"]
		held = self.screen("charles", "D29-H")
		self.assertEqual((held["p"], held.get("s2", []), held["next"]["k"], held["next"]["h"]), ("", ["View guarantee"], "blk", "The advance guarantee has not been verified."))
		record = self.screen("josphat", "D29-G")
		self.assertEqual(record["p"], "Save guarantee")
		sec = advance.record_guarantee(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("g"), actor=self.p["josphat"], issuer="Test Bank", beneficiary="Ministry of Health", reference="TEST-AG-01", amount=100000,
			issued_on=D("2027-06-01"), expires_on=D("2027-08-31"))["security"]
		verify = self.screen("charles", "D29-V")
		self.assertEqual(verify["p"], "Verify guarantee")
		advance.verify_guarantee(self.case, security=sec, expected_version=self.t.version(), idempotency_key=self.t.key("v"), actor=self.p["charles"], confirmation_reference="TEST-AG-CONF-01", received_on=D("2027-07-02"))
		review = self.screen("charles", "D29")
		self.assertEqual((review["p"], review["s2"]), ("Sign advance certification", ["View advance clause", "View guarantee"]))
		text = frappe.as_json(review["regions"])
		for needle in ("10% of KES 1,000,000 = KES 100,000", "KES 10,000 for each unit accepted and invoiced", "TEST-AG-01", "Verified", "ADV-01"):
			self.assertIn(needle, text)
		advance.sign_advance_certification(self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["charles"])
		pay = self.screen("josphat", "D09-F")
		self.assertEqual(pay["actions"]["Save draft"]["args"]["kind"], "advance")
		out = payment.save_advance_payment(self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("p"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="ADV-BANK")
		payment.submit_finance_for_approval(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("s"), actor=self.p["josphat"])
		approve = self.screen("beatrice", "D17")
		self.assertEqual(approve["actions"]["Approve payment"]["args"]["kind"], "payment")
		payment.approve_finance_record(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["beatrice"])
		payment.record_finance_settlement(self.case, payment=out["payment"], expected_version=self.t.version(), idempotency_key=self.t.key("st"), actor=self.p["beatrice"], effective_date=D("2027-07-05"), evidence="Bank line ADV")
		self.goods(8)
		inv = self.t.claim("ADV-INV-1", 8)["invoice"]
		recovery = self.screen("charles", "D29-R")
		self.assertEqual(recovery["p"], "Sign certification")
		text = frappe.as_json(recovery["regions"])
		for needle in ("KES 800,000", "KES 80,000", "KES 720,000", "KES 20,000", "KES 100,000"):
			self.assertIn(needle, text)

	def test_the_supplier_can_claim_the_advance_the_terms_provide_only_while_none_stands(self):
		board = router.board_for(self.case, self.p["david"], tab="Invoices")
		self.assertIn("Claim advance", board["s2"])
		self.assertEqual(board["dialogs"]["advance"]["cmd"] if "cmd" in board["dialogs"]["advance"] else board["dialogs"]["advance"].get("command"), "PrepareContractAdvance")
		advance.prepare_advance(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("adv"), actor=self.p["david"], claim_reference="ADV-01", amount=100000)
		self.assertNotIn("Claim advance", router.board_for(self.case, self.p["david"], tab="Invoices").get("s2", []))
