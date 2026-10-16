# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FU-CM-119 (the Project Owner's decision of 16 October 2026): "Finance should be able to record an early liability and prepare a credit adjustment from the relevant claim. ERPNext remains the accounting owner.
Recording liability does not certify acceptance or release the payment hold."

When a corrected claim supports less than the liability Finance already posted, Finance used to raise the credit note somewhere else and come back to name it. Now the person who holds Finance preparation prepares it
from the claim: Contract Management asks ERPNext for a Draft credit note for exactly the shortfall, hands it to a different Finance person, and that person posts it natively. Nothing here writes the ledger; the
hold lifts when ERPNext reports the credit posted, and not before."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.native import adapter
from kentender_contracts.services import holds, payment, work
from kentender_contracts.tests import dead_end
from kentender_contracts.tests.test_cm_liability import LiabilityCase, refusal


class TestCreditPreparedFromTheClaim(LiabilityCase):
	def owed(self):
		"""Ten claimed and posted by Finance as a liability, then corrected to the eight accepted: 200,000 of the 1,000,000 is owed back."""
		first = self.claim("INV-01", 10)
		self.t.post_accounting(first["invoice"])
		second = self.correct(first)
		return second, self.row(second).native_invoice

	def prepare(self, second, who="josphat", key="prep"):
		return payment.prepare_liability_credit(self.case, invoice=second["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key(key), actor=self.p[who])

	def approve(self, second, who="beatrice", key="appr"):
		return payment.approve_liability_credit(self.case, invoice=second["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key(key), actor=self.p[who])

	def gap(self):
		return payment.liability_gap(self.case)[0]

	def liability_hold(self):
		return [h for h in holds.open_holds(self.case) if h.key.startswith("liability:")]

	def drafts(self, original):
		return frappe.get_all("Purchase Invoice", filters={"return_against": original, "docstatus": 0}, fields=["name", "grand_total", "is_return"])

	def test_finance_preparation_is_offered_prepare_credit_note_and_nobody_else_is(self):
		self.owed()
		board = router.board_for(self.case, self.p["josphat"], tab="Invoices")
		self.assertEqual((board["id"], board["p"]), ("D08-LR", "Prepare credit note"))
		self.assertEqual(board["actions"]["Prepare credit note"]["args"], {"kind": "credit", "invoice": self.gap()["successor"]})
		self.assertIn("Reconcile credit", board["s2"], "a credit raised elsewhere can still be named")
		self.assertIn("releases no payment hold", frappe.as_json(board))
		dead_end.assert_sound(self, board, "josphat")
		for who in ("charles", "david"):
			self.assertNotEqual((router.board_for(self.case, self.p[who], tab="Invoices") or {}).get("p"), "Prepare credit note", who)

	def test_preparing_makes_a_draft_credit_for_exactly_the_shortfall_and_certifies_and_releases_nothing(self):
		second, original = self.owed()
		out = self.prepare(second)
		draft = self.drafts(original)
		self.assertEqual([(d.name, d.grand_total, d.is_return) for d in draft], [(out["credit"], -200000, 1)])
		self.assertEqual(out["amount"], 200000)
		self.assertEqual(adapter.credit_against(original), 0, "a draft is not a credit")
		self.assertTrue(self.liability_hold(), "the hold stays until ERPNext reports the credit posted")
		self.assertFalse(frappe.db.exists("Contract Certification", {"invoice": second["invoice"], "state": "Signed"}))
		self.assertTrue(frappe.db.exists("Contract Event", {"contract_case": self.case, "event_type": "Credit note prepared"}))

	def test_it_goes_to_the_finance_approver_and_the_maker_waits(self):
		second, _original = self.owed()
		self.prepare(second)
		subject = f"credit invoice {self.gap()['successor_no']}"
		live = [(x["command"], x["title"], x["state"], x["holder"]) for x in work.live(self.case) if x["subject"] == subject]
		self.assertIn(("ApproveNativeFinanceRecord", "Review the credit note.", "actionable", self.p["beatrice"]), live)
		self.assertIn(("ApproveNativeFinanceRecord:waiting:credit", "Waiting for the Finance approver.", "waiting", self.p["josphat"]), live)
		self.assertTrue(frappe.db.exists("Notification Log", {"for_user": self.p["beatrice"], "subject": "Review the credit note."}), "the approver is told once the table names it")
		self.assertFalse(frappe.db.exists("Notification Log", {"for_user": self.p["josphat"], "subject": "Waiting for the Finance approver."}), "a waiting item is never an alert")

	def test_the_approver_and_the_maker_each_see_their_own_board(self):
		second, _original = self.owed()
		self.prepare(second)
		mine = router.board_for(self.case, self.p["josphat"], tab="Invoices")
		theirs = router.board_for(self.case, self.p["beatrice"], tab="Invoices")
		self.assertEqual((mine["id"], mine["p"]), ("D08-LW", ""))
		self.assertEqual((theirs["id"], theirs["p"], theirs["s2"]), ("D08-LA", "Approve credit note", ["Return credit note"]))
		for who, board in (("josphat", mine), ("beatrice", theirs)):
			dead_end.assert_sound(self, board, who)
		self.assertEqual(theirs["actions"]["Approve credit note"]["args"], {"kind": "credit", "invoice": self.gap()["successor"]})

	def test_preparing_twice_is_refused_and_a_replay_of_one_key_changes_nothing(self):
		second, original = self.owed()
		key = self.t.key("once")
		args = dict(invoice=second["invoice"], expected_version=self.t.version(), idempotency_key=key, actor=self.p["josphat"])
		first = payment.prepare_liability_credit(self.case, **args)
		again = payment.prepare_liability_credit(self.case, **args)
		self.assertEqual(again["credit"], first["credit"])
		self.assertEqual(refusal(self.prepare, second, key="twice").code, "CM_CHANGED")
		self.assertEqual(len(self.drafts(original)), 1)

	def test_only_finance_preparation_prepares_and_only_finance_approval_approves(self):
		second, original = self.owed()
		self.assertEqual(refusal(self.prepare, second, "charles").code, "CM_AUTHORITY")
		self.assertEqual(refusal(self.prepare, second, "david").code, "CM_AUTHORITY")
		self.prepare(second)
		self.assertEqual(refusal(self.approve, second, "charles").code, "CM_AUTHORITY")
		self.assertIn(refusal(self.approve, second, "josphat").code, ("CM_AUTHORITY", "CM_SEGREGATION"), "the person who prepared it does not approve it")
		self.assertEqual(len(self.drafts(original)), 1, "nothing was posted")

	def test_nothing_is_owed_until_a_claim_is_corrected_below_its_posted_liability(self):
		first = self.claim("INV-01", 10)
		self.t.post_accounting(first["invoice"])
		exc = refusal(payment.prepare_liability_credit, self.case, invoice=first["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("no"), actor=self.p["josphat"])
		self.assertEqual(exc.code, "CM_CHANGED")

	def test_approving_posts_the_credit_lifts_the_hold_and_the_corrected_claim_is_certified_and_paid_once(self):
		second, original = self.owed()
		self.prepare(second)
		out = self.approve(second)
		self.assertTrue(out["reconciled"])
		self.assertEqual(adapter.credit_against(original), 200000)
		self.assertEqual(adapter.posted(original) - adapter.credit_against(original), 800000)
		self.assertFalse(self.liability_hold())
		for who in ("josphat", "beatrice"):
			self.assertFalse([t for t in self.tasks(who) if t[0] in ("ReconcileInvoiceLiability", "ApproveNativeFinanceRecord")], f"{who} has nothing left to do for the credit")
		kinds = frappe.get_all("Contract Event", filters={"contract_case": self.case}, pluck="event_type")
		for expected in ("Credit note prepared", "Native credit received", "Credit note posted", "Liability reconciled"):
			self.assertIn(expected, kinds)
		self.t.certify_invoice(second["invoice"])
		self.t.pay(second["invoice"], "CRN-BANK-1")
		self.assertEqual(payment.settled_amount(second["invoice"]), 800000, "paid once, at what the corrected claim supports")

	def test_returning_it_discards_the_draft_tells_the_maker_why_and_a_new_one_can_be_prepared(self):
		second, original = self.owed()
		self.prepare(second)
		ask = lambda reason, who="beatrice": payment.return_liability_credit(self.case, invoice=second["invoice"], expected_version=self.t.version(), idempotency_key=self.t.key("ret"), actor=self.p[who], reason=reason)
		self.assertEqual(refusal(ask, "   ").code, "CM_INPUT")
		self.assertEqual(refusal(ask, "Wrong period.", "josphat").code, "CM_AUTHORITY", "the maker does not send their own work back")
		ask("The credit should carry the March posting date.")
		self.assertEqual(self.drafts(original), [], "the unposted draft is gone")
		self.assertTrue(frappe.db.exists("Notification Log", {"for_user": self.p["josphat"], "subject": ["like", "The credit note was returned: The credit should carry the March%"]}))
		self.assertFalse([t for t in self.tasks("beatrice") if t[0] == "ApproveNativeFinanceRecord"], "the approver's task ended with the return")
		self.assertTrue(self.liability_hold())
		self.prepare(second, key="again")
		self.assertEqual(len(self.drafts(original)), 1)
		self.assertTrue(self.approve(second)["reconciled"])

	def test_a_credit_already_posted_for_part_leaves_only_the_rest_to_prepare(self):
		second, original = self.owed()
		from kentender_contracts.tests import native_world as world

		world.credit_note(original, 1, "crn-part")  # Finance's own native credit of 100,000: the hook reads it, 100,000 is still needed
		self.assertEqual((self.gap()["credited"], self.gap()["reconciled"]), (100000, False))
		out = self.prepare(second)
		self.assertEqual(out["amount"], 100000)
		self.assertTrue(self.approve(second)["reconciled"])
		self.assertEqual(adapter.credit_against(original), 200000)

	def test_a_credit_that_erpnext_refuses_is_shown_in_plain_words_and_leaves_nothing_behind(self):
		from unittest import mock

		second, original = self.owed()
		with mock.patch.object(adapter, "prepare_credit", side_effect=frappe.ValidationError("Quantity must be a whole number.")):
			exc = refusal(self.prepare, second, key="refused")
		self.assertEqual(exc.code, "CM_RECONCILE")
		self.assertIn("whole number", exc.detail["reason"])
		self.assertEqual(self.drafts(original), [])
