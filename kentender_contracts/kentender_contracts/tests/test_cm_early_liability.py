# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FU-CM-93 (the Project Owner's decision of 16 October 2026): "Yes, from inside CM. Finance should be able to record an early liability ... from the relevant claim. ERPNext remains the accounting owner. Recording
liability does not certify acceptance or release the payment hold."

The services and the native proof already existed (test_cm_liability); what was missing was the way in. A person who holds Finance preparation is offered **Record liability** on a claim that has its native draft
and is not yet certified; it opens the accounting screen for that claim, and nobody else is offered it."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import errors, payment
from kentender_contracts.tests import dead_end
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests.test_cm_liability import LiabilityCase


class TestRecordLiabilityFromTheClaim(LiabilityCase):
	def held(self):
		"""Ten claimed, eight accepted: the claim is held for review with its native draft."""
		out = self.claim("INV-01", 10)
		self.assertEqual(self.row(out).state, "Held")
		return out

	def invoices(self, who: str) -> dict:
		return router.board_for(self.case, self.p[who], tab="Invoices")

	def test_finance_preparation_is_offered_record_liability_on_a_held_claim_and_nobody_else_is(self):
		self.held()
		board = self.invoices("josphat")
		self.assertIn("Record liability", board["s2"])
		self.assertEqual(board["actions"]["Record liability"]["do"], "route")
		for who in ("charles", "david", "beatrice", "naomi", "daniel"):
			self.assertNotIn("Record liability", self.invoices(who).get("s2", []), f"{who} is not offered it")

	def test_it_opens_the_accounting_screen_for_that_claim_with_its_own_next_step(self):
		out = self.held()
		number = self.row(out).invoice_no
		board = router.board_for(self.case, self.p["josphat"], tab="Invoices", subject=("record-liability", str(number)))
		self.assertEqual((board["id"], board["p"]), ("D33", "Submit invoice for approval"))
		self.assertEqual(board["next"]["k"], "turn")
		self.assertIn("payment stays held", board["next"]["h"])
		dead_end.assert_sound(self, board, "josphat")
		for who in ("charles", "david"):  # the head of procurement is not Finance, nor is the supplier: the route does not open the accounting screen for them
			other = router.board_for(self.case, self.p[who], tab="Invoices", subject=("record-liability", str(number)))
			self.assertNotEqual((other or {}).get("id"), "D33", who)

	def test_recording_it_through_to_the_posting_certifies_nothing_and_leaves_payment_held(self):
		out = self.held()
		self.t.post_accounting(out["invoice"])
		row = self.row(out)
		self.assertEqual((row.state, row.accounting_state), ("Held", "Posted"))
		self.assertFalse(frappe.db.exists("Contract Certification", {"invoice": out["invoice"], "state": "Signed"}), "no certification was made")
		with self.assertRaises(errors.ContractError) as refused:  # nothing is payable before certification
			payment.save_finance_draft(self.case, invoice=out["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("pay"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="X")
		self.assertEqual(refused.exception.code, "CM_INVOICE")
		self.assertNotIn("Record liability", self.invoices("josphat").get("s2", []), "once posted there is nothing more to record")

	def test_a_claim_without_a_native_draft_offers_nothing_to_record(self):
		out = self.held()
		frappe.db.set_value("Contract Invoice", out["invoice"], "native_invoice", "")
		self.assertNotIn("Record liability", self.invoices("josphat").get("s2", []))
		with self.assertRaises(errors.ContractError):
			payment.save_accounting_invoice(self.case, invoice=out["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("no"), actor=self.p["josphat"], posting_date=frappe.utils.today(), payable_account="x",
				cost_centre="y", expense_account="z")
