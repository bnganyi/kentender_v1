# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 10 boards D32 (H), D22 (P), D11 (B, C), D38 (P, R, T) (plan Phase 9; tracker CM8-901..909): the screen each person gets at each step of final acceptance, completion, the certificate's
delivery, the close-out and a correction of it.

The server builds each board for the viewer at their step; with `CM_CAPTURE_BOARDS=1` each is written as a fixture for the structural fidelity gate."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D, long_date, short_date  # noqa: F401
import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import closeout, closure_correction, final_acceptance, people, warranty
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

EVIDENCE = [{"label": "Delivery incident", "file": "/private/files/delivery-incident.pdf"}]


class CompletionBoards(ContractCase):
	native = True
	#: how the test's award is named: "-FIN" makes the issued terms require the Accounting Officer's final acceptance
	SUFFIX = "-FIN"
	#: the test that needs the award publication left open, so that the closing review lists a surviving obligation (the head records it early everywhere else: FU-CM-108)
	PUBLICATION_OPEN = ("test_the_accounting_officer_reviews_the_final_acceptance_and_the_head_completes_it",)

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
		tag = self.id().rsplit(".", 1)[-1][:24]
		self.t = tw.Thread(self.p, tag=tag, item=world.ITEM_PLAIN, award_case=f"CM-TEST-{tag}{self.SUFFIX}")
		self.case = self.t.active(publication_open=self._testMethodName in self.PUBLICATION_OPEN)
		if self._testMethodName in self.PUBLICATION_OPEN:  # the obligation stays open and survives the close-out; the head's own task is set aside, or it would be the head's only task once the contract is closed and lead the head's screen there
			from kentender_contracts.services import work

			work.finish(self.case, command="RecordContractAwardPublication", state="Superseded", actor=self.p["charles"])
		self.t.appointed()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["julia"])
		self.units = tw.fresh_serials(10)
		arrival = self.t.arrive(self.units, received_at=D("2027-07-12 10:00:00"))["arrival"]
		self.t.inspect(arrival, self.units)
		frappe.flags.kt_cm_clock = D("2027-07-20 10:00:00")
		self.t.accept(arrival)
		frappe.flags.kt_cm_clock = D("2028-07-28 08:30:00")

	def screen(self, who, expected, capture=True, **kw):
		board = router.board_for(self.case, self.p[who], **kw)
		self.assertEqual(board["id"], expected, f"{who}: {board.get('title')} / {(board.get('next') or {}).get('h')}")
		return tw.capture(board) if capture else board

	def acceptance(self):
		return final_acceptance.sign(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("final"), actor=self.p["amina"])

	def certificate(self):
		return closeout.issue_completion_certificate(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("completion"), actor=self.p["charles"])

	def delivered(self):
		return closeout.confirm_certificate_delivery(self.case, certificate=closeout.completion_certificate(self.case).name, delivered_on=D("2028-07-28"), method="Hand delivery", reference="DISP-014",
			evidence=EVIDENCE, expected_version=self.t.version(), idempotency_key=self.t.key("delivered"), actor=self.p["charles"])

	def close(self):
		review = frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "state": "Awaiting signature"}, "name")
		return closeout.sign_closeout(self.case, closeout=review, expected_version=self.t.version(), idempotency_key=self.t.key("close"), actor=self.p["amina"])

	def claim(self):
		frappe.flags.kt_cm_clock = D("2028-07-10 09:00:00")
		warranty.record_claim(self.case, unit=self.units[3], fault="Battery does not charge", notice_date=D("2028-07-10"), remedy="Like-for-like replacement", expected_version=self.t.version(), idempotency_key=self.t.key("claim"),
			actor=self.p["julia"])
		frappe.flags.kt_cm_clock = D("2028-07-28 08:30:00")


class TestFinalAcceptanceToClosure(CompletionBoards):
	def test_the_accounting_officer_reviews_the_final_acceptance_and_the_head_completes_it(self):
		board = self.screen("amina", "D32", tab="Obligations")
		self.assertEqual((board["title"], board["p"], board["s2"], board["next"]["h"]), ("Record final acceptance", "Sign final acceptance", ["Return for correction"], "Review the final acceptance evidence."))
		facts = board["regions"][0]["b"][0]["items"]
		self.assertEqual(facts[0], ["Units accepted", "10"])
		self.assertEqual(facts[1], ["Initial 10 — warranty ended", long_date("2028-07-20")])
		self.assertEqual([facts[2][0], facts[2][1]], ["Unresolved completion defects", "None"])
		record = board["regions"][1]["b"]
		self.assertIn(f"I record final acceptance on {long_date('2028-07-28')} for the scope identified in the schedule under", record[0]["v"])
		self.assertEqual(record[1]["items"], [["Scope", "Whole contract — 10 laptop computers"], ["Remaining obligations", "None"]])
		self.assertEqual(board["actions"]["Sign final acceptance"]["command"], "SignFinalContractAcceptance")
		self.assertEqual(board["dialogs"]["return"]["args"], {"stage": "final acceptance"})
		self.acceptance()
		certificate = self.screen("charles", "D22", tab="Obligations")
		rows = certificate["regions"][0]["b"][0]["items"]
		self.assertIn(["Final acceptance", "Recorded"], rows)
		self.assertIn(["Unresolved defects", "None"], rows)
		self.assertIn(f"completed on {long_date('2028-07-28')}", certificate["regions"][0]["b"][1]["v"])
		self.certificate()
		delivery = self.screen("charles", "D22-P", tab="Obligations")
		self.assertEqual((delivery["p"], delivery["next"]["h"], delivery["s2"]), ("Confirm delivery", "Confirm certificate delivery.", ["View delivery status", "View certificate"]))
		self.assertEqual([f["l"] for f in delivery["regions"][0]["b"][1]["items"]], ["Delivered on", "How it was delivered", "Delivery reference", "Proof of delivery"])
		self.assertEqual(delivery["actions"]["Confirm delivery"]["command"], "ConfirmCertificateDelivery")
		self.delivered()
		review = self.screen("amina", "D11", tab="Obligations")
		self.assertEqual((review["p"], review["s2"]), ("Sign close-out", ["Return for correction"]))
		completion = review["regions"][0]["b"][1]["items"]
		self.assertEqual([completion[0], completion[3]], [["Warranty", "Ended with no unresolved claim"], ["Completion certificate", "Certificate 1"]])
		owner = frappe.db.get_value("Contract Obligation", {"contract_case": self.case, "kind": "Publication"}, "owner_user")
		self.assertEqual(review["regions"][1]["b"][1]["items"], [["Surviving obligations", f"Publication — {people.full_name(owner)}, Not confirmed — set by current directions"]])
		self.assertEqual(review["dialogs"]["return"]["args"], {"stage": "close-out"})
		self.close()
		closed = self.screen("amina", "D11-C", tab="Obligations")
		self.assertEqual((closed["st"], closed["next"]["k"], closed["p"], closed["s2"][:2]), ("Closed", "done", "", ["View close-out record", "View history"]))
		self.assertNotIn("Request close-out correction", closed["s2"], "the Accounting Officer decides a correction; the head of procurement asks for it")
		head = self.screen("charles", "D11-C", tab="Obligations", capture=False)
		self.assertIn("Request close-out correction", head["s2"])
		self.assertEqual(head["actions"]["Request close-out correction"]["route"], [self.case, "obligations", "request-correction"])
		self.assertEqual(closed["regions"][0]["b"][1]["items"][-1], ["Funding", "Commitment closed by the funding owner"])
		self.assertEqual(closed["regions"][1]["b"][1]["items"][0][0], "Surviving obligations")

	def test_an_open_claim_blocks_the_final_acceptance_and_names_the_unit(self):
		self.claim()
		board = self.screen("amina", "D32-H", tab="Obligations")
		self.assertEqual((board["p"], board["s2"], board["next"]["k"]), ("", [], "blk"))
		self.assertEqual(board["regions"][0]["b"][0]["items"][0], ["Warranty", "Warranty expired; timely claim remains open"])
		self.assertEqual([r[0] for r in board["regions"][0]["b"][0]["items"]], ["Warranty", "Remedy", "Defect"])
		self.assertIn(f"Battery does not charge — notified {short_date('2028-07-10')}", board["regions"][0]["b"][0]["items"][2][1])
		self.assertEqual([r["t"] for r in board["regions"]], ["Completion facts", "Evidence"])

	def test_a_claim_opened_after_the_review_blocks_the_close_out_review(self):
		self.acceptance()
		self.certificate()
		self.delivered()
		self.claim()
		board = self.screen("amina", "D11-B", tab="Obligations")
		self.assertEqual((board["p"], board["s2"], board["next"]["k"]), ("", [], "blk"))
		self.assertEqual(board["regions"][0]["b"][0]["items"][1], ["Open claim", f"Unit {self.units[3]}"])
		self.assertEqual(board["next"]["fixes"], ["View issue"])


class TestCompletionWithoutFinalAcceptance(CompletionBoards):
	SUFFIX = ""

	def test_the_certificate_says_the_goods_were_completed_when_they_were_accepted_not_when_the_agreement_began(self):
		# the issued terms require no final acceptance, so the evidence of completion is the last acceptance (20 July 2027 here); the agreement began on 2 July 2027, before anything was delivered
		frappe.flags.kt_cm_clock = D("2027-07-21 08:05:00")  # the claim, its certification and its payment, so nothing keeps the head from completing the contract
		invoice = self.t.claim("AFYA-1", 10)["invoice"]
		self.t.certify_invoice(invoice)
		self.t.pay(invoice, "B-1")
		frappe.flags.kt_cm_clock = D("2028-07-28 08:30:00")
		certificate = self.screen("charles", "D22", tab="Obligations", capture=False)
		statement = certificate["regions"][0]["b"][1]["v"]
		self.assertIn(f"completed on {long_date('2027-07-20')}", statement)
		self.assertNotIn(long_date("2027-07-02"), statement, "the agreement's own date is not the completion date")


class TestCorrection(CompletionBoards):
	def setUp(self):
		super().setUp()
		self.acceptance()
		self.certificate()
		self.delivered()
		self.close()

	def request(self, fact="Certificate delivery", submit=True, correcting=0):
		return closure_correction.prepare(self.case, fact=fact, reason="Required completion certificate delivery was recorded without evidence", evidence_files=EVIDENCE, submit=submit, correcting=correcting,
			expected_version=self.t.version(), idempotency_key=self.t.key("corr"), actor=self.p["charles"])

	def test_a_correction_from_the_request_to_the_reopened_contract(self):
		form = self.screen("charles", "D38-P", tab="Obligations", subject=("request-correction",))
		self.assertEqual((form["title"], form["p"], form["s2"], form["next"]["h"]), ("Request close-out correction", "Submit correction", ["Save draft", "Cancel"], "Explain the completion error."))
		self.assertEqual([f["l"] for f in form["regions"][1]["b"][0]["items"]], ["Completion fact that was wrong", "Reason", "Evidence", "Proposed disposition"])
		self.assertEqual(form["actions"]["Save draft"]["args"], {"submit": False})
		self.request()
		decision = self.screen("amina", "D38", tab="Obligations")
		self.assertEqual((decision["p"], decision["s2"], decision["next"]["h"]), ("Reopen contract", ["-Keep closed with surviving work", "Return for correction", "View closure"], "Decide the correction."))
		self.assertEqual(decision["regions"][0]["b"][1]["v"], "Keep closed with surviving work is unavailable: the bound completion rule requires this evidence.")
		self.assertEqual(decision["dialogs"]["reopen"]["args"], {"correction": 1})
		self.assertNotIn("keep", decision["dialogs"])
		closure_correction.decide(self.case, correction=1, decision="Reopen", reason="Required completion evidence was not established.", expected_version=self.t.version(), idempotency_key=self.t.key("reopen"), actor=self.p["amina"])
		reopened = self.screen("charles", "D38-R")
		self.assertEqual((reopened["st"], reopened["next"]["h"], reopened["p"]), ("Active", "Confirm certificate delivery.", "Confirm delivery"))
		self.assertEqual(reopened["regions"][0]["b"][0]["items"][:2], [["Closure 1", "Retained"], ["Reopening 1", reopened["regions"][0]["b"][0]["items"][1][1]]])
		self.assertEqual(reopened["regions"][0]["b"][0]["items"][2], ["Spending, stock and legal dates", "Unchanged"])

	def test_another_fact_may_be_kept_closed_and_the_dialog_asks_for_the_surviving_work(self):
		self.request(fact="Other completion fact")
		decision = self.screen("amina", "D38", tab="Obligations", capture=False)
		self.assertEqual(decision["s2"][0], "Keep closed with surviving work")
		self.assertEqual([f.get("l") for f in decision["dialogs"]["keep"]["b"][0]["items"]], ["Reason", "Surviving item", "Reference", "Owner", "Due event", "Term that lets it survive"])
		self.assertEqual(decision["dialogs"]["keep"]["b"][0]["items"][3]["t"], "pick")

	def test_a_terminated_contract_is_not_reopened_here(self):
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Terminated")
		board = self.screen("charles", "D38-T", tab="Obligations", subject=("request-correction",))
		self.assertEqual((board["p"], board["s2"], board["next"]), ("", ["View termination", "View settlement"], None))
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Closed")
