# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The electronic tender-security journey (Project Owner, 10 October 2026):
submission, physical original, issuer verification and compliance are four
separate facts; an upload never means verified; an unavailable issuer leaves
verification pending; the mock issuer names itself."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import evidence, security_verification as sv, simulation
from kentender_procurement.bid_submission.tests.support import DAVID, key, pdf
from kentender_procurement.bid_submission.tests.test_security_and_price import ISSUER, REFERENCE, SecurityCase

SOURCE = "Test Issuer Service (simulation)"


class VerificationCase(SecurityCase):
	def setUp(self):
		super().setUp()
		simulation.reset_controls()
		self.addCleanup(simulation.reset_controls)

	def version(self):
		return frappe.db.get_value("Bid Workspace", self.bid, "record_version")

	def proof_handle(self):
		view = self.task("company")
		group = next(g for g in view["groups"] if any(f["label"] == "Form of Tender Security" for f in g["fields"]))
		return next(f["handle"] for f in group["fields"] if f["kind"] == "evidence")

	def add_proof(self):
		result = evidence.upload_bid_evidence(bid_reference=self.bid, handle=self.proof_handle(), filename="guarantee.pdf", content=pdf(), expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertTrue(result["ok"], result)

	def ready(self, reference=REFERENCE):
		self.answer_security(reference=reference)
		self.add_proof()

	def electronic(self):
		return self.task("company")["tender_security"]["electronic"]

	def submit(self, **kw):
		return sv.submit_tender_security(bid_reference=self.bid, expected_record_version=self.version(), idempotency_key=key(), user=DAVID, **kw)

	def check(self):
		return sv.check_tender_security_verification(bid_reference=self.bid, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)


class TestSubmissionIsExplicit(VerificationCase):
	def test_an_upload_or_a_filled_form_is_never_a_submission_or_a_verification(self):
		before = self.electronic()
		self.assertEqual((before["submission"]["state"], before["verification"]["state"], before["compliance"]["state"]), ("Not submitted", "Not requested", "Not yet assessed"))
		self.ready()
		after = self.electronic()
		self.assertEqual((after["submission"]["state"], after["verification"]["state"], after["submission"]["can_submit"]), ("Not submitted", "Not requested", True))
		self.assertIsNone(sv.row_for(self.bid))
		self.assertEqual(after["compliance"]["state"], "Meets")  # compliance is a comparison of the answers, not a verification

	def test_submitting_needs_every_detail_and_the_proof(self):
		self.answer_security()  # no proof yet
		refused = self.submit()
		self.assertEqual((refused["ok"], sorted(refused["errors"])), (False, ["proof"]))
		self.assertIsNone(sv.row_for(self.bid))

	def test_a_submission_asks_the_issuer_and_the_four_facts_stay_apart(self):
		self.ready()
		result = self.submit()
		self.assertTrue(result["ok"], result)
		shown = self.electronic()
		self.assertEqual((shown["submission"]["state"], shown["verification"]["state"], shown["verification"]["last_response"]), ("Submitted", "Confirmed", "Confirmed"))
		self.assertEqual(shown["verification"]["source"], SOURCE)
		self.assertTrue(shown["verification"]["responded_at"])
		self.assertIsInstance(shown["verification"]["response_ms"], int)
		self.assertEqual(shown["compliance"]["state"], "Meets")
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original receipt not yet recorded")  # the physical original is its own fact
		self.assertEqual(sv.row_for(self.bid).source, SOURCE)

	def test_the_four_issuer_responses(self):
		for suffix, expected_state, expected_last in (("", "Confirmed", "Confirmed"), ("-PENDING", "Pending", "Pending"), ("-MISMATCH", "Mismatch", "Mismatch"), ("-UNAVAILABLE", "Pending", "Unavailable")):
			with self.subTest(suffix=suffix or "plain"):
				frappe.db.delete(sv.VERIFICATION, {"bid_workspace": self.bid})
				self.answer_security(reference=REFERENCE + suffix)
				if not suffix:
					self.add_proof()
				self.submit()
				shown = self.electronic()["verification"]
				self.assertEqual((shown["state"], shown["last_response"]), (expected_state, expected_last))
				if expected_last == "Unavailable":
					self.assertEqual(shown["responded_at"], "")  # nothing was answered
					self.assertIn("stays pending", shown["text"])

	def test_an_unavailable_issuer_leaves_it_pending_and_checking_again_can_confirm(self):
		self.ready()
		simulation.set_controls(issuer_response="Unavailable")
		self.submit()
		self.assertEqual(self.electronic()["verification"]["state"], "Pending")
		simulation.set_controls(issuer_response="Automatic")
		self.assertTrue(self.check()["ok"])
		again = self.electronic()["verification"]
		self.assertEqual((again["state"], again["attempts"]), ("Confirmed", 2))

	def test_with_no_issuer_service_nothing_is_ever_confirmed(self):
		self.ready()
		previous = frappe.conf.get("kt_bds_simulation_environment")
		frappe.conf["kt_bds_simulation_environment"] = 0
		self.addCleanup(frappe.conf.__setitem__, "kt_bds_simulation_environment", previous)
		self.submit()
		shown = self.electronic()["verification"]
		self.assertEqual((shown["state"], shown["last_response"], shown["source"]), ("Pending", "Unavailable", sv.NO_SERVICE))

	def test_changing_the_instrument_after_submitting_needs_a_new_submission(self):
		self.ready()
		self.submit()
		self.answer_security(reference=REFERENCE + "-X")
		changed = self.electronic()
		self.assertEqual((changed["submission"]["state"], changed["verification"]["state"]), ("Changed since submitted", "Pending"))
		self.assertFalse(self.check()["ok"])  # checking the old submission is refused until it is submitted again
		self.assertTrue(self.submit()["ok"])
		self.assertEqual(self.electronic()["submission"]["state"], "Submitted")

	def test_compliance_compares_the_answers_with_the_published_requirement(self):
		from kentender_procurement.bid_submission.services import bid_context, clock

		self.ready()
		ctx = bid_context.load(self.bid, actor=DAVID, organisation="", at=clock.now())
		facts = sv._facts(ctx)
		self.assertEqual(sv.compliance(ctx, facts)["state"], "Meets")
		wrong = sv.compliance(ctx, {**facts, "amount": "1.00"})
		self.assertEqual(wrong["state"], "Does not meet")
		self.assertIn("the amount differs from the published amount", wrong["text"])
		self.assertEqual(sv.compliance(ctx, {**facts, "security_type": "Cash"})["state"], "Does not meet")
		self.assertEqual(sv.compliance(ctx, {**facts, "valid_until": ""})["state"], "Not yet assessed")

	def test_the_verification_record_is_sealed_and_never_blocks_the_bid(self):
		self.ready()
		self.submit()
		self.assertEqual(frappe.get_meta(sv.VERIFICATION).permissions, [])
		doc = frappe.new_doc(sv.VERIFICATION)
		self.assertFalse(doc.has_permission("read"))
		self.assertTrue(frappe.get_hooks("has_permission")[sv.VERIFICATION])
