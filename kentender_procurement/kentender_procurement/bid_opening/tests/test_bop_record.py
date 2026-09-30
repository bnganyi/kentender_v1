# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 plan Phase 6 (BOP10-601…606): the opening record, member
signing, automatic completion and the once-only Evaluation handoff, the
correction after completion, the register copy and the audit export.
Fixtures BOP-N07, N08, N09, N11; acceptance BOP-A07, A08, A10, A19; PRC-A03,
A04, A06, A07 through the real owner. Test attestations are not electronic
signatures (TRUST-ADR-001 v0.1 §2)."""

from __future__ import annotations

import json

import frappe

from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import (
	correction, export, finish, my_work_provider, reads, record, register_copy, signing,
)
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, OUTSIDER
from kentender_procurement.bid_opening.tests.test_bop_ceremony import CeremonyCase
from kentender_procurement.bid_submission.tests.support import DAVID, PETER, key

MEMBERS = (CHAIR, MEMBER, INDEPENDENT)


class RecordCase(CeremonyCase):
	def read_out_and_ended(self):
		entry = self.opened()
		self.at(self.minutes_after(1.75))
		self.assertTrue(self.readout(entry)["ok"])
		self.at(self.minutes_after(4))
		self.assertTrue(self.finish()["ok"])
		return entry

	def freeze(self):
		self.at(self.minutes_after(7))
		out = record.freeze_opening_minutes(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertTrue(out["ok"], out)
		return out

	def sign(self, user, *, only=None):
		version, mine = signing.my_targets(self.case_doc(), user)
		chosen = [t for t in mine if not only or t["target_id"] in only]
		return signing.sign_opening_record(tender=self.name, minutes_version=version, targets=[{"target_id": t["target_id"], "target_digest": t["target_digest"]}
			for t in chosen], idempotency_key=key(), user=user)

	def sign_all(self, members=MEMBERS):
		out = None
		for i, user in enumerate(members):
			self.at(self.minutes_after(8 + i))
			out = self.sign(user)
			self.assertTrue(out["ok"], out)
		return out

	def completed(self):
		entry = self.read_out_and_ended()
		self.freeze()
		self.sign_all()
		return entry


class TestPrepareAndFreeze(RecordCase):
	def test_the_draft_records_nothing_and_lists_each_members_targets(self):
		self.read_out_and_ended()
		prepare = self.next_step(CHAIR)
		self.assertEqual((prepare["headline"], prepare["primary_action"]), ("Prepare opening record", "prepare_record"))
		self.assertTrue(prepare["sentence"].endswith("The draft is built from the register, attendance and what happened in the session."))
		draft = reads.get_opening(tender=self.name, user=CHAIR)["record"]["draft"]
		pages = draft["pages"]
		self.assertGreaterEqual(pages, 1)
		mine = [t for t in draft["targets"] if t["required_member"] == MEMBER]
		self.assertEqual(sorted(t["target_type"] for t in mine), sorted(["Tender page", "Price location", *["Minutes page"] * pages, "Final minutes page"]))
		self.assertEqual({t["target_type"]: t["what_you_do"] for t in mine}, {"Tender page": "Sign the page", "Price location": "Initial the price",
			"Minutes page": "Initial each page", "Final minutes page": "Sign with full name and designation"})  # board r2
		self.assertEqual(frappe.db.count("Proceeding Minutes Version", {"proceeding": self.case_doc().proceeding}), 0)
		self.assertIsNone(reads.get_opening(tender=self.name, user=MEMBER)["record"]["draft"])  # only the recorder sees the draft
		self.assertTrue(self.next_step(MEMBER)["headline"].endswith("to prepare the opening record"))

	def test_bop_a07_a10_signing_completes_once_and_hands_the_opened_bid_to_evaluation(self):
		self.read_out_and_ended()
		frozen = self.freeze()
		doc = self.case_doc()
		self.assertEqual((doc.state, frozen["version_number"]), ("Awaiting attestations", 1))
		self.assertIn(f"Review and sign opening record for {self.reference}", [r["title"] for r in my_work_provider.my_work_rows(MEMBER)["assigned"]])
		turn = self.next_step(MEMBER)
		self.assertEqual((turn["kind"], turn["headline"]), (ns.KIND_YOUR_TURN, "Review and sign opening record"))
		# every target must be named with the digest the member saw
		version, mine = signing.my_targets(doc, MEMBER)
		with self.assertRaises(Exception) as partial:
			self.sign(MEMBER, only={mine[0]["target_id"]})
		self.assertEqual(partial.exception.code, "PRC_TARGET_CHANGED")
		with self.assertRaises(frappe.DoesNotExistError):
			signing.sign_opening_record(tender=self.name, minutes_version=version, targets=[], idempotency_key=key(), user=OUTSIDER)
		self.at(self.minutes_after(8))
		self.assertTrue(self.sign(MEMBER)["ok"])
		waiting = self.next_step(MEMBER)
		self.assertEqual(waiting["kind"], ns.KIND_WAITING)
		self.assertTrue(waiting["headline"].startswith("Waiting for ") and waiting["headline"].endswith(" to sign the opening record"))
		self.assertEqual(waiting["sentence"], f"You signed version 1 at {self.minutes_after(8)[11:16]}.")
		self.assertNotIn(f"Review and sign opening record for {self.reference}", [r["title"] for r in my_work_provider.my_work_rows(MEMBER)["assigned"]])
		self.assertTrue(self.next_step(INDEPENDENT)["sentence"].endswith(f"signed at {self.minutes_after(8)[11:16]}."))
		self.at(self.minutes_after(9))
		self.assertFalse(self.sign(INDEPENDENT)["completed"])
		self.at(self.minutes_after(10.5))
		self.assertTrue(self.sign(CHAIR)["completed"])  # the last proof completes the opening, no chair click
		doc = self.case_doc()
		self.assertEqual((doc.state, str(doc.completed_at)), ("Opening complete", self.minutes_after(10.5)))
		self.assertEqual(frappe.db.get_value("Proceeding", doc.proceeding, "state"), "Finalized")
		handoffs = frappe.get_all("Evaluation Handoff", filters={"tender": self.name}, fields=["handoff_id", "consumer", "delivery_status", "payload_json"])
		self.assertEqual(len(handoffs), 1)
		payload = json.loads(handoffs[0].payload_json)
		self.assertEqual((handoffs[0].consumer, handoffs[0].delivery_status, len(payload["packages"])), ("evaluation", "Pending", 1))
		self.assertEqual(payload["register"]["register_id"], doc.register)
		self.assertTrue(payload["opening_record"]["digest"])
		done = self.next_step(CHAIR)
		self.assertEqual(done["kind"], ns.KIND_DONE)
		self.assertTrue(done["headline"].startswith("The opening was completed at "))
		# boards r6/h1: the completion instant with its seconds (FU-BOP-25)
		completed = frappe.db.get_value("Bid Opening Case", doc.name, "completed_at")
		seconds = frappe.utils.get_datetime(completed).strftime("%H:%M:%S")
		self.assertIn(seconds, done["headline"])
		opening = reads.get_opening(tender=self.name, user=AUDITOR)
		self.assertIn(seconds, opening["record"]["completion"]["completed_label"])
		self.assertRegex(opening["record"]["versions"][0]["frozen_label"], r"\d{2}:\d{2}:\d{2}")
		self.assertEqual(done["sentence"], "The opened bid is now available to the Evaluation Committee.")
		self.assertTrue(reads.get_opening(tender=self.name, user=CHAIR)["journey"]["stages"][2]["marker"] == "done")


class TestVersionsAndProofs(RecordCase):
	def test_bop_n07_n11_a_new_version_keeps_old_proofs_but_needs_fresh_ones(self):
		self.read_out_and_ended()
		self.freeze()
		self.at(self.minutes_after(8))
		old_version, old_targets = signing.my_targets(self.case_doc(), MEMBER)
		self.sign(MEMBER)
		self.at(self.minutes_after(8.75))
		with self.assertRaises(Exception):
			record.supersede_opening_minutes(tender=self.name, reason="x", correction_note="y", expected_version=self.case_version(), idempotency_key=key(), user=MEMBER)
		empty = record.supersede_opening_minutes(tender=self.name, reason="", correction_note="", expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual(empty["ok"], False)
		v2 = record.supersede_opening_minutes(tender=self.name, reason="Add the attendee’s repeat request and the chair’s response",
			correction_note="The attendee asked for the total to be repeated; the member repeated it.", expected_version=self.case_version(), idempotency_key=key(),
			user=CHAIR)
		self.assertEqual(v2["version_number"], 2)
		changed = self.next_step(MEMBER)
		self.assertEqual((changed["kind"], changed["headline"]), (ns.KIND_YOUR_TURN, "The opening record changed. Review the latest version before signing"))
		with self.assertRaises(Exception) as stale:
			signing.sign_opening_record(tender=self.name, minutes_version=old_version, targets=[{"target_id": t["target_id"], "target_digest": t["target_digest"]}
				for t in old_targets], idempotency_key=key(), user=MEMBER)
		self.assertEqual(stale.exception.code, "PRC_TARGET_CHANGED")
		kept = frappe.get_all("Proceeding Attestation", filters={"minutes_version": old_version, "member_user": MEMBER}, pluck="satisfies_current")
		self.assertTrue(kept and set(kept) == {0})
		self.sign_all()
		self.assertEqual(self.case_doc().state, "Opening complete")

	def test_an_unverified_proof_does_not_count(self):
		self.read_out_and_ended()
		self.freeze()
		self._flag("kt_prc_signing_outcome", "Rejected")
		refused = self.sign(MEMBER)
		self.assertEqual((refused["ok"], refused["code"]), (False, "PRC_PROOF_UNVERIFIED"))
		self._flag("kt_prc_signing_outcome", None)
		self.assertEqual(self.case_doc().state, "Awaiting attestations")
		self.assertEqual(self.next_step(MEMBER)["headline"], "Review and sign opening record")


class TestEmptyCompletion(RecordCase):
	def test_bop_a19_n08_an_empty_opening_completes_with_no_evaluation_handoff(self):
		self.ready_to_open()
		self.at(self.minutes_after(12 / 60))
		self.begin()
		self.at(self.minutes_after(1))
		finish.end_with_no_bids(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.freeze()
		_version, mine = signing.my_targets(self.case_doc(), MEMBER)
		self.assertEqual({t["target_type"] for t in mine}, {"Minutes page", "Final minutes page"})  # only the opening-record targets
		self.sign_all()
		doc = self.case_doc()
		self.assertEqual((doc.state, doc.outcome, doc.evaluation_handoff), ("Opening complete", "No bids", None))
		self.assertEqual(frappe.db.count("Evaluation Handoff", {"tender": self.name}), 0)
		self.assertEqual(self.next_step(CHAIR)["headline"], "Opening complete — no bids to evaluate")


class TestAfterCompletion(RecordCase):
	def test_bop_n11_a_correction_is_one_of_four_kinds_and_leaves_the_original(self):
		self.completed()
		before = export.export_opening(tender=self.name, user=AUDITOR)
		self.at(self.minutes_after(15))
		denied = correction.correct_opening_record(tender=self.name, kind="Submitted total", correct_information="KES 1.00", reason="x",
			expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual((denied["ok"], denied["message"]), (False, "This correction cannot change a bid or replace the signed opening record."))
		with self.assertRaises(frappe.DoesNotExistError):
			correction.correct_opening_record(tender=self.name, kind="Attendance note", correct_information="x", reason="y", expected_version=self.case_version(),
				idempotency_key=key(), user=MEMBER)
		added = correction.correct_opening_record(tender=self.name, kind="Attendance note", correct_information="Test Attendee left at 11:03 EAT",
			reason="Add the departure noted during the opening", expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertTrue(added["ok"])
		after = export.export_opening(tender=self.name, user=AUDITOR)
		self.assertEqual(before["proceedings"]["original"], after["proceedings"]["original"])
		self.assertTrue(after["proceedings"]["original_digest_verified"])
		self.assertEqual([s["kind"] for s in after["proceedings"]["supplements"]], ["Attendance note"])
		self.assertEqual(before["evaluation_handoff"], after["evaluation_handoff"])
		self.assertTrue(self.next_step(CHAIR)["headline"].startswith("Correction added at "))
		with self.assertRaises(frappe.DoesNotExistError):
			export.export_opening(tender=self.name, user="Administrator")

	def test_bop_a08_n09_only_a_submitting_tenderer_gets_the_register(self):
		self.read_out_and_ended()
		with self.assertRaises(frappe.DoesNotExistError):
			register_copy.request_opening_register(tender=self.name, idempotency_key=key(), user=PETER)  # a supplier who did not bid
		with self.assertRaises(frappe.DoesNotExistError):
			register_copy.request_opening_register(tender=self.name, idempotency_key=key(), user=OUTSIDER)
		pending = register_copy.request_opening_register(tender=self.name, idempotency_key=key(), user=DAVID)
		self.assertEqual(pending["status"], "Pending")  # the record is not complete yet
		with self.assertRaises(frappe.DoesNotExistError):
			register_copy.get_register_copy(tender=self.name, user=DAVID)
		self.freeze()
		self.sign_all()
		copy = register_copy.get_register_copy(tender=self.name, user=DAVID)
		self.assertTrue(copy["content"].startswith(b"%PDF"))
		self.assertEqual(copy["register_digest"], frappe.db.get_value("Opening Register", self.case_doc().register, "register_digest"))
		self.assertEqual(frappe.db.get_value("Opening Register Request", {"requester_user": DAVID}, "status"), "Delivered")

	def test_when_self_service_is_off_the_accounting_officer_provides_it(self):
		settings = frappe.get_doc("Bid Opening Settings")
		settings.register_self_service = 0
		settings.flags.kt_bop_command = True
		settings.save(ignore_permissions=True)
		self.addCleanup(lambda: frappe.db.set_single_value("Bid Opening Settings", "register_self_service", None))
		self.completed()
		request = register_copy.request_opening_register(tender=self.name, idempotency_key=key(), user=DAVID)
		self.assertEqual(request["status"], "Pending")
		self.assertIn(f"Provide opening register for {self.reference}", [r["title"] for r in my_work_provider.my_work_rows(AO)["assigned"]])
		register_copy.provide_register_copy(tender=self.name, request=request["request"], idempotency_key=key(), user=AO)
		self.assertEqual(frappe.db.get_value("Opening Register Request", {"request_id": request["request"]}, "status"), "Ready")
		self.assertNotIn(f"Provide opening register for {self.reference}", [r["title"] for r in my_work_provider.my_work_rows(AO)["assigned"]])
