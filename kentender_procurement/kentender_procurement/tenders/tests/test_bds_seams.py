# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published Tenders seams Bid Submission consumes (BDS-CHG-001 v0.8
plan D3; Tenders tracker TND12-B01…B04):

- `bidder_projection` — the allowlisted public Tender list and detail with
  effective addenda applied, the guest-safe document stream, anonymous
  public answers and one candidate's own questions and notices (BDS §7.1
  `GetAvailableTenders` / `GetPublishedTenderForBidder`);
- `bid_definition.definition_for` / `map_bid_definition_addendum` — the
  exact stored identity map of each successor definition (BDS §4.4.6,
  §7.4 `MapBidDefinitionAddendum`; heuristic matching is prohibited);
- `events.pending_for_consumer` — the outbox read across Tenders;
- the candidate-registry test override on `frappe.flags`.
"""

from __future__ import annotations

import json
import re
from collections import Counter

import frappe

from kentender_procurement.std_templates.compiler import addenda as std_addenda
from kentender_procurement.std_templates.services import runtime as std_runtime
from kentender_procurement.tenders.services import addenda, bid_definition, bidder_projection, cancellation, candidate_gateway, clarifications, digest, events, submission_close
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fake_candidates
from kentender_procurement.tenders.tests import fixtures as fx
from kentender_procurement.tenders.tests.test_open_period import CHANNELS, OpenPeriodCase

LIST_KEYS = {"reference", "title", "procuring_entity", "method", "reservation", "submission_deadline", "published_at", "availability"}
TENDER_KEYS = {
	"reference", "title", "procuring_entity", "method", "reservation", "items", "total_quantity", "delivery_location", "latest_delivery", "currency",
	"tender_security_amount", "validity_days", "published_at", "clarification_deadline", "original_submission_deadline", "submission_deadline",
	"availability", "clarifications_open", "documents", "addenda", "answers", "cancellation",
}
#: Internal record names, release/definition identities, private paths and digests never reach a supplier.
LEAK = re.compile(r"\bTD[RVPAC]-\d|\bTBD-|\bTC[QN]-|stdr-|PBD-|/private/|file_url|\b[0-9a-f]{64}\b")
QUESTION = "May the two comparable contracts be from different customers?"
ANSWER = "Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer."


class BidSeamsCase(OpenPeriodCase):
	CANDIDATE = {"bidder_arrangement_id": "ARR-TNDT-001", "candidate_name": "Afya Digital Supplies Limited", "notice_address": "tenders@afyadigital.example"}
	SECOND = {"bidder_arrangement_id": "ARR-TNDT-002", "candidate_name": "Second Supplier Limited", "notice_address": "bids@second.example"}

	def setUp(self):
		super().setUp()
		self.candidates = fake_candidates.install(self)
		self.reference = self._root().tender_reference
		frappe.flags.kt_tenders_notice_sync = True
		frappe.flags.kt_tenders_notice_transport = lambda notice: {"result": "Delivered", "provider_reference": f"test:{notice.name}", "failure_reason": ""}
		self.addCleanup(setattr, frappe.flags, "kt_tenders_notice_sync", False)
		self.addCleanup(setattr, frappe.flags, "kt_tenders_notice_transport", None)

	def _register(self):
		frappe.flags.kt_tenders_clock = "2027-05-19 09:20:00"
		for candidate in (self.CANDIDATE, self.SECOND):
			self.candidates.register(tender=self.name, **candidate)

	def _issue(self, *, confirm: bool = True) -> str:
		frappe.flags.kt_tenders_clock = "2027-05-31 08:30:00"
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "revised_submission_deadline": "2027-06-12 11:00:00"})
		root = self._root()
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		frappe.flags.kt_tenders_clock = "2027-05-31 09:00:00"
		addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		if confirm:
			self._confirm_addendum(name)
		return name

	def _confirm_addendum(self, name: str) -> None:
		for channel in CHANNELS:
			self._confirm("addendum", channel, addendum=name, available_at="2027-05-31 09:00:00")

	def _answer(self, clarification: str, text: str, audience: str) -> None:
		root = self._root()
		clarifications.respond_to_tender_clarification(tender=self.name, clarification=clarification, response=text, affects_published_tender=False, response_audience=audience, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)


class TestPublicTender(BidSeamsCase):
	def test_the_list_is_allowlisted_and_availability_follows_trusted_time(self):
		rows = bidder_projection.available_tenders(at="2027-05-20 10:00:00")
		mine = [r for r in rows if r["reference"] == self.reference]
		self.assertEqual(len(mine), 1)
		self.assertEqual(set(mine[0]), LIST_KEYS)
		expected_reservation = bid_definition.projection(self._root(), frappe.get_doc("Tender Version", frappe.db.get_value("Tender Publication", self._root().publication, "tender_version")), publication_id="x")["reservation"]["category"]
		self.assertEqual(
			(mine[0]["title"], mine[0]["method"], mine[0]["reservation"], mine[0]["submission_deadline"], mine[0]["published_at"], mine[0]["availability"]),
			("Supply and delivery of business laptops", "Open Tender", expected_reservation, "2027-06-05T11:00:00+03:00", "2027-05-15T08:00:00+03:00", "open"),
		)
		self.assertIsNone(LEAK.search(json.dumps(rows)))
		# the deadline instant itself is closed (strict before), before the close job runs
		at_deadline = next(r for r in bidder_projection.available_tenders(at="2027-06-05 11:00:00") if r["reference"] == self.reference)
		self.assertEqual(at_deadline["availability"], "closed")

	def test_an_unpublished_tender_is_never_public(self):
		frappe.db.set_value("Tender", self.name, "published_at", None, update_modified=False)
		self.assertIsNone(bidder_projection.published_tender(self.reference))
		self.assertIsNone(bidder_projection.resolve_published(self.reference))
		self.assertNotIn(self.reference, [r["reference"] for r in bidder_projection.available_tenders()])
		self.assertIsNone(bidder_projection.stream_public_document(self.reference, "invitation"))

	def test_the_detail_carries_current_facts_and_applies_an_addendum_only_once_effective(self):
		self.assertEqual(bidder_projection.resolve_published(self.reference), self.name)
		before = bidder_projection.published_tender(self.reference, at="2027-05-20 10:05:00")
		self.assertEqual(set(before), TENDER_KEYS)
		self.assertEqual(
			(before["delivery_location"], before["submission_deadline"], before["original_submission_deadline"], before["clarification_deadline"], before["addenda"], before["clarifications_open"], before["availability"]),
			(fx.LOCATION, "2027-06-05T11:00:00+03:00", "2027-06-05T11:00:00+03:00", "2027-05-27T17:00:00+03:00", [], True, "open"),
		)
		self.assertEqual((before["currency"], before["tender_security_amount"], before["validity_days"], before["total_quantity"]), ("KES", "500000", 120, {"quantity": "1", "unit": "Each"}))
		self.assertEqual([(d["key"], d["label"], d["published_at"]) for d in before["documents"]], [("invitation", "Invitation to Tender", "2027-05-15T08:00:00+03:00"), ("complete-tender", "Complete Tender", "2027-05-15T08:00:00+03:00")])
		name = self._issue(confirm=False)
		awaiting = bidder_projection.published_tender(self.reference, at="2027-05-31 09:00:00")
		self.assertEqual((awaiting["addenda"], awaiting["delivery_location"], awaiting["submission_deadline"]), ([], fx.LOCATION, "2027-06-05T11:00:00+03:00"))
		self._confirm_addendum(name)
		after = bidder_projection.published_tender(self.reference, at="2027-06-01 12:15:00")
		addendum_reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.assertEqual(after["delivery_location"], self.FIXTURE_ADDENDUM["revised_value"])
		self.assertEqual((after["submission_deadline"], after["original_submission_deadline"], after["clarifications_open"]), ("2027-06-12T11:00:00+03:00", "2027-06-05T11:00:00+03:00", False))
		self.assertEqual(after["addenda"], [{"reference": addendum_reference, "summary": "Delivery point clarified", "issued_at": "2027-05-31T09:00:00+03:00", "revised_submission_deadline": "2027-06-12T11:00:00+03:00", "document_key": addendum_reference}])
		self.assertIsNone(LEAK.search(json.dumps(after)))

	def test_documents_stream_by_public_key_without_a_path_or_digest(self):
		invitation = bidder_projection.stream_public_document(self.reference, "invitation")
		self.assertEqual(set(invitation), {"file_name", "content_type", "content"})
		self.assertTrue(invitation["file_name"].startswith("Invitation to Tender."))
		self.assertGreater(len(invitation["content"]), 100)
		self.assertTrue(bidder_projection.stream_public_document(self.reference, "complete-tender")["file_name"].startswith("Complete Tender."))
		for key in ("internal", "../invitation", ""):
			self.assertIsNone(bidder_projection.stream_public_document(self.reference, key))
		self.assertIsNone(bidder_projection.stream_public_document("TND-NOT-A-TENDER", "invitation"))
		name = self._issue(confirm=False)
		addendum_reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.assertIsNone(bidder_projection.stream_public_document(self.reference, addendum_reference))  # frozen, not public yet
		self._confirm_addendum(name)
		notice = bidder_projection.stream_public_document(self.reference, addendum_reference)
		self.assertEqual(notice["file_name"].rsplit(".", 1)[0], addendum_reference)

	def test_a_guest_reads_the_same_public_projection(self):
		expected = bidder_projection.published_tender(self.reference, at="2027-05-20 10:05:00")
		frappe.set_user("Guest")
		self.assertEqual(bidder_projection.published_tender(self.reference, at="2027-05-20 10:05:00"), expected)
		self.assertIsNotNone(bidder_projection.stream_public_document(self.reference, "invitation"))

	def test_a_cancelled_tender_stays_readable_with_its_notice_and_is_not_open(self):
		frappe.flags.kt_tenders_clock = "2027-06-04 14:00:00"
		root = self._root()
		cancellation.cancel_tender(tender=self.name, ground="INADEQUATE_BUDGET", reason="The confirmed budget available for this procurement is insufficient to proceed.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		detail = bidder_projection.published_tender(self.reference, at="2027-06-04 15:00:00")
		self.assertEqual((detail["availability"], detail["clarifications_open"], detail["cancellation"]), ("cancelled", False, {"cancelled_at": "2027-06-04T14:00:00+03:00", "notice_key": "cancellation-notice"}))
		self.assertIsNotNone(bidder_projection.stream_public_document(self.reference, "cancellation-notice"))
		self.assertEqual(next(r for r in bidder_projection.available_tenders(at="2027-06-04 15:00:00") if r["reference"] == self.reference)["availability"], "cancelled")


class TestAnswersAndCandidateView(BidSeamsCase):
	def test_public_answers_are_anonymous_and_asker_only_answers_stay_private(self):
		self._register()
		first = clarifications.receive_tender_clarification(tender=self.name, candidate_registration_id="ARR-TNDT-001", question=QUESTION, received_at="2027-05-26 09:00:00", inbound_event_id="EVT-1", user=fx.PRODUCER)
		second = clarifications.receive_tender_clarification(tender=self.name, candidate_registration_id="ARR-TNDT-002", question="Is a local warranty partner acceptable?", received_at="2027-05-26 09:30:00", inbound_event_id="EVT-2", user=fx.PRODUCER)
		frappe.flags.kt_tenders_clock = "2027-05-26 11:00:00"
		self._answer(first["clarification"], ANSWER, "All registered candidates")
		self._answer(second["clarification"], "Yes, if the manufacturer authorises the partner.", "Asker only")
		answers = bidder_projection.public_answers(self.name)
		self.assertEqual([(a["question"], a["answer"], a["answered_at"]) for a in answers], [(QUESTION, ANSWER, "2027-05-26T11:00:00+03:00")])
		self.assertEqual(set(answers[0]), {"key", "question", "answer", "answered_at"})
		self.assertNotIn("ARR-", json.dumps(answers))
		self.assertEqual(bidder_projection.published_tender(self.reference, at="2027-05-26 12:00:00")["answers"], answers)
		# each candidate sees only its own questions, and the notices sent to it
		asker = bidder_projection.candidate_view(self.name, "ARR-TNDT-001")
		self.assertEqual([(q["question"], q["status"], q["audience"], q["answer"]) for q in asker["questions"]], [(QUESTION, "Answered", "All registered candidates", ANSWER)])
		self.assertEqual([(n["kind"], n["subject_key"], n["status"]) for n in asker["notices"]], [("answer", answers[0]["key"], "Delivered")])
		other = bidder_projection.candidate_view(self.name, "ARR-TNDT-002")
		self.assertEqual([(q["question"], q["audience"]) for q in other["questions"]], [("Is a local warranty partner acceptable?", "Asker only")])
		self.assertEqual(Counter(n["kind"] for n in other["notices"]), Counter({"answer": 2}))
		self.assertIsNone(LEAK.search(json.dumps(asker) + json.dumps(other)))
		self.assertIsNone(bidder_projection.candidate_view(self.name, "ARR-NOT-REGISTERED"))

	def test_an_addendum_notice_is_keyed_by_the_addendum_reference(self):
		self._register()
		name = self._issue()
		addendum_reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		view = bidder_projection.candidate_view(self.name, "ARR-TNDT-001")
		self.assertEqual([(n["kind"], n["subject_key"], n["status"]) for n in view["notices"]], [("addendum", addendum_reference, "Delivered")])
		self.assertEqual(set(view["notices"][0]), {"kind", "subject_key", "status", "attempt_count", "last_attempt_at", "delivered_at"})


class TestDefinitionMap(BidSeamsCase):
	def test_a_successor_stores_the_exact_identity_map_against_its_predecessor(self):
		original = bid_definition.current(self.name)
		loaded = bid_definition.definition_for(self.name, original["definition_version"])
		self.assertEqual((loaded["definition_digest"], loaded["status"], loaded["definition"]), (original["definition_digest"], "Effective", original["definition"]))
		self.assertIsNone(bid_definition.definition_for(self.name, 99))
		name = self._issue(confirm=False)
		row = frappe.get_doc("Tender Bid Definition", frappe.db.get_value("Tender Addendum", name, "successor_bid_definition"))
		self.assertEqual(row.predecessor_bid_definition, original["name"])
		stored = json.loads(row.identity_map_json)
		self.assertEqual(row.identity_map_digest, digest.sha256_hex(stored))
		release = std_runtime.release_doc(json.loads(row.definition_json)["template_release_id"])
		self.assertEqual(stored["classifications"], std_addenda.classify(original["definition"], json.loads(row.definition_json), std_runtime.installed_assets(release).addendum_rules))
		self.assertGreater(Counter(c["classification"] for c in stored["classifications"])["unchanged"], 0)
		with self.assertRaises(TendersError):  # a frozen successor is not bidder-current yet
			bid_definition.map_bid_definition_addendum(tender=self.name, from_version=1, to_version=2)
		self._confirm_addendum(name)
		mapped = bid_definition.map_bid_definition_addendum(tender=self.name, from_version=1, to_version=2)
		addendum_reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.assertEqual([(s["from_version"], s["to_version"], s["addendum_reference"]) for s in mapped["steps"]], [(1, 2, addendum_reference)])
		self.assertEqual((mapped["steps"][0]["classifications"], mapped["steps"][0]["fresh_required"]), (stored["classifications"], stored["fresh_required"]))
		self.assertEqual(mapped["to_definition_digest"], row.definition_digest)
		self.assertEqual(bid_definition.map_bid_definition_addendum(tender=self.name, from_version=2, to_version=2)["steps"], [])
		for bad in ((2, 1), (1, 3)):
			with self.assertRaises(TendersError):
				bid_definition.map_bid_definition_addendum(tender=self.name, from_version=bad[0], to_version=bad[1])


class TestConsumerSeams(BidSeamsCase):
	def test_pending_events_are_read_by_consumer_across_tenders(self):
		frappe.flags.kt_tenders_clock = "2027-06-05 11:00:00"
		submission_close.close_due_submission_periods()
		pending = events.pending_for_consumer(event_type=submission_close.EVENT_TYPE, consumer=submission_close.CONSUMER)
		self.assertIn(self.name, [e.tender for e in pending])
		self.assertEqual({e.status for e in pending}, {"Pending"})
		self.assertEqual(events.pending_for_consumer(event_type=submission_close.EVENT_TYPE, consumer="someone-else"), [])
		opened = events.pending_for_consumer(event_type="TenderOpenForSubmission", consumer="bidder-service")
		self.assertIn(self.name, [e.tender for e in opened])

	def test_a_provider_set_through_the_flag_answers_the_gateway(self):
		class Provider:
			@staticmethod
			def candidate_audience(*, tender, at):
				return [{"candidate_registration_id": "ARR-FAKE-001", "destination": "fake@example.test", "destination_version": "3"}]

			@staticmethod
			def candidate_registration(*, tender, candidate_registration_id):
				return {"candidate_registration_id": candidate_registration_id, "candidate_name": "Fake Supplier", "destination": "fake@example.test", "destination_version": "3", "registered_at": None} if candidate_registration_id == "ARR-FAKE-001" else None

		frappe.flags.kt_tender_candidate_registry = Provider
		self.assertEqual([r["candidate_registration_id"] for r in candidate_gateway.candidate_audience(tender=self.name)], ["ARR-FAKE-001"])
		self.assertEqual(candidate_gateway.candidate_name(tender=self.name, candidate_registration_id="ARR-FAKE-001"), "Fake Supplier")
		# without the test flag the gateway asks Bid Submission's provider (TPR FU-25: the stand-in is retired)
		frappe.flags.kt_tender_candidate_registry = None
		self.assertEqual(candidate_gateway._provider().__name__, "kentender_procurement.bid_submission.services.candidate_registry")
		self.assertFalse(frappe.db.exists("DocType", "Tender Candidate Registration"))
