# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.16 §5.2, §7.2, §10.8 (BOP-OF-AC-006, AC-007, AC-008) and PRC-CHG-001 v0.14 §5.1, §7.2 against REAL Tenders cancellation: the existing
`TenderCancelled` event reaches Bid Opening through the Tenders delivery ledger.

Authoritative cancellation denies every ceremony command at once — before the opening record has caught up. Before Start the case ends Not held, once; after
Start it ends Cancelled after start with every actual event kept, nothing finalised or handed to Evaluation. A case already Not held has the cancellation
attached, with no second decision item and no invented closed manifest. A duplicate, replayed or out-of-order delivery creates nothing new; a failed
delivery is kept and retried from the same event; and the Accounting Officer's exact item clears only when the BOP/PRC terminal outcome commits."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import ceremony, cancellation_consumer, incidents, interventions, not_held, presence, reads, records, simulation
from kentender_procurement.bid_opening.services.errors import BidOpeningError
from kentender_procurement.bid_opening.tests.support import AO, CHAIR, INDEPENDENT, MEMBER, SUPPORT
from kentender_procurement.bid_opening.tests.test_bop_ceremony import CeremonyCase, events_of
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.tenders.services import cancellation as tender_cancellation
from kentender_procurement.tenders.services import cancellation_delivery
from kentender_procurement.tenders.test_services import ground_verifier

REASON = "The confirmed budget available for this procurement is insufficient to proceed."
PENDING = "Cancellation recorded. The opening record is being updated."
ENDED = "This tender was cancelled. Opening ended."


class CancelCase(CeremonyCase):
	def setUp(self):
		super().setUp()
		ground_verifier.reset_controls()
		self.addCleanup(ground_verifier.reset_controls)
		# delivery runs only when a test says so, so the instant between "committed" and "delivered" can be examined
		patcher = mock.patch.object(cancellation_delivery, "after_commit")
		patcher.start()
		self.addCleanup(patcher.stop)

	def cancel_tender(self, *, post_close: bool = True):
		if post_close:
			ground_verifier.set_controls(verified_cancellation_grounds="INADEQUATE_BUDGET")
		root = frappe.get_doc("Tender", self.name)
		return tender_cancellation.cancel_tender(tender=self.name, ground="INADEQUATE_BUDGET", reason=REASON, expected_record_version=root.record_version,
			idempotency_key=key(), user=AO)

	def deliver(self) -> dict:
		return cancellation_delivery.run(tender=self.name)

	def items(self, status: str | None = None) -> list:
		filters = {"opening_case": self.case_doc().name}
		if status:
			filters["status"] = status
		return frappe.get_all(not_held.DECISION, filters=filters, fields=["name", "kind", "status", "clearing_event", "cleared_at"])

	def counts(self) -> dict:
		doc = self.case_doc()
		return {"events": frappe.db.count("Proceeding Event", {"proceeding": doc.proceeding}), "entries": frappe.db.count("Opening Entry", {"opening_case": doc.name}),
			"journal": frappe.db.count("Opening Command Journal", {"opening_case": doc.name})}

	def unreadable_then_escalated(self):
		"""The paused opening that support cannot recover: the Accounting Officer's item is open."""
		self.started_with_one_bid()
		simulation.set_controls(render_outcome="Unreadable")
		self.at(self.minutes_after(1))
		self.open_next()
		[incident] = incidents.open_incidents(self.case_doc().name)
		incidents.record_unresolved(tender=self.name, incident=incident.incident_id, resolution_note="The package cannot be rendered.", idempotency_key=key(), user=SUPPORT)
		self.assertEqual([i["status"] for i in self.items()], ["Open"])


class TestImmediateDenial(CancelCase):
	def test_every_ceremony_command_is_refused_the_moment_the_cancellation_commits(self):
		entry = self.opened()
		self.at(self.minutes_after(1.5))
		self.cancel_tender()
		self.assertEqual(self.case_doc().state, "Opening")  # Bid Opening has not caught up: the denial does not wait for it
		before = self.counts()
		attempts = {
			"read out": lambda: self.readout(entry),
			"open next": self.open_next,
			"finish": self.finish,
			"begin": self.begin,
			"resume": lambda: ceremony.resume_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR),
			"join": lambda: presence.join_opening(tender=self.name, idempotency_key=key(), user=MEMBER),
			"attendance": lambda: interventions.record_attendance(tender=self.name, person_name="Test Attendee", capacity="Tenderer representative", movement="Arrival",
				represented_tenderer="Example Test Supplier Ltd", idempotency_key=key(), user=CHAIR),
		}
		for label, attempt in attempts.items():
			with self.assertRaises(BidOpeningError, msg=label) as ctx:
				attempt()
			self.assertEqual((ctx.exception.code, str(ctx.exception)), ("BOP_TENDER_CANCELLED", PENDING), label)
		self.assertEqual(self.counts(), before)  # nothing was written, not even a journal row
		view = reads.get_opening(tender=self.name, user=CHAIR)
		self.assertEqual((view["cancellation"]["state"], view["cancellation"]["message"]), ("Recorded", PENDING))
		self.assertEqual(view["next_step"]["headline"], PENDING)
		self.assertEqual(view["next_step"]["kind"], ns.KIND_NOT_INVOLVED)
		# once the closure commits, the words become the terminal ones
		self.deliver()
		with self.assertRaises(BidOpeningError) as terminal:
			self.open_next()
		self.assertEqual((terminal.exception.code, str(terminal.exception)), ("BOP_TENDER_CANCELLED", ENDED))
		self.assertEqual(reads.get_opening(tender=self.name, user=CHAIR)["cancellation"]["message"], ENDED)

	def test_the_commands_that_must_still_work_are_not_refused(self):
		"""The consumption itself, the support finding and the incident reads continue: the denial is for the ceremony."""
		self.unreadable_then_escalated()
		self.cancel_tender()
		[incident] = [i for i in frappe.get_all(incidents.INCIDENT, filters={"opening_case": self.case_doc().name}, fields=["incident_id"])]
		self.assertTrue(cancellation_consumer.deliver(tender=self.name, cancellation=frappe.db.get_value("Tender", self.name, "cancellation"), event_id="x", payload={})["receipt"])
		self.assertIsNotNone(incident)


class TestConsumption(CancelCase):
	def test_after_start_the_partial_record_is_closed_once_and_nothing_goes_to_evaluation(self):
		entry = self.opened()
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		self.at(self.minutes_after(3))
		result = self.cancel_tender()
		decided = frappe.db.get_value("Tender Cancellation", result["cancellation"], "decided_at")
		self.at(self.minutes_after(9))  # delivery runs later than the decision
		self.assertEqual(self.deliver(), {"delivered": 1, "failed": 0})
		doc = self.case_doc()
		proceeding = frappe.db.get_value("Proceeding", doc.proceeding, ["state", "actual_start", "ceased_at", "actual_end", "cancellation_reference", "cancellation_source_at",
			"cancellation_received_at"], as_dict=True)
		self.assertEqual((doc.state, proceeding.state, proceeding.cancellation_reference), ("Cancelled after start", "Aborted after start", result["cancellation"]))
		self.assertEqual((str(proceeding.ceased_at), str(proceeding.cancellation_source_at), str(proceeding.cancellation_received_at)), (str(decided), str(decided), self.minutes_after(9)))
		self.assertIsNone(proceeding.actual_end)  # never a normal end, never a fabricated one
		self.assertEqual(len(events_of(doc, "ReadoutConfirmed")), 1)  # the actual partial chronology is kept
		self.assertEqual(frappe.db.count("Evaluation Handoff", {"opening_case": doc.name}), 0)
		self.assertEqual(frappe.db.count("Proceeding Minutes Version", {"proceeding": doc.proceeding}), 0)
		# a duplicate delivery (the ledger row is delivered, the consumer asked again) creates nothing new
		before = self.counts()
		again = cancellation_consumer.deliver(tender=self.name, cancellation=result["cancellation"], event_id="dup", payload={})
		self.assertEqual(again["receipt"], f"Cancelled after start:{result['cancellation']}")
		self.assertEqual(self.counts(), before)
		self.assertEqual(frappe.db.count("Proceeding Event", {"proceeding": doc.proceeding, "event_type": "ProceedingAborted"}), 1)

	def test_before_start_the_case_is_not_held_once_with_no_decision_item_and_no_invented_manifest(self):
		self.prepare_case()
		self.at(self.minutes_before(30))  # still open for submission
		result = self.cancel_tender(post_close=False)
		self.assertEqual(self.deliver(), {"delivered": 1, "failed": 0})
		doc = self.case_doc()
		proceeding = frappe.db.get_value("Proceeding", doc.proceeding, ["state", "cancellation_reference", "custody_reference"], as_dict=True)
		self.assertEqual((doc.state, proceeding.state, proceeding.cancellation_reference), ("Not held", "Not held", result["cancellation"]))
		self.assertFalse(doc.manifest_handoff)  # no closed manifest existed, and none was fabricated
		self.assertFalse(proceeding.custody_reference)
		self.assertEqual(self.items(), [])  # a cancellation before Start creates no AO decision item
		before = self.counts()
		cancellation_consumer.deliver(tender=self.name, cancellation=result["cancellation"], event_id="dup", payload={})
		self.assertEqual(self.counts(), before)
		self.assertEqual(frappe.db.count("Proceeding Event", {"proceeding": doc.proceeding, "event_type": "ProceedingNotHeld"}), 1)

	def test_not_held_then_cancelled_attaches_the_cancellation_and_clears_the_exact_item_once(self):
		"""OF-F03: the opening never started; the Accounting Officer recorded Not held and holds the decision item; a lawful cancellation then arrives."""
		self.ready_to_open()
		simulation.set_controls(attendance_service_down=1)
		self.at(self.minutes_after(15))
		recorded = not_held.record_opening_not_held(tender=self.name, reason="The public attendance service failed and the opening did not start.", expected_version=self.case_version(),
			idempotency_key=key(), user=AO)
		self.assertTrue(recorded["ok"], recorded)
		[item] = self.items("Open")
		self.assertEqual(item["kind"], "Not held")
		manifest = self.case_doc().manifest_handoff
		self.assertEqual(self.case_doc().state, "Not held")
		# the decision screen's read and a page view change nothing
		reads.get_opening(tender=self.name, user=AO)
		self.assertEqual([i["status"] for i in self.items()], ["Open"])
		result = self.cancel_tender()
		self.at(self.minutes_after(40))
		self.assertEqual(self.deliver(), {"delivered": 1, "failed": 0})
		doc = self.case_doc()
		proceeding = frappe.db.get_value("Proceeding", doc.proceeding, ["state", "not_held_reason", "cancellation_reference", "cancellation_received_at", "actual_start"], as_dict=True)
		self.assertEqual((doc.state, proceeding.state, proceeding.cancellation_reference, proceeding.actual_start), ("Not held", "Not held", result["cancellation"], None))
		self.assertIn("attendance service failed", proceeding.not_held_reason)  # the factual reason stands
		self.assertEqual(doc.manifest_handoff, manifest)  # unchanged: no manifest created or replaced
		[cleared] = self.items()  # still one item, now cleared by the committed outcome, not duplicated
		self.assertEqual((cleared["name"], cleared["status"]), (item["name"], "Cleared"))
		self.assertTrue(cleared["clearing_event"] and cleared["cleared_at"])
		self.assertEqual(frappe.db.count("Proceeding Event", {"proceeding": doc.proceeding, "event_type": "ProceedingCancellationReceived"}), 1)
		before = self.counts()
		cancellation_consumer.deliver(tender=self.name, cancellation=result["cancellation"], event_id="dup", payload={})
		self.assertEqual(self.counts(), before)
		self.assertEqual(len(self.items()), 1)

	def test_an_unresolved_paused_opening_item_clears_only_when_the_terminal_outcome_commits(self):
		self.unreadable_then_escalated()
		self.cancel_tender()
		# the cancellation is committed and the page is read, but the closure has not been delivered: the item stays open
		self.assertEqual(reads.get_opening(tender=self.name, user=AO)["cancellation"]["state"], "Recorded")
		self.assertEqual([i["status"] for i in self.items()], ["Open"])
		self.assertEqual(self.case_doc().state, "Interrupted")
		self.deliver()
		self.assertEqual(self.case_doc().state, "Cancelled after start")
		[item] = self.items()
		self.assertEqual(item["status"], "Cleared")
		self.assertTrue(item["clearing_event"])

	def test_a_failed_delivery_denies_the_ceremony_keeps_the_item_open_and_is_retried_from_the_same_event(self):
		self.unreadable_then_escalated()
		result = self.cancel_tender()
		from kentender_procurement.proceedings.services import lifecycle

		with mock.patch.object(lifecycle, "close_aborted", side_effect=RuntimeError("Proceedings is down")):
			self.assertEqual(self.deliver(), {"delivered": 0, "failed": 1})
		row = frappe.get_doc("Tender Event Delivery", {"tender": self.name})
		self.assertEqual((row.status, row.attempts), ("Failed", 1))
		self.assertEqual((self.case_doc().state, [i["status"] for i in self.items()]), ("Interrupted", ["Open"]))  # nothing half-closed
		with self.assertRaises(BidOpeningError) as ctx:  # authoritative cancellation already denies the ceremony
			ceremony.resume_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual(ctx.exception.code, "BOP_TENDER_CANCELLED")
		self.assertEqual(self.deliver(), {"delivered": 1, "failed": 0})
		self.assertEqual((self.case_doc().state, [i["status"] for i in self.items()]), ("Cancelled after start", ["Cleared"]))
		self.assertEqual(frappe.get_doc("Tender Event Delivery", {"tender": self.name}).event_id, row.event_id)
		self.assertEqual(frappe.db.get_value("Proceeding", self.case_doc().proceeding, "cancellation_reference"), result["cancellation"])

	def test_a_reference_that_is_not_the_tenders_cancellation_is_refused_and_changes_nothing(self):
		self.unreadable_then_escalated()
		self.cancel_tender()
		before = self.counts()
		for wrong in ("TCN-NOT-THIS-TENDERS", ""):
			with self.assertRaises(Exception):
				cancellation_consumer.deliver(tender=self.name, cancellation=wrong, event_id="x", payload={})
		self.assertEqual(self.counts(), before)
		self.assertEqual(self.case_doc().state, "Interrupted")

	def test_a_tender_that_was_never_cancelled_cannot_be_closed_by_assertion(self):
		self.started_with_one_bid()
		with self.assertRaises(Exception):
			cancellation_consumer.deliver(tender=self.name, cancellation="TCN-FABRICATED", event_id="x", payload={})
		self.assertEqual(self.case_doc().state, "Opening")

	def test_the_scheduler_sweep_delivers_the_same_event_when_the_request_died_first(self):
		from kentender_procurement.bid_opening.services import sweep

		self.unreadable_then_escalated()
		self.cancel_tender()
		sweep.sweep_tender(self.name)
		self.assertEqual(self.case_doc().state, "Cancelled after start")
		self.assertEqual(frappe.db.get_value("Tender Event Delivery", {"tender": self.name}, "status"), "Delivered")
		before = self.counts()
		sweep.sweep_tender(self.name)
		self.assertEqual(self.counts(), before)

	def test_the_sweep_gives_a_tender_cancelled_before_the_ledger_existed_its_rows_and_closes_it(self):
		from kentender_procurement.bid_opening.services import sweep

		self.unreadable_then_escalated()
		self.cancel_tender()
		frappe.db.delete("Tender Event Delivery", {"tender": self.name})  # as if cancelled before the ledger existed
		sweep.sweep_tender(self.name)
		self.assertEqual(self.case_doc().state, "Cancelled after start")
		self.assertEqual(frappe.db.count("Tender Event Delivery", {"tender": self.name}), 1)
