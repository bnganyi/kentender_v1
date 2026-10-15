# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.9, 5.21, 7, 19.5 and boards D32, D32-H, D22, D22-P, D11, D11-B, D11-C, D38-P, D38, D38-R, D38-T (plan Phase 9; tracker CM8-901..909): final acceptance, completion, delivery of the
certificate, close-out and its correction.

Final acceptance is the Accounting Officer's own act where the issued terms ask for one, and the security-return clock starts from it and from nothing else. The completion certificate is the head of procurement's, and
its delivery to the contractor is a further evidenced fact that comes before the review the Accounting Officer closes. An unresolved completion defect stops both. Closing asks the funding owner once; a closed contract is
corrected only by a reasoned request and a successor decision."""

from __future__ import annotations

import frappe

from kentender_contracts.services import closeout, closure_correction, errors, final_acceptance, funding_closure, holds, issues, records, security_actions, warranty, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

ACCEPTED_ON = "2027-07-20 10:00:00"
FINAL_ON = "2028-07-28 08:30:00"
NOTICE_ON = "2028-07-10 09:00:00"


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class CompletionCase(ContractCase):
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
		tag = self.id().rsplit(".", 1)[-1][:24]
		self.t = tw.Thread(self.p, tag=tag, item=world.ITEM_PLAIN, award_case=f"CM-TEST-{tag}-FIN")
		self.case = self.t.active()
		self.t.appointed()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["julia"])
		self.units = tw.fresh_serials(10)
		arrival = self.t.arrive(self.units, received_at="2027-07-12 10:00:00")["arrival"]
		self.t.inspect(arrival, self.units)
		frappe.flags.kt_cm_clock = ACCEPTED_ON
		self.t.accept(arrival)
		frappe.flags.kt_cm_clock = FINAL_ON

	# -- the steps ---------------------------------------------------------------------------------------------------------------------
	def accept_finally(self, who="amina"):
		return final_acceptance.sign(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("final"), actor=self.p[who])

	def issue_certificate(self):
		return closeout.issue_completion_certificate(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("completion"), actor=self.p["charles"])

	def certificate(self):
		return closeout.completion_certificate(self.case)

	def confirm_delivery(self, **kw):
		values = {"delivered_on": str(frappe.utils.getdate(frappe.flags.kt_cm_clock)), "method": "Hand delivery to the supplier's office", "reference": "DISP-014", "evidence": [{"label": "Signed delivery note", "file": "x"}]}
		values.update(kw)
		return closeout.confirm_certificate_delivery(self.case, certificate=self.certificate().name, expected_version=self.t.version(), idempotency_key=self.t.key("delivered"), actor=self.p["charles"], **values)

	def completed(self):
		"""Final acceptance, the certificate and its delivery: the review is ready for the Accounting Officer."""
		self.accept_finally()
		self.issue_certificate()
		return self.confirm_delivery()

	def close(self):
		review = frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "state": "Awaiting signature"}, "name")
		return closeout.sign_closeout(self.case, closeout=review, expected_version=self.t.version(), idempotency_key=self.t.key("close"), actor=self.p["amina"])

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}

	def commands(self, who):
		return {c for c, _, _ in self.tasks(who)}

	def claim(self):
		return warranty.record_claim(self.case, unit=self.units[3], fault="Battery does not charge", notice_date="2028-07-10", remedy="Like-for-like replacement", expected_version=self.t.version(), idempotency_key=self.t.key("claim"), actor=self.p["julia"])


class TestFinalAcceptance(CompletionCase):
	def test_the_accounting_officer_is_asked_once_everything_is_accepted_and_the_head_is_not_yet(self):
		self.assertIn(("SignFinalContractAcceptance", "Review the final acceptance evidence.", "actionable"), self.tasks("amina"))
		self.assertNotIn("IssueCompletionCertificate", self.commands("charles"))
		self.assertIn("Final acceptance", [r["kind"] for r in closeout.remaining_obligations(self.case)])

	def test_the_evidence_is_read_from_the_records_and_names_the_units_and_the_end_of_their_warranty(self):
		found = final_acceptance.evidence(self.case)
		self.assertEqual((found["accepted"], found["defects"], found["warranty_ends"]), (10, [], ["2028-07-20"]))
		self.assertTrue(found["treatment"])

	def test_only_the_accounting_officer_signs_it_and_it_is_recorded_once(self):
		self.assertEqual(refusal(self.accept_finally, "charles").code, "CM_AUTHORITY")
		done = self.accept_finally()
		self.assertEqual(done["state"], "Signed")
		self.assertTrue(final_acceptance.signed(self.case))
		self.assertTrue(frappe.db.get_value("Contract Certificate", done["certificate"], "proof_reference"))
		again = self.accept_finally()
		self.assertTrue(again.get("already"))
		self.assertEqual(frappe.db.count("Contract Certificate", {"contract_case": self.case, "kind": "Final acceptance"}), 1)

	def test_signing_it_starts_the_head_s_completion_and_the_security_return_clock_from_that_instant(self):
		self.accept_finally()
		self.assertIn("IssueCompletionCertificate", self.commands("charles"))
		self.assertNotIn("SignFinalContractAcceptance", self.commands("amina"))
		found = security_actions.final_acceptance(self.case)
		self.assertEqual(str(found["on"]), "2028-07-28")

	def test_an_open_warranty_claim_blocks_it_names_the_unit_and_its_holder(self):
		frappe.flags.kt_cm_clock = NOTICE_ON
		self.claim()
		frappe.flags.kt_cm_clock = FINAL_ON
		found = final_acceptance.evidence(self.case)["defects"]
		self.assertEqual([d["what"] for d in found], [f"Unit {self.units[3]} still has an unresolved completion defect."])
		self.assertEqual(found[0]["holder"], self.p["julia"])
		exc = refusal(self.accept_finally)
		self.assertEqual(exc.code, "CM_CLOSURE")
		self.assertEqual(exc.detail["remaining"][0]["kind"], "Completion defect")
		self.assertIn("SignFinalContractAcceptance", {x["command"] for x in work.live(self.case) if x["holder"] == self.p["amina"] and x["state"] == "blocked"})
		self.assertEqual({h.key.split(":")[0] for h in holds.open_holds(self.case)}, {"warranty claim"})

	def test_resolving_the_claim_lifts_the_block_and_the_acceptance_proceeds(self):
		frappe.flags.kt_cm_clock = NOTICE_ON
		self.claim()
		frappe.flags.kt_cm_clock = FINAL_ON
		issues.close(self.case, issues.get(self.case, 1), "Supplier remedied the unit.", self.p["julia"])
		self.assertEqual(final_acceptance.evidence(self.case)["defects"], [])
		self.assertEqual(self.accept_finally()["state"], "Signed")

	def test_returning_it_sends_the_reason_to_the_head_and_it_comes_back_to_the_accounting_officer(self):
		self.assertEqual(refusal(closeout.return_review, self.case, stage="final acceptance", reason=" ", expected_version=self.t.version(), idempotency_key=self.t.key("r0"), actor=self.p["amina"]).code, "CM_INPUT")
		closeout.return_review(self.case, stage="final acceptance", reason="The second acceptance report lists the wrong store.", expected_version=self.t.version(), idempotency_key=self.t.key("r1"), actor=self.p["amina"])
		self.assertNotIn("SignFinalContractAcceptance", self.commands("amina"))
		self.assertIn(("PrepareContractCloseout", "Correct the final acceptance evidence and send it back.", "actionable"), self.tasks("charles"))
		closeout.prepare_closeout(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("again"), actor=self.p["charles"])
		self.assertIn("SignFinalContractAcceptance", self.commands("amina"))
		self.assertNotIn("PrepareContractCloseout", self.commands("charles"))

	def test_a_contract_whose_terms_ask_for_no_final_acceptance_goes_straight_to_the_head(self):
		frappe.flags.kt_cm_clock = tw.CLOCK  # a new award is received on the world's own day, inside its signing window
		other = tw.Thread(self.p, tag="plain" + self.id().rsplit(".", 1)[-1][:8], item=world.ITEM_PLAIN).active()
		frappe.flags.kt_cm_clock = FINAL_ON
		self.assertFalse(final_acceptance.required(other))
		self.assertFalse(final_acceptance.offer(other))
		self.assertTrue(final_acceptance.required(self.case))


class TestCertificateDeliveryAndClosure(CompletionCase):
	def test_signing_the_certificate_asks_for_its_delivery_and_makes_no_review_yet(self):
		self.accept_finally()
		self.issue_certificate()
		self.assertIn(("ConfirmCertificateDelivery", "Confirm certificate delivery.", "actionable"), self.tasks("charles"))
		self.assertIn("Certificate delivery", [r["kind"] for r in closeout.remaining_obligations(self.case)])
		self.assertEqual(frappe.db.count("Contract Closeout", {"contract_case": self.case}), 0)
		self.assertEqual(refusal(closeout.prepare_closeout, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("early"), actor=self.p["charles"]).code, "CM_CLOSURE")
		self.assertNotIn("SignContractCloseout", self.commands("amina"))

	def test_delivery_needs_the_day_the_way_and_the_proof_and_is_recorded_once(self):
		self.accept_finally()
		self.issue_certificate()
		exc = refusal(self.confirm_delivery, delivered_on="", method=" ", evidence=[])  # a blank date is not today
		self.assertEqual(exc.code, "CM_INPUT")
		self.assertEqual(set(exc.detail["fields"]), {"delivered_on", "method", "evidence"})
		self.assertEqual(refusal(self.confirm_delivery, delivered_on="2099-01-01").code, "CM_INPUT")
		out = self.confirm_delivery()
		self.assertTrue(out["closeout"])
		self.assertTrue(closeout.delivered(self.certificate()))
		self.assertEqual(closeout.delivery_of(self.certificate())["by"], self.p["charles"])
		self.assertTrue(self.confirm_delivery().get("already"))
		self.assertEqual(frappe.db.count("Contract Closeout", {"contract_case": self.case}), 1)
		self.assertIn("SignContractCloseout", self.commands("amina"))
		self.assertNotIn("ConfirmCertificateDelivery", self.commands("charles"))

	def test_only_the_head_confirms_delivery(self):
		self.accept_finally()
		self.issue_certificate()
		exc = refusal(closeout.confirm_certificate_delivery, self.case, certificate=self.certificate().name, delivered_on="2028-07-28", method="Post", evidence=[{"label": "Receipt", "file": "x"}], expected_version=self.t.version(),
			idempotency_key=self.t.key("stranger"), actor=self.p["julia"])
		self.assertEqual(exc.code, "CM_AUTHORITY")

	def test_the_review_states_the_final_acceptance_and_classifies_what_survives(self):
		self.completed()
		review = records.loads(frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "state": "Awaiting signature"}, "review_json"))
		self.assertEqual(review["final_acceptance"], "Recorded on 28 July 2028")
		self.assertEqual(review["remaining"], [])
		self.assertEqual([c["kind"] for c in review["classified"]], ["Publication"])
		self.assertTrue(all(c["owner"] and c["basis"] for c in review["classified"]))

	def test_a_running_warranty_survives_the_closure_with_its_owner_and_its_end(self):
		frappe.flags.kt_cm_clock = "2028-07-10 09:00:00"  # the warranty still runs
		self.completed()
		review = records.loads(frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "state": "Awaiting signature"}, "review_json"))
		warranty_row = next(c for c in review["classified"] if c["kind"] == "Warranty")
		self.assertEqual((warranty_row["owner"], warranty_row["due"]), (self.p["julia"], "2028-07-20"))

	def test_an_unclassified_surviving_duty_is_needs_review_and_prevents_the_closure(self):
		self.completed()
		from kentender_contracts.services import obligations

		obligations.open_obligation(self.case, kind="Other", rule="", trigger_event="A duty nobody classified", trigger_at=frappe.utils.now_datetime(), subject="mystery duty", owner=self.p["charles"], state="Needs review")
		exc = refusal(self.close)
		self.assertEqual(exc.code, "CM_CLOSURE")
		self.assertIn("Needs review", [r["kind"] for r in exc.detail["remaining"]])

	def test_a_claim_opened_after_the_review_blocks_the_close_out_and_names_the_claim(self):
		self.completed()
		frappe.flags.kt_cm_clock = NOTICE_ON
		self.claim()
		frappe.flags.kt_cm_clock = FINAL_ON
		exc = refusal(self.close)
		self.assertIn(exc.code, ("CM_CLOSURE", "CM_HOLD"))
		self.assertIn(("SignContractCloseout", "Review and sign the close-out.", "blocked"), self.tasks("amina"))

	def test_closing_asks_the_funding_owner_once_and_shows_what_it_answered(self):
		self.completed()
		closed = self.close()
		self.assertEqual(closed["state"], "Closed")
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Closed")
		self.assertEqual(funding_closure.status(self.case, closeout.CLOSURE_SUBJECT), "Acknowledged")
		self.assertEqual(closeout.funding_state(self.case), "Commitment closed by the funding owner")
		self.assertEqual(frappe.db.count("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Funding closure"}), 1)
		again = closeout.sign_closeout(self.case, closeout=closed["closeout"], expected_version=self.t.version(), idempotency_key=self.t.key("close-again"), actor=self.p["amina"])
		self.assertTrue(again.get("already"))

	def test_a_funding_owner_that_cannot_answer_leaves_the_contract_closed_and_the_closure_pending(self):
		self.completed()

		class Silent:
			def close(self, **kw):
				from kentender_core.services import contract_funding_contract as seam

				raise seam.Unavailable("owner offline")

			def recall(self, **kw):
				return None

		frappe.flags.kt_contract_funding_providers = [Silent()]
		self.addCleanup(lambda: setattr(frappe.flags, "kt_contract_funding_providers", None))
		self.close()
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Closed")
		self.assertEqual(closeout.funding_state(self.case), "Funding finalisation pending")


class TestCorrection(CompletionCase):
	def setUp(self):
		super().setUp()
		self.completed()
		self.close()

	def request(self, fact="Certificate delivery", submit=True, who="charles", correcting=0, reason="Delivery was recorded without proof."):
		return closure_correction.prepare(self.case, fact=fact, reason=reason, evidence_files=[{"label": "Delivery incident", "file": "x"}], submit=submit, correcting=correcting, expected_version=self.t.version(),
			idempotency_key=self.t.key("corr"), actor=self.p[who])

	def decide(self, decision, number=1, who="amina", reason="Decided.", survivors=None):
		return closure_correction.decide(self.case, correction=number, decision=decision, reason=reason, survivors=survivors, expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p[who])

	def test_a_draft_makes_no_task_and_a_submission_makes_the_exact_one(self):
		out = self.request(submit=False)
		self.assertEqual(closure_correction.get(self.case, 1).state, "Draft")
		self.assertNotIn("ConfirmContractClosure", self.commands("amina"))
		self.request(correcting=out["correction_no"])
		self.assertEqual(closure_correction.get(self.case, 1).state, "Submitted")
		self.assertIn(("ConfirmContractClosure", "Decide the correction.", "actionable"), self.tasks("amina"))

	def test_only_the_head_asks_and_a_request_needs_a_fact_a_reason_and_evidence(self):
		self.assertEqual(refusal(self.request, who="amina").code, "CM_AUTHORITY")
		exc = refusal(closure_correction.prepare, self.case, fact="Nothing", reason=" ", evidence_files=[], submit=True, expected_version=self.t.version(), idempotency_key=self.t.key("bad"), actor=self.p["charles"])
		self.assertEqual(set(exc.detail["fields"]), {"fact", "reason", "evidence"})

	def test_the_person_who_asked_cannot_decide_and_only_the_accounting_officer_does(self):
		self.request()
		self.assertEqual(refusal(self.decide, "Reopen", who="charles").code, "CM_AUTHORITY")
		self.assertEqual(refusal(self.decide, "Reopen", reason=" ").code, "CM_INPUT")

	def test_a_return_goes_back_to_the_head_who_corrects_and_submits_again(self):
		self.request()
		self.decide("Return", reason="Name the exact certificate.")
		self.assertEqual(closure_correction.get(self.case, 1).state, "Returned")
		self.assertIn("PrepareContractClosureCorrection", self.commands("charles"))
		self.assertNotIn("ConfirmContractClosure", self.commands("amina"))
		self.request(correcting=1, reason="Delivery of completion certificate 1 was recorded without proof.")
		self.assertEqual(closure_correction.get(self.case, 1).state, "Submitted")
		self.assertIn("ConfirmContractClosure", self.commands("amina"))

	def test_a_required_completion_fact_cannot_be_kept_closed(self):
		self.request()
		exc = refusal(self.decide, "Keep", survivors=[{"kind": "Delivery", "ref": "C1", "owner": self.p["charles"], "due": "on proof", "basis": "Because"}])
		self.assertEqual(exc.code, "CM_RECONCILE")
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Closed")

	def test_another_fact_may_be_kept_closed_only_with_named_surviving_work(self):
		self.request(fact="Other completion fact", reason="A snag list item was missed.")
		self.assertEqual(refusal(self.decide, "Keep", survivors=[]).code, "CM_INPUT")
		self.decide("Keep", survivors=[{"kind": "Snag item", "ref": "SN-1", "owner": self.p["julia"], "due": "On the supplier's visit", "basis": "Clause 12 snag period"}])
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Closed")
		row = frappe.get_doc("Contract Obligation", {"contract_case": self.case, "kind": "Other", "state": "Open"})
		self.assertEqual((row.owner_user, row.subject), (self.p["julia"], "surviving snag item SN-1"))

	def test_reopening_keeps_the_closure_restores_activity_and_asks_for_the_delivery_again(self):
		self.request()
		self.decide("Reopen", reason="Required completion evidence was not established.")
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Active")
		self.assertEqual(frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "version_no": 1}, "state"), "Closed")
		self.assertEqual(closure_correction.get(self.case, 1).state, "Reopened")
		self.assertFalse(closeout.delivered(self.certificate()))
		self.assertIn("ConfirmCertificateDelivery", self.commands("charles"))
		self.assertEqual(frappe.db.count("Contract Obligation", {"contract_case": self.case, "kind": "Publication", "state": ["!=", "Superseded"]}), 1, "nothing about legal dates was restored")

	def test_the_corrected_delivery_makes_a_new_review_and_the_second_closure_asks_the_owner_nothing_more(self):
		self.request()
		self.decide("Reopen")
		self.confirm_delivery(reference="DISP-015")
		self.assertEqual(frappe.db.count("Contract Closeout", {"contract_case": self.case}), 2)
		again = self.close()
		self.assertEqual(again["state"], "Closed")
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Closed")
		self.assertEqual(frappe.db.count("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Funding closure"}), 1)
		self.assertEqual(closeout.delivery_of(self.certificate())["previous"][0]["withdrawn"]["correction"], closure_correction.get(self.case, 1).name)

	def test_a_reopened_final_acceptance_is_asked_for_again(self):
		self.request(fact="Final acceptance", reason="The acceptance was signed before a defect was reported.")
		self.decide("Reopen")
		self.assertIn("SignFinalContractAcceptance", self.commands("amina"))
		self.assertEqual(frappe.db.get_value("Contract Certificate", {"contract_case": self.case, "kind": "Final acceptance"}, "state"), "Superseded")

	def test_a_terminated_contract_is_never_reopened_through_a_correction(self):
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Terminated")
		exc = refusal(self.request)
		self.assertEqual(exc.code, "CM_CHANGED")
		self.assertIn("termination", exc.detail["reason"])
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Closed")

	def test_a_contract_that_is_not_closed_cannot_be_corrected(self):
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Active")
		self.assertEqual(refusal(self.request).code, "CM_CHANGED")
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Closed")

	def test_one_correction_at_a_time(self):
		self.request()
		exc = refusal(self.request, fact="Final acceptance")
		self.assertEqual(exc.code, "CM_CHANGED")
