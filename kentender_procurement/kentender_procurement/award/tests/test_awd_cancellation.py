# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Cancellation and no award (AWD-CHG-001 v0.4 §5.7; AWD-AC-018; tracker AWD4-803)."""

from __future__ import annotations

from kentender_procurement.award.services import issues, simulation, state, tender_events
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AwardCase

EVENT = {"event_key": "TND-CANCEL:T1", "kind": "Cancellation", "source": "Tenders", "source_reference": "TCN-1", "authority": "amina.hassan@moh.example.test",
	"reason": "The procurement is no longer required.", "effective_at": "2027-06-17 09:30:00"}


class TestCancellation(AwardCase):
	def test_cancel_closes_tasks(self):
		self.deliver()
		self.signed_opinion()
		doc = self.case()
		syn.set_fact(doc.tender, cancelled=True)
		syn.add_event(doc.tender, EVENT)
		self.at("2027-06-17 09:30:00")
		tender_events.consume_case(doc.name)
		doc = self.case()
		self.assertEqual((doc.stage, doc.outcome, doc.cancelled), ("Closed", "Cancelled", 1))
		self.assertEqual(state.cycle(doc).interrupted_stage, "Decision")
		self.assertEqual(state.signed_opinion(doc).state, "Signed")

	def test_unconfirmed_cancellation_does_not_close(self):
		self.deliver()
		doc = self.case()
		syn.add_event(doc.tender, EVENT)  # the event without a confirmed cancelled status
		tender_events.consume_case(doc.name)
		self.assertEqual(self.case().stage, "Opinion")
		simulation.set_controls(status_service_down=1)
		tender_events.consume_case(doc.name)
		self.assertEqual(self.case().stage, "Opinion")

	def test_cancellation_after_notice_is_a_restriction_not_a_close(self):
		self.deliver()
		self.awarded()
		doc = self.case()
		syn.set_fact(doc.tender, cancelled=True)
		syn.add_event(doc.tender, EVENT)
		tender_events.consume_case(doc.name)
		doc = self.case()
		self.assertEqual(doc.stage, "Waiting to proceed")
		self.assertEqual(issues.open_issues(doc, subtype="Cancellation after notification")[0].title, "This award is on hold.")

	def test_suspension_event_is_an_authoritative_hold(self):
		self.deliver()
		self.awarded()
		doc = self.case()
		syn.add_event(doc.tender, {"event_key": "SUSP-1", "kind": "Suspension", "authority": "Review Board", "source_reference": "PPARB/2027/33",
			"reason": "Review Board suspension", "effective_at": "2027-06-20 11:00:00"})
		tender_events.consume_case(doc.name)
		tender_events.consume_case(doc.name)
		found = issues.open_issues(self.case(), issue_type="Review/order")
		self.assertEqual((len(found), found[0].basis), (1, "Authoritative order"))
