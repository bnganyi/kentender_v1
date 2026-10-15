# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 10 boards D27 (R, A), D14 (P), D34 (R, A, P, H, L, X) and the reviewer screens (plan Phase 8; tracker CM8-802): the screen each person gets at each step of a change.

The server builds each board for the viewer at their step; with `CM_CAPTURE_BOARDS=1` each is written as a fixture for the structural fidelity gate."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_contracts.boards import router
from kentender_contracts.rules import profile as profiles
from kentender_contracts.services import change
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

EVIDENCE = [{"label": "Supplier request 1", "file": "/private/files/request-1.pdf"}]


class ChangeBoards(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: (setattr(frappe.flags, "kt_cm_funding_fault", None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["carol"])
		self.t.appointed()

	def screen(self, who, expected, capture=True, **kw):
		board = router.board_for(self.case, self.p[who], **kw)
		self.assertEqual(board["id"], expected, f"{who}: {board.get('title')} / {(board.get('next') or {}).get('h')}")
		return tw.capture(board) if capture else board

	def ask(self, kind="Extension", request=None, who="carol"):
		request = request or ({"proposed_date": "2027-07-27"} if kind == "Extension" else {"quantities": {"L1": 11}})
		return change.request_change(self.case, kind=kind, request=request, reason="Supplier reports a seven-day shipment delay." if kind == "Extension" else "One additional user needs the same specified laptop",
			evidence=EVIDENCE, expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p[who])

	def appoint(self, kind):
		roster = dict(zip(change.REVIEW_KINDS[kind], (self.p["peter"], self.p["faith"], self.p["brian"]), strict=True))
		return change.appoint_reviewers(self.case, change=1, reference="AO/VAR/2027/001", reviewers=roster, expected_version=self.t.version(), idempotency_key=self.t.key("appoint"), actor=self.p["charles"])

	def reviewed(self, kind):
		for review, who in zip(change.REVIEW_KINDS[kind], ("peter", "faith", "brian"), strict=True):
			change.record_review(self.case, change=1, kind=review, recommendation="Approve date extension without price change" if kind == "Extension" else "Supported at the unchanged rate", declaration=change.NO_CONFLICT,
				reference="QTY-01" if review == "Funding confirmation" else "", expected_version=self.t.version(), idempotency_key=self.t.key("rec"), actor=self.p[who])
			change.sign_review(self.case, change=1, kind=review, expected_version=self.t.version(), idempotency_key=self.t.key("sig"), actor=self.p[who])

	def submit(self):
		return change.submit_for_decision(self.case, change=1, expected_version=self.t.version(), idempotency_key=self.t.key("submit"), actor=self.p["charles"])

	def approve(self):
		return change.decide(self.case, change=1, decision="Approve", reason="The documented grounds support the change.", expected_version=self.t.version(), idempotency_key=self.t.key("decide"), actor=self.p["amina"])

	def sign(self, party):
		return change.sign_amendment(self.case, change=1, party=party, expected_version=self.t.version(), idempotency_key=self.t.key(party), actor=self.p["mary" if party == "Supplier" else "amina"])


class TestExtension(ChangeBoards):
	def test_a_delivery_extension_from_the_request_to_the_amendment(self):
		julia = self.screen("carol", "D27", tab="Obligations", subject=("request-extension",))
		self.assertEqual((julia["title"], julia["p"], julia["next"]["h"]), ("Request delivery extension", "Request extension", "Explain the requested delivery date."))
		self.assertEqual([f["l"] for f in julia["regions"][0]["b"][0]["items"]], ["Current delivery", "Proposed date", "Reason", "Supplier request", "Amount and quantity"])
		before = router.board_for(self.case, self.p["carol"], tab="Obligations")
		self.assertEqual(before["id"], "D10")
		self.assertIn("Request delivery extension", before["s2"])
		self.ask()
		hop = self.screen("charles", "D27-N", capture=False)
		self.assertEqual((hop["p"], hop["title"]), ("Appoint reviewers", "Name the reviewers"))
		self.appoint("Extension")
		reviewer = self.screen("peter", "D27-V", capture=False)
		self.assertEqual(reviewer["p"], "Record review")
		change.record_review(self.case, change=1, kind="Technical review", recommendation="Approve date extension without price change", declaration=change.NO_CONFLICT, expected_version=self.t.version(),
			idempotency_key=self.t.key("rec"), actor=self.p["peter"])
		self.assertEqual(self.screen("peter", "D27-S", capture=False)["p"], "Sign review")
		change.sign_review(self.case, change=1, kind="Technical review", expected_version=self.t.version(), idempotency_key=self.t.key("sig"), actor=self.p["peter"])
		for review, who in zip(change.REVIEW_KINDS["Extension"][1:], ("faith", "brian"), strict=True):
			change.record_review(self.case, change=1, kind=review, recommendation="Approve date extension without price change", declaration=change.NO_CONFLICT, expected_version=self.t.version(), idempotency_key=self.t.key("rec"), actor=self.p[who])
			change.sign_review(self.case, change=1, kind=review, expected_version=self.t.version(), idempotency_key=self.t.key("sig"), actor=self.p[who])
		hop = self.screen("charles", "D27-R")
		self.assertEqual((hop["p"], hop["s2"], hop["next"]["h"]), ("Submit change for decision", ["Return for correction"], "Submit the supported request for decision."))
		table = hop["regions"][1]["b"][0]
		self.assertEqual([r[0] for r in table["rows"]], ["Peter Mugo", "Faith Atieno", "Brian Wafula"])
		self.assertEqual({r[2] for r in table["rows"]}, {"No conflict"})
		self.submit()
		ao = self.screen("amina", "D14")
		self.assertEqual((ao["p"], ao["s2"], ao["next"]["h"]), ("Approve extension", ["Decline", "Return for correction"], "Decide the requested delivery date."))
		self.assertEqual(sorted(ao["dialogs"]), ["approve", "decline", "return"])
		self.assertEqual(ao["regions"][0]["b"][0]["rows"][0], ["Delivery date", "20 July 2027", "27 July 2027"])
		self.approve()
		supplier = self.screen("mary", "D27-A")
		self.assertEqual((supplier["p"], supplier["s2"], supplier["subj"]), ("Sign amendment", ["Report a problem"], "Amendment 1"))
		waiting = self.screen("amina", "D14-P", tab="Obligations")
		self.assertEqual(waiting["next"]["k"], "wait")
		self.assertEqual(waiting["regions"][0]["b"][0]["items"][1], ["Operative delivery date", "20 July 2027 — amendment not yet effective"])
		self.sign("Supplier")
		self.assertEqual(self.screen("amina", "D27-A", capture=False)["p"], "Sign amendment")
		self.sign("Entity")
		after = router.board_for(self.case, self.p["carol"], tab="Obligations")
		register = next(r for r in after["regions"] if r["t"] == "Contract changes")
		self.assertEqual(register["b"][0]["rows"][0][:3], ["Change 1", "Delivery date to 27 Jul 2027", "Effective"])
		view = router.board_for(self.case, self.p["charles"], tab="Agreement", subject=("amendment", "1"))
		self.assertEqual(view["title"], "Amendment 1")


class TestQuantity(ChangeBoards):
	def test_a_quantity_change_from_the_request_to_the_effective_amendment_and_its_pending_update(self):
		julia = self.screen("carol", "D34", tab="Obligations", subject=("request-quantity",))
		self.assertEqual((julia["title"], julia["p"], julia["next"]["h"]), ("Request quantity change", "Request change", "Explain the additional quantity."))
		table = julia["regions"][0]["b"][0]
		self.assertEqual((table["rows"][0], table["inputs"]), (["Laptop computer", "10", "KES 100,000", "#11"], {"0,3": "quantity.L1"}))
		self.assertEqual(julia["regions"][0]["b"][1]["items"], [["Proposed total", "KES 1,100,000"], ["Cumulative quantity change", "10%"], ["Cumulative value change", "10%"]])
		blocked = self.screen("carol", "D34-X", tab="Obligations", subject=("request-quantity", "12"))
		self.assertEqual((blocked["next"]["k"], blocked["next"]["h"], blocked["p"]), ("blk", "Proposed quantity exceeds the applicable limit", ""))
		self.assertEqual(blocked["regions"][0]["b"][1]["items"][0], ["Applicable limit", "15% goods quantity"])
		self.assertEqual(blocked["regions"][0]["b"][0]["rows"][1], ["Total", "KES 1,000,000", "KES 1,200,000"])
		self.ask("Quantity")
		self.appoint("Quantity")
		self.reviewed("Quantity")
		hop = self.screen("charles", "D34-R")
		self.assertEqual((hop["p"], hop["next"]["h"]), ("Submit change for decision", "Submit the change for decision."))
		self.submit()
		ao = self.screen("amina", "D34-A")
		self.assertEqual((ao["p"], ao["s2"]), ("Approve change", ["Decline", "Return for correction"]))
		self.assertEqual(ao["dialogs"]["approve"]["p"], "Confirm decision")
		self.approve()
		supplier = self.screen("mary", "D34-P")
		self.assertEqual((supplier["p"], supplier["subj"], supplier["back"]), ("Sign amendment", "Amendment 1", "Back to my contracts"))
		frappe.flags.kt_cm_funding_fault = "fail"
		self.sign("Supplier")
		self.sign("Entity")
		pending = self.screen("amina", "D34-H", tab="Obligations")
		rows = dict(pending["regions"][0]["b"][0]["items"])
		self.assertEqual((rows["Operative quantity"], rows["Budget adjustment"], rows["Order update"], rows["New spending"]), ("11", "Pending", "Done", "Held for the changed quantity"))
		self.assertEqual(pending["next"]["k"], "wait")

	def test_an_early_total_increase_is_held_for_the_legal_question(self):
		verified = profiles.Profile("VERIFIED-NO-ANSWER", "A verified profile that has not answered LQ-02", profiles.VERIFIED, False, profiles.STATUTORY)
		with mock.patch.dict(profiles.PROFILES, {verified.id: verified}):
			frappe.db.set_value("Contract Case", self.case, "legal_profile", verified.id)
			self.ask("Quantity")
			self.appoint("Quantity")
			self.reviewed("Quantity")
			held = self.screen("charles", "D34-L")
			self.assertEqual((held["next"]["k"], held["next"]["h"], held["p"]), ("blk", "Change requires legal review", ""))
			self.assertEqual(held["next"]["fixes"], ["View rule", "View request", "Return for correction"])
			self.assertIn("within twelve months of signing", held["next"]["s2"])
