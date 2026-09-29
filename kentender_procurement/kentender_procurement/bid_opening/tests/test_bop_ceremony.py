# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 plan Phase 5 (BOP10-501…508): Begin, one bid at a time,
the readout with its pages, requests, a member's own account, a comment for
Evaluation, pauses and their recovery, the empty outcome, the end of the
ceremony and a cancellation after Start. Fixtures BOP-N02, N02A, N04, N05,
N06, N12, N15, N16, N18; acceptance BOP-A02, A04, A05, A06, A09, A14, A18,
A20. Test stand-ins only (owner decision OD-C)."""

from __future__ import annotations

import hashlib
import json

import frappe

from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import (
	cancellation, ceremony, finish, incidents, interventions, my_work_provider, presence, reads, renders, simulation,
)
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, OUTSIDER, SUPPORT, OpeningCase
from kentender_procurement.bid_submission.services import simulation as bds_simulation
from kentender_procurement.bid_submission.test_services import tender_box
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


def events_of(case_doc, event_type: str) -> list:
	return frappe.get_all("Proceeding Event", filters={"proceeding": case_doc.proceeding, "event_type": event_type},
		fields=["event_id", "recorded_at", "reported_at", "reported_by", "actor", "linked_event", "source"], order_by="sequence asc")


class CeremonyCase(OpeningCase, SubmissionCase):
	def setUp(self):
		super().setUp()
		self.addCleanup(lambda: bds_simulation.set_controls(reveal_outcome="Deliver"))

	def started_with_one_bid(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.ready_to_open()
		self.at(self.minutes_after(12 / 60))
		self.assertTrue(self.begin()["ok"])

	def opened(self):
		self.started_with_one_bid()
		self.at(self.minutes_after(1))
		out = self.open_next()
		self.assertTrue(out["ok"], out)
		return out["entry"]


class TestBegin(CeremonyCase):
	def test_bop_n02_begin_needs_the_whole_committee_and_only_the_chair(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.prepared()
		self.at(self.minutes_before(0.5))
		self.join(CHAIR)
		self.join(MEMBER)
		interventions.record_attendance(tender=self.name, person_name="Test Attendee", capacity="Tenderer representative", movement="Arrival",
			represented_tenderer="Example Test Supplier Ltd", idempotency_key=key(), user=CHAIR)
		self.close_box()
		self.heartbeat_all((CHAIR, MEMBER))
		self.receive()
		self.at(self.minutes_after(0.2))
		refused = self.begin()
		self.assertEqual((refused["ok"], refused["code"]), (False, "BOP_MEMBER_ABSENT"))
		self.assertEqual(self.case_doc().state, "Ready to open")
		with self.assertRaises(frappe.DoesNotExistError):
			self.begin(user=MEMBER)
		self.join(INDEPENDENT)
		started = self.begin()
		self.assertTrue(started["ok"])
		doc = self.case_doc()
		self.assertEqual((doc.state, started["bids"]), ("Opening", 1))
		proceeding = frappe.get_doc("Proceeding", doc.proceeding)
		self.assertEqual((proceeding.state, len(proceeding.members)), ("In session", 3))
		self.assertEqual(frappe.db.count("Proceeding Attendance", {"proceeding": doc.proceeding, "person_name": "Test Attendee"}), 1)  # carried, not re-recorded
		with self.assertRaises(Exception) as again:
			self.begin()
		self.assertEqual(again.exception.code, "BOP_VERSION_CONFLICT")


class TestMainPath(CeremonyCase):
	def test_bop_a05_a20_one_bid_opened_read_out_recorded_and_ended(self):
		self.started_with_one_bid()
		self.assertEqual((self.next_step(CHAIR)["headline"], self.next_step(CHAIR)["primary_action"]), ("Open the first bid", "open_next"))
		self.at(self.minutes_after(1))
		entry = self.open_next()["entry"]
		row = frappe.get_doc("Opening Entry", {"entry_id": entry})
		# The facts are the sealed package's own, unchanged (BOP-A05, §5 "never corrected at opening").
		from kentender_procurement.bid_opening.services import labels
		from kentender_procurement.bid_opening.services.package_renderer import facts_of

		correlation = frappe.db.get_value("Bid Submission Attempt", {"submission_version": row.submission_version, "status": "Accepted"}, "correlation_id")
		sealed = facts_of(json.loads(tender_box.stored_package(correlation)))
		self.assertEqual((row.bidder_name, row.currency, row.status, row.security_given), (sealed["tenderer_name"], sealed["currency"], "Opened",
			labels.security(sealed["security_given"])))
		self.assertEqual(float(row.submitted_total), float(sealed["submitted_total"]))
		total = float(row.submitted_total)
		self.assertGreaterEqual(row.page_count, 2)
		self.assertTrue(renders.read(entry).startswith(b"%PDF"))
		manifest = json.loads(frappe.db.get_value("Bid Opening Handoff", self.case_doc().manifest_handoff, "payload_json"))
		self.assertEqual(row.package_digest, manifest["envelopes"][0]["package_digest"])
		read = self.next_step(MEMBER)
		self.assertEqual((read["kind"], read["headline"]), (ns.KIND_YOUR_TURN, "Read these details aloud"))
		self.assertEqual(self.next_step(CHAIR)["headline"], "Record what was read aloud")
		with self.assertRaises(Exception) as early:
			self.open_next()
		self.assertEqual(early.exception.code, "BOP_READOUT_INCOMPLETE")
		# BOP-N16: wrong bid, absent or non-member speaker, pages outside the bid, a speech time before the reveal
		with self.assertRaises(Exception):
			self.readout("BOC-NOT-A-BID")
		self.assertEqual(self.readout(entry, speaker=OUTSIDER)["ok"], False)
		self.assertEqual(self.readout(entry, pages=(row.page_count + 1,))["ok"], False)
		self.assertEqual(self.readout(entry, reported=self.minutes_after(0.5))["ok"], False)
		self.at(self.minutes_after(1.75))
		done = self.readout(entry, reported=self.minutes_after(1.5), pages=(1,))
		self.assertTrue(done["ok"], done)
		row.reload()
		self.assertEqual((row.status, str(row.readout_confirmed_at), str(row.reported_speech_at), row.designated_pages), ("Read out", self.minutes_after(1.75),
			self.minutes_after(1.5), "1"))
		[readout] = events_of(self.case_doc(), "ReadoutConfirmed")
		self.assertEqual((str(readout.recorded_at), str(readout.reported_at), readout.reported_by), (self.minutes_after(1.75), self.minutes_after(1.5), CHAIR))
		self.assertEqual(float(frappe.db.get_value("Opening Entry", {"entry_id": entry}, "submitted_total")), total)  # never edited
		with self.assertRaises(Exception) as none_left:
			self.open_next()
		self.assertEqual(none_left.exception.code, "BOP_VERSION_CONFLICT")
		# a request answered during opening, a member's own account, a comment for Evaluation (BOP-A14, BOP-N15)
		asked = interventions.record_intervention(tender=self.name, exception_class="Repeat request", speaker_name="Test Attendee",
			what="Asked for the submitted total to be repeated", response="The member repeated KES 46,400,000.00.", entry=entry, reported_at=self.minutes_after(1.7),
			idempotency_key=key(), user=CHAIR)
		self.assertTrue(asked["ok"])
		with self.assertRaises(frappe.DoesNotExistError):
			interventions.record_member_account(tender=self.name, account="Not mine to write.", idempotency_key=key(), user=OUTSIDER)
		account = interventions.record_member_account(tender=self.name, account="I could not hear the security reference clearly.", entry=entry,
			idempotency_key=key(), user=INDEPENDENT)
		self.assertEqual(frappe.db.get_value("Proceeding Event", account["event"], ["actor", "source"]), (INDEPENDENT, "Member"))
		interventions.record_intervention(tender=self.name, exception_class="Procedural comment", speaker_name="Test Independent Member",
			what="Asked for the security reference to be repeated", response="The member repeated the reference.", linked_account=account["event"],
			idempotency_key=key(), user=CHAIR)
		comment = interventions.record_comment_for_evaluation(tender=self.name, entry=entry, made_by="Test Independent Member",
			comment="The security reference on the price page differs from the reference read aloud.",
			response="The observation is recorded for the Evaluation Committee to check. No decision is made at opening.", idempotency_key=key(), user=CHAIR)
		self.assertTrue(comment["ok"])
		outcomes = frappe.get_all("Opening Exception", filters={"opening_case": self.case_doc().name}, pluck="outcome", order_by="recorded_at asc")
		self.assertEqual(outcomes, ["Answered during opening", "Answered during opening", "Recorded for Evaluation"])
		self.assertEqual(float(frappe.db.get_value("Opening Entry", {"entry_id": entry}, "submitted_total")), total)  # BOP-A06: nothing changed the bid
		end = self.next_step(CHAIR)
		self.assertEqual((end["headline"], end["primary_action"]), ("End the opening", "end"))
		self.at(self.minutes_after(4))
		key_ = key()
		ended = finish.finish_ceremony(tender=self.name, expected_version=self.case_version(), idempotency_key=key_, user=CHAIR)
		replay = finish.finish_ceremony(tender=self.name, expected_version=ended["record_version"] - 1, idempotency_key=key_, user=CHAIR)
		self.assertEqual(ended, replay)  # BOP-N06: a replay changes nothing
		doc = self.case_doc()
		self.assertEqual((doc.state, doc.outcome), ("Readout complete", "Bids opened"))
		register = frappe.get_doc("Opening Register", doc.register)
		self.assertEqual((register.entry_count, register.is_empty, json.loads(register.entry_ids_json)), (1, 0, [entry]))
		self.assertEqual(register.register_digest, hashlib.sha256(json.dumps(finish.register_rows(doc.name), sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest())
		self.assertEqual(frappe.db.get_value("Proceeding", doc.proceeding, "state"), "Session ended")
		self.assertEqual(self.next_step(CHAIR)["headline"], "Prepare opening record")
		self.assertIn(f"Prepare opening record for {self.reference}", [r["title"] for r in my_work_provider.my_work_rows(CHAIR)["assigned"]])
		audit = reads.get_opening(tender=self.name, user=AUDITOR)["ceremony"]
		self.assertEqual([r["tenderer"] for r in audit["register"]], [row.bidder_name])
		self.assertIsNone(reads.get_opening(tender=self.name, user="Administrator")["ceremony"])  # no bid facts for a technical reader


class TestEmpty(CeremonyCase):
	def test_bop_n12_a_convened_empty_opening_ends_with_one_action(self):
		self.ready_to_open()
		self.at(self.minutes_after(12 / 60))
		self.assertEqual(self.begin()["bids"], 0)
		zero = self.next_step(CHAIR)
		self.assertEqual((zero["headline"], zero["primary_action"]), ("No bids to open", "end_no_bids"))
		with self.assertRaises(Exception):
			self.finish()
		self.at(self.minutes_after(1))
		key_ = key()
		ended = finish.end_with_no_bids(tender=self.name, expected_version=self.case_version(), idempotency_key=key_, user=CHAIR)
		self.assertEqual(ended, finish.end_with_no_bids(tender=self.name, expected_version=ended["record_version"] - 1, idempotency_key=key_, user=CHAIR))
		doc = self.case_doc()
		self.assertEqual((doc.state, doc.outcome, frappe.db.get_value("Opening Register", doc.register, "is_empty")), ("Readout complete", "No bids", 1))
		self.assertEqual((len(events_of(doc, "NoBidsOutcome")), len(events_of(doc, "ProceedingEnded"))), (1, 1))
		self.assertEqual(frappe.db.count("Opening Entry", {"opening_case": doc.name}), 0)

	def test_bop_n04_a_withdrawn_bid_is_never_opened(self):
		from kentender_procurement.bid_submission.services import withdrawal
		from kentender_procurement.bid_submission.tests.support import MARY

		receipt = self.submit(self.signed())["receipt_reference"]
		self.at("2027-05-31 09:00:00")
		withdrawn = withdrawal.withdraw_bid(bid_reference=self.bid, receipt_reference=receipt, reason="Our pricing changed after the addendum was issued.",
			confirmed=True, expected_record_version=self.version(), idempotency_key=key(), user=MARY)
		self.assertTrue(withdrawn["ok"], withdrawn)
		self.ready_to_open()
		self.at(self.minutes_after(12 / 60))
		self.assertEqual(self.begin()["bids"], 0)


class TestPauses(CeremonyCase):
	def test_branch_1_a_member_leaving_pauses_and_rejoining_resumes(self):
		entry = self.opened()
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		self.at(self.minutes_after(2))
		presence.leave_opening(tender=self.name, idempotency_key=key(), user=INDEPENDENT)
		doc = self.case_doc()
		self.assertEqual(doc.state, "Interrupted")
		wait = self.next_step(CHAIR)
		from kentender_procurement.bid_opening.services import people

		officers = ", ".join(people.full_name(u) for u in people.accounting_officers())
		self.assertEqual((wait["kind"], wait["headline"]), (ns.KIND_WAITING, f"Waiting for Test Independent Member to rejoin or for {officers} to appoint a replacement"))
		self.assertTrue(wait["sentence"].startswith("Opening is paused because Test Independent Member is not present."))
		self.assertIn(f"Appoint replacement for {self.reference}", [r["title"] for r in my_work_provider.my_work_rows(AO)["assigned"]])
		with self.assertRaises(Exception):
			interventions.record_intervention(tender=self.name, exception_class="Repeat request", speaker_name="x", what="y", response="z", idempotency_key=key(), user=CHAIR)
		with self.assertRaises(Exception):
			self.finish()
		self.at(self.minutes_after(5))
		rejoined = self.join(INDEPENDENT)
		self.assertTrue(rejoined["resumed"])
		doc = self.case_doc()
		self.assertEqual(doc.state, "Opening")
		self.assertEqual(frappe.db.get_value("Proceeding", doc.proceeding, "state"), "In session")
		self.assertEqual((len(events_of(doc, "OpeningPaused")), len(events_of(doc, "OpeningResumed"))), (1, 1))
		self.assertTrue(self.finish()["ok"])

	def test_bop_n02a_a_lapse_after_the_last_readout_blocks_the_end(self):
		entry = self.opened()
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		self.at(self.minutes_after(3.5))
		presence.heartbeat(tender=self.name, user=CHAIR)  # the chair's page is alive; the others' stopped at 1.75 minutes
		self.assertEqual(self.case_doc().state, "Interrupted")
		with self.assertRaises(Exception) as refused:
			self.finish()
		self.assertEqual(refused.exception.code, "BOP_VERSION_CONFLICT")

	def test_branch_2_an_unreadable_bid_pauses_until_support_resolves_and_the_chair_retries(self):
		self.started_with_one_bid()
		simulation.set_controls(render_outcome="Unreadable")
		self.at(self.minutes_after(1))
		out = self.open_next()
		self.assertEqual((out["ok"], out["code"]), (False, "BOP_PACKAGE_UNREADABLE"))
		doc = self.case_doc()
		self.assertEqual((doc.state, frappe.db.count("Opening Entry", {"opening_case": doc.name})), ("Interrupted", 0))
		blocked = self.next_step(CHAIR)
		self.assertEqual((blocked["kind"], blocked["headline"]), (ns.KIND_BLOCKED, "This bid could not be opened. Opening access support is checking it; you can retry when they resolve it."))
		self.assertEqual(blocked["fixes"][0]["label"], "View problem details")
		refused = ceremony.retry_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual(refused["reason"], "incident_not_resolved")
		[incident] = incidents.open_incidents(doc.name)
		simulation.set_controls(render_outcome="Render")
		self.at(self.minutes_after(5))
		incidents.record_resolution(tender=self.name, incident=incident.incident_id, resolution_note="Renderer restored.", idempotency_key=key(), user=SUPPORT)
		self.assertEqual(self.next_step(CHAIR)["headline"], "Retry opening")
		self.at(self.minutes_after(5.25))
		retried = ceremony.retry_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertTrue(retried["ok"], retried)
		self.assertEqual(frappe.db.get_value("Opening Entry", {"entry_id": retried["entry"]}, "envelope_id"), frappe.db.get_value("Opening Exception",
			{"opening_case": doc.name, "exception_class": "Package unreadable"}, "envelope_id"))

	def test_support_cannot_fix_it_so_the_accounting_officer_decides(self):
		self.started_with_one_bid()
		simulation.set_controls(render_outcome="Unreadable")
		self.at(self.minutes_after(1))
		self.open_next()
		[incident] = incidents.open_incidents(self.case_doc().name)
		incidents.record_unresolved(tender=self.name, incident=incident.incident_id, resolution_note="The package cannot be rendered.", idempotency_key=key(), user=SUPPORT)
		ao = self.next_step(AO)
		self.assertEqual((ao["kind"], ao["headline"]), (ns.KIND_YOUR_TURN, "Decide how to proceed with the paused opening"))
		self.assertIn(f"Decide how to proceed with the paused opening for {self.reference}", [r["title"] for r in my_work_provider.my_work_rows(AO)["assigned"]])
		self.assertTrue(self.next_step(CHAIR)["headline"].endswith("to resolve the paused opening"))
		with self.assertRaises(Exception):
			self.finish()

	def test_branch_3_a_bid_that_does_not_match_is_never_opened_or_skipped(self):
		self.started_with_one_bid()
		bds_simulation.set_controls(reveal_outcome="Mismatch")
		self.at(self.minutes_after(1))
		out = self.open_next()
		self.assertEqual(out["code"], "BOP_PACKAGE_MISMATCH")
		doc = self.case_doc()
		self.assertEqual((doc.state, frappe.db.count("Opening Entry", {"opening_case": doc.name})), ("Interrupted", 0))
		self.assertEqual(self.next_step(CHAIR)["headline"],
			"Opening is paused while Opening access support checks this bid against the submissions received at the deadline.")

	def test_a_successor_joins_from_resumption_with_a_new_roster_segment(self):
		from kentender_procurement.bid_opening.services import appointment
		from kentender_procurement.tenders.tests import fixtures as tender_fx

		entry = self.opened()
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		presence.leave_opening(tender=self.name, idempotency_key=key(), user=MEMBER)
		roster = [{"user": CHAIR, "committee_role": "Chair and recorder"}, {"user": tender_fx.BOTH, "committee_role": "Member"},
			{"user": INDEPENDENT, "committee_role": "Independent member"}]
		refused = appointment.appoint_opening_committee(tender=self.name, members=roster, expected_version=self.case_version(), idempotency_key=key(), user=AO)
		self.assertEqual(refused["ok"], False)  # a replacement needs its reason
		self.assertTrue(appointment.appoint_opening_committee(tender=self.name, members=roster, reason="The member cannot return.", expected_version=self.case_version(),
			idempotency_key=key(), user=AO)["ok"])
		proceeding = frappe.get_doc("Proceeding", self.case_doc().proceeding)
		self.assertEqual(sorted({m.roster_segment for m in proceeding.members}), [1, 2])
		self.at(self.minutes_after(3))
		for user in (CHAIR, INDEPENDENT):
			presence.heartbeat(tender=self.name, user=user)
			self.join(user)  # a changed roster renews everyone's release
		self.assertEqual(self.case_doc().state, "Interrupted")  # the successor has not joined yet
		self.assertTrue(self.join(tender_fx.BOTH)["resumed"])  # full roster present, release renewed: the opening continues
		self.assertEqual(self.case_doc().state, "Opening")
		with self.assertRaises(Exception) as not_paused:
			ceremony.resume_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual(not_paused.exception.code, "BOP_VERSION_CONFLICT")


class TestCancelledAfterStart(CeremonyCase):
	def test_bop_n18_a_cancellation_after_start_keeps_the_partial_record_and_stops_everything(self):
		entry = self.opened()
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		self.at(self.minutes_after(3))
		closed = cancellation.close_cancelled_opening(tender=self.name, cancellation_reference="TEST-CANCEL-AFTER-START")
		self.assertEqual(closed, cancellation.close_cancelled_opening(tender=self.name, cancellation_reference="TEST-CANCEL-AFTER-START"))
		doc = self.case_doc()
		proceeding = frappe.db.get_value("Proceeding", doc.proceeding, ["state", "actual_start", "ceased_at", "actual_end"], as_dict=True)
		self.assertEqual((doc.state, proceeding.state, str(proceeding.ceased_at), proceeding.actual_end), ("Cancelled after start", "Aborted after start",
			self.minutes_after(3), None))
		self.assertEqual(len(events_of(doc, "ReadoutConfirmed")), 1)
		for fn in (self.open_next, self.finish):
			with self.assertRaises(Exception):
				fn()
		view = reads.get_opening(tender=self.name, user=CHAIR)
		self.assertEqual((view["next_step"]["kind"], view["cancellation"]["message"]), (ns.KIND_NOT_INVOLVED, "Opening ended by Tender cancellation"))
		with self.assertRaises(frappe.DoesNotExistError):
			reads.get_opening(tender=self.name, user=OUTSIDER)


class TestMaterialChecks(CeremonyCase):
	def test_bop_a05_the_opening_cannot_end_while_an_opened_bid_is_not_read_out(self):
		self.opened()
		refused = self.finish()
		self.assertEqual((refused["ok"], refused["code"], refused["missing"]), (False, "BOP_READOUT_INCOMPLETE", 1))
		self.assertEqual(self.case_doc().state, "Opening")

	def test_bop_a02_every_material_act_rechecks_the_whole_roster(self):
		"""Defence in depth (§5): even before an absence has become a recorded pause,
		the next reveal or readout refuses and names the missing member."""
		entry = self.opened()
		frappe.db.set_value("Opening Presence", {"member_user": INDEPENDENT, "state": "Present"}, "state", "Lapsed")  # a disconnect not yet processed
		refused = self.readout(entry)
		self.assertEqual((refused["ok"], refused["code"], refused["message"]), (False, "BOP_MEMBER_ABSENT", "Opening is paused because Test Independent Member is not present."))
		self.assertEqual(frappe.db.get_value("Opening Entry", {"entry_id": entry}, "status"), "Opened")
