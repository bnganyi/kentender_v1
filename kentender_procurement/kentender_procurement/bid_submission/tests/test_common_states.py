# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.17 BDS-DES-16 and §11.5 View status (plan Phase 11,
slice 11.15): the one common-state catalogue holds the §8 message of every
code it answers to as its heading; View status reads the latest attempt —
pending, rejected, accepted — or the submission service, and never
dispatches; the Submit page gives way to Deadline passed for a bid that was
not submitted in time."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission import portal
from kentender_procurement.bid_submission.services import common_states, reads, simulation, status_view
from kentender_procurement.bid_submission.services.errors import MESSAGES
from kentender_procurement.bid_submission.tests.support import MARY, PETER
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


class TestCatalogue(SubmissionCase):
	def test_every_coded_state_carries_its_section_8_message_as_its_heading(self):
		catalogue = common_states.catalogue()
		coded = {key: entry for key, entry in catalogue.items() if entry.get("code")}
		self.assertTrue(coded)
		for key, entry in coded.items():
			with self.subTest(state=key):
				self.assertEqual(MESSAGES[entry["code"]], entry["heading"])
		self.assertEqual(common_states.for_code("BDS_SUBMISSION_UNCERTAIN"), "confirmation-pending")
		self.assertEqual(common_states.for_code("BDS_NOT_A_CODE"), "")
		self.assertEqual(common_states.state("custody-rejected", retry=True)["retry"], True)
		self.assertEqual(common_states.state("stale-draft", retry=True)["retry"], False)  # no retry action


class TestViewStatus(SubmissionCase):
	def status(self, user=MARY):
		return status_view.get_status_page(tender_reference=self.reference, user=user)

	def test_each_attempt_outcome_is_one_state_and_reading_dispatches_nothing(self):
		base = f"/tenders/{self.reference}/bid"
		self.assertEqual(self.status()["state"]["key"], "not-submitted")
		simulation.set_controls(gate_closed=1)
		self.assertEqual(self.status()["state"]["key"], "production-not-enabled")
		simulation.set_controls(gate_closed=0, custody_service_down=1)
		self.assertEqual(self.status()["state"]["key"], "submission-unavailable")
		simulation.reset_controls()

		simulation.set_controls(deposit_outcome="Reject", rejection_reference="TBX-REJECT-033-01")
		self.assertEqual(self.submit(self.signed())["code"], "BDS_CUSTODY_REJECTED")
		rejected = self.status()["state"]
		self.assertEqual((rejected["key"], rejected["retry"], rejected["href"], rejected["figures"]["rejection_reference"]), ("custody-rejected", True, f"{base}/submit", "TBX-REJECT-033-01"))

		simulation.set_controls(deposit_outcome="Uncertain")
		pending = self.submit(self.signed())
		attempts = frappe.db.count("Bid Submission Attempt", {"bid_workspace": self.bid})
		state = self.status()["state"]
		self.assertEqual((state["key"], state["figures"]["correlation_id"], state["href"]), ("confirmation-pending", pending["correlation_id"], f"{base}/status"))
		self.assertEqual(frappe.db.count("Bid Submission Attempt", {"bid_workspace": self.bid}), attempts)  # a read never dispatches

		simulation.set_controls(uncertain_resolution="Accept")
		from kentender_procurement.bid_submission.services import submission

		submission.reconcile_uncertain_attempts()
		simulation.reset_controls()
		accepted = self.status()
		receipt = frappe.db.get_value("Bid Submission Version", frappe.db.get_value("Bid Workspace", self.bid, "current_submission_version"), "receipt")
		self.assertEqual((accepted["state"], accepted["redirect"]), (None, f"{base}/receipt/{receipt}"))
		self.assertEqual(portal.resolve(path=f"{base}/status", query={}, user=MARY)["redirect"], f"{base}/receipt/{receipt}")
		self.assertEqual(portal.resolve(path=f"{base}/status", query={}, user=PETER)["verdict"], "NOT_FOUND")

	def test_after_the_deadline_an_unsubmitted_bid_reads_deadline_passed(self):
		self.at(frappe.utils.add_to_date(self.deadline(), seconds=1))
		self.assertEqual(self.status()["state"]["key"], "deadline-passed")
		page = reads.get_submit_page(tender_reference=self.reference, user=MARY)
		self.assertEqual((page["state"]["key"], page["state"]["href"]), ("deadline-passed", "/my-bids"))
		self.assertTrue(page["state"]["figures"]["current_time"].endswith(" EAT"))
