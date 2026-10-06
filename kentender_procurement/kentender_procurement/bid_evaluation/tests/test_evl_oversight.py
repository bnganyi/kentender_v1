# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Oversight reads of Bid Evaluation (OVS-CHG-001 v0.6 §4, §4.1, §7, §13, §15;
plan D1, D2, D16; tracker OVS6-0201 to OVS6-0211; acceptance OVS-AC-004 to
OVS-AC-007, OVS-AC-009, OVS-AC-011, OVS-AC-017).

The Accounting Officer and the Head of Procurement Function see status only
until a report version is delivered, and every delivered version, read-only,
afterwards. They never see the live case, a version being signed, or a
correction being prepared. A Head of User Department whose unit contributed
to the Tender sees a department-level summary and nothing of the bids. The
committee, the secretary and the recipient keep what they had.

The disclosure is driven through every read the API offers, as the real
personas, so a missed route cannot pass."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.bid_evaluation.services import appointment, correction, my_work_provider, next_steps, reads, report, signing  # noqa: F401
from kentender_procurement.bid_evaluation.tests.support import AO, AUDITOR, CHAIR, HOP, MEMBER, MEMBER_2, OUTSIDER, SECRETARY
from kentender_procurement.bid_evaluation.tests.test_evl_report import MEMBERS, ReportCase
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx

BIDDER = "Afya Digital Supplies Limited"
HOD = req_fx.HOD  # Head of User Department in the contributing unit
HOD_OTHER = req_fx.HOD_BETA  # Head of User Department in a unit that never contributed


def dump(value) -> str:
	return json.dumps(value, default=str)


class OversightCase(ReportCase):
	def resolve(self, user):
		return reads.resolve(tender_reference=self.reference, user=user)

	def report(self, user, version=""):
		return reads.report_view(tender_reference=self.reference, user=user, version=version)

	def record(self, user):
		return reads.committee_record(tender_reference=self.reference, user=user)

	def deliver(self):
		self.evl_ready()
		self.evl_freeze()
		for user in MEMBERS:
			self.evl_sign(user)
		self.assertEqual(self.evl_doc().state, "Report sent")

	def not_found(self, fn, *args, **kwargs):
		with self.assertRaises(frappe.DoesNotExistError):
			fn(*args, **kwargs)

	def assert_status_only(self, user):
		"""Nothing of the bids reaches the reader, through any read."""
		view = self.resolve(user)
		for forbidden in ("comparison", "attention", "outcome", "delivered_report", "department_summary"):
			self.assertNotIn(forbidden, view, f"{user}: {forbidden}")
		self.assertNotIn(BIDDER, dump(view), user)
		self.assertNotIn(BIDDER, dump(self.record(user)), user)
		self.assertNotIn(BIDDER, dump(my_work_provider.my_work_rows(user)), user)
		self.not_found(self.report, user)
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")
		self.not_found(reads.bid, tender_reference=self.reference, bid=bid, user=user)


class TestStatusOnlyBeforeDelivery(OversightCase):
	def test_the_accounting_officer_sees_status_only_while_reviewing_and_signing(self):
		self.assert_status_only(AO)
		self.evl_ready()
		self.evl_freeze()  # a version in Signing is frozen but not delivered
		self.assertEqual(self.evl_doc().state, "Signing")
		self.assert_status_only(AO)
		signing_version = signing.signing_version(self.evl_doc()).name
		self.not_found(self.report, AO, version=signing_version)
		self.assertFalse(reads.access(self.evl_doc(), AO)["oversight_full"])

	def test_the_head_before_delivery_is_not_given_the_version_being_signed(self):
		self.evl_ready()
		self.evl_freeze()
		# the recipient-to-be reads setup only until a report is delivered
		self.not_found(self.report, HOP)
		self.assertNotIn(BIDDER, dump(self.resolve(HOP)))

	def test_a_department_head_sees_no_bids_before_delivery(self):
		view = self.resolve(HOD)
		self.assertEqual(view["department_summary"], {})
		self.assertNotIn(BIDDER, dump(view))
		self.assertNotIn("comparison", view)
		self.not_found(self.report, HOD)
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")
		self.not_found(reads.bid, tender_reference=self.reference, bid=bid, user=HOD)
		self.assertNotIn("declaration", dump(view["committee"]["members"]))  # no member's declaration reaches a department

	def test_a_technical_reader_sees_status_only_before_delivery(self):
		view = self.resolve("Administrator")
		self.assertEqual(set(view) & {"comparison", "committee", "source", "delivered_report"}, set())
		self.assertNotIn(BIDDER, dump(view))
		self.not_found(self.report, "Administrator")

	def test_a_department_head_of_another_unit_and_an_outsider_get_not_found(self):
		self.not_found(self.resolve, HOD_OTHER)
		self.not_found(self.resolve, OUTSIDER)
		self.assertEqual([r for r in reads.list_work(user=HOD_OTHER)["register"]], [])


class TestAfterDelivery(OversightCase):
	def setUp(self):
		super().setUp()
		self.deliver()

	def test_the_accounting_officer_reads_the_decision_and_the_report(self):
		view = self.resolve(AO)
		self.assertTrue(view["viewer"]["oversight_full"])
		decision = view["delivered_report"]
		self.assertEqual(decision["recommendation"]["outcome"], "Recommendation")
		self.assertEqual(decision["recommendation"]["recommended"]["bidder"], BIDDER)
		self.assertIn("This report does not constitute an award.", decision["recommendation"]["statement"])
		self.assertEqual(decision["comparison"]["rows"][0]["bidder"], BIDDER)
		self.assertEqual(decision["version_number"], 1)
		# the live case is not on the payload: only the frozen version
		for live in ("comparison", "attention", "outcome"):
			self.assertNotIn(live, view)
		doc = self.report(AO)
		self.assertFalse(doc["live"])
		self.assertEqual(doc["report_state"], "Delivered")
		self.assertEqual(doc["content"]["recommendation"]["recommended"]["bidder"], BIDDER)
		self.assertEqual(len(doc["signatures"]), 3)
		self.assertTrue(all(s["signed"] for s in doc["signatures"]))
		record = self.record(AO)
		self.assertTrue(record["clarifications"] or record["sessions"] is not None)
		self.assertIn("sessions", record)

	def test_the_done_line_offers_to_open_the_report_to_the_two_offices_only(self):
		for user in (AO, HOP):
			answer = next_steps.answer(self.evl_doc(), user)
			self.assertEqual(answer["kind"], "done", user)
			self.assertEqual(answer["primary_action"], "view_report", user)
			self.assertIn("The committee report was sent to", answer["headline"])
		for user in (CHAIR, MEMBER, AUDITOR):
			self.assertEqual(next_steps.answer(self.evl_doc(), user)["primary_action"], "", user)  # the committee's Done carries no action

	def test_a_head_who_is_not_the_recipient_reads_the_same(self):
		name = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": self.case}, "name")
		frappe.db.set_value("Evaluation Report Delivery", name, "recipient_user", AO)  # the AO is now the recipient
		view = self.resolve(HOP)
		self.assertTrue(view["viewer"]["oversight_full"])
		self.assertEqual(view["delivered_report"]["recommendation"]["recommended"]["bidder"], BIDDER)
		self.assertEqual(self.report(HOP)["content"]["recommendation"]["outcome"], "Recommendation")

	def test_a_technical_reader_reads_the_delivered_report_and_nothing_of_the_bids(self):
		# OVS-P05 and EVL-CHG-001 v0.5 section 9.10: the delivered report, read-only; sealed bids and their documents never
		view = self.resolve("Administrator")
		self.assertEqual(view["delivered_report"]["recommendation"]["recommended"]["bidder"], BIDDER)
		self.assertEqual(view["guidance"]["primary_action"], "")  # a technical reader is given no action
		self.assertEqual(self.report("Administrator")["content"]["recommendation"]["outcome"], "Recommendation")
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")
		self.not_found(reads.bid, tender_reference=self.reference, bid=bid, user="Administrator")
		self.not_found(reads.evidence, tender_reference=self.reference, bid=bid, digest="0" * 64, user="Administrator")
		self.not_found(reads.delivered_bid, tender_reference=self.reference, bid=bid, user="Administrator")

	def test_oversight_grants_no_bid_level_read_and_no_command(self):
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")
		for user in (AO, HOP):
			self.not_found(reads.bid, tender_reference=self.reference, bid=bid, user=user)  # the bid detail is a later slice (plan D16, part B)
			access = reads.access(self.evl_doc(), user)
			self.assertFalse(access["bids"], user)
			self.assertFalse(access["secretary"] or access["chair"] or access["member"], user)
			self.assertFalse(self.resolve(user)["viewer"]["bids"], user)

	def test_the_committee_the_secretary_and_the_auditor_keep_their_access(self):
		for user in (CHAIR, MEMBER, MEMBER_2, SECRETARY, AUDITOR):
			self.assertEqual(self.resolve(user)["comparison"]["rows"][0]["bidder"], BIDDER, user)
			self.assertEqual(self.report(user)["content"]["recommendation"]["outcome"], "Recommendation", user)
		self.not_found(self.resolve, OUTSIDER)
		self.not_found(self.report, OUTSIDER)

	def test_the_register_shows_the_outcome_only_after_delivery(self):
		for user in (AO, HOP, AUDITOR, MEMBER):
			row = next(r for r in reads.list_work(user=user)["register"] if r["tender"] == self.reference)
			self.assertEqual(row["outcome"], "Recommendation", user)
		self.assertEqual(reads.list_work(user=OUTSIDER)["register"], [])

	def test_a_department_head_reads_a_summary_and_never_the_bids(self):
		view = self.resolve(HOD)
		summary = view["department_summary"]
		self.assertEqual(summary["outcome"], "Recommendation")
		self.assertEqual(summary["recommended_bidder"], BIDDER)
		self.assertEqual(summary["version_number"], 1)
		self.assertIn("reason", summary)
		self.assertFalse(summary["validity_expired"])
		for forbidden in ("comparison", "attention", "delivered_report", "work"):
			self.assertNotIn(forbidden, view)
		self.not_found(self.report, HOD)  # no full report
		self.not_found(self.record, HOD)  # nor the committee record
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")
		self.not_found(reads.bid, tender_reference=self.reference, bid=bid, user=HOD)
		self.not_found(self.resolve, HOD_OTHER)

	def test_reading_creates_no_task_and_no_event(self):
		before = frappe.db.count("Evaluation Source Event", {"evaluation_case": self.case}), frappe.db.count("Notification Log")
		for user in (AO, HOP):
			self.resolve(user)
			self.report(user)
			self.record(user)
			reads.list_work(user=user)
		self.assertEqual((frappe.db.count("Evaluation Source Event", {"evaluation_case": self.case}), frappe.db.count("Notification Log")), before)


class TestEdgesAndRevocation(OversightCase):
	def test_a_cancellation_before_delivery_shows_the_facts_and_no_partial_findings(self):
		from kentender_procurement.bid_evaluation.services import tender_events

		tender_events.record_simulated_event(tender=self.name, kind="Cancellation", instruction_reference="MOH/CANCEL/TEST", authority=AO,
			reason="Procurement proceedings terminated under the recorded decision.")
		self.assertEqual(self.evl_doc().state, "Cancelled")
		for user in (AO, HOP):
			self.assert_status_only(user)
			events = self.resolve(user)["work"]["owner_events"]
			self.assertEqual([e["kind"] for e in events], ["Cancellation"], user)
			self.assertEqual(events[0]["instruction_reference"], "MOH/CANCEL/TEST", user)

	def test_a_report_with_no_current_recommendation_implies_no_winner(self):
		self.deliver()
		version = frappe.get_doc("Evaluation Report Version", self.first_version_name())
		content = json.loads(version.content_json)
		content["recommendation"].update(outcome=report.EXPIRED, recommended=None, reason="Tender validity has expired.")
		content["summary"].update(outcome=report.EXPIRED, recommendation=report.EXPIRED, evaluated_total="")
		frappe.db.set_value("Evaluation Report Version", version.name, "content_json", json.dumps(content))
		decision = self.resolve(AO)["delivered_report"]
		self.assertEqual(decision["recommendation"]["outcome"], report.EXPIRED)
		self.assertIsNone(decision["recommendation"]["recommended"])
		summary = self.resolve(HOD)["department_summary"]
		self.assertTrue(summary["validity_expired"])
		self.assertEqual((summary["recommended_bidder"], summary["evaluated_total"]), ("", ""))
		self.assertNotIn("Recommendation", [f["label"] for f in self.stage(AO)["facts"]])

	def test_a_revoked_responsibility_stops_reading_at_once_and_a_regrant_restores_it(self):
		from kentender_core.services import responsibility_administration as administration

		self.deliver()
		self.assertTrue(self.resolve(AO)["delivered_report"])
		row = frappe.db.get_value("User Responsibility Assignment", {"user": AO, "business_role": "Accounting Officer", "status": "Enabled"},
			["name", "fixture_namespace"], as_dict=True)
		administration.revoke(row.name, reason="Test: the office holder was reassigned.", actor="Administrator")
		try:
			self.not_found(self.resolve, AO)
			self.not_found(self.report, AO)
			self.not_found(reads.delivered_bid, tender_reference=self.reference, bid=frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name"), user=AO)
			self.assertEqual(reads.list_work(user=AO)["register"], [])
		finally:
			administration.grant(user=AO, business_role="Accounting Officer", fixture_namespace=row.fixture_namespace, actor="Administrator")
		self.assertTrue(self.resolve(AO)["delivered_report"])

	def first_version_name(self) -> str:
		return frappe.db.get_value("Evaluation Report Version", {"evaluation_case": self.case, "version_number": 1}, "name")

	def stage(self, user) -> dict:
		from kentender_procurement.tenders.services import read as tender_read

		return next(s for s in tender_read.get_tender(tender=self.reference, user=user)["stage_summaries"] if s["key"] == "bid-evaluation")


class TestReturnAndCorrection(OversightCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.first = frappe.db.get_value("Evaluation Report Version", {"evaluation_case": self.case, "version_number": 1}, "name")

	def test_a_return_keeps_the_delivered_version_and_hides_the_correction(self):
		correction.return_report(tender=self.name, comment="Correct the service-address page reference from page 3 to page 2.", idempotency_key=key(), user=HOP)
		self.assertEqual(self.evl_doc().state, "Reviewing")
		for user in (AO, HOP):
			view = self.resolve(user)
			self.assertEqual(view["delivered_report"]["report"], self.first, user)
			self.assertEqual(view["delivered_report"]["report_state"], "Returned", user)
			self.assertEqual(view["delivered_report"]["correction"]["headline"], "A corrected report is being prepared.", user)
			self.assertIn("page 3 to page 2", view["delivered_report"]["correction"]["reason"], user)
			self.assertEqual(self.report(user)["report"], self.first, user)
			for live in ("comparison", "attention", "outcome"):
				self.assertNotIn(live, view)
		# the next version is frozen and out for signature: still not theirs to read
		self.evl_freeze()
		corrected = signing.signing_version(self.evl_doc()).name
		self.assertNotEqual(corrected, self.first)
		for user in (AO, HOP):
			self.assertEqual(self.report(user)["report"], self.first, user)
			self.assertEqual([h["name"] for h in self.report(user)["history"]], [self.first], user)
			self.not_found(self.report, user, version=corrected)
		self.assertEqual(self.resolve(HOD)["department_summary"]["correction"]["returned"], True)

	def test_a_corrected_report_becomes_current_and_keeps_the_earlier_version(self):
		correction.return_report(tender=self.name, comment="Correct the service-address page reference from page 3 to page 2.", idempotency_key=key(), user=HOP)
		self.evl_freeze()
		for user in MEMBERS:
			self.evl_sign(user)
		second = frappe.db.get_value("Evaluation Report Version", {"evaluation_case": self.case, "version_number": 2}, "name")
		for user in (AO, HOP):
			view = self.resolve(user)
			self.assertEqual(view["delivered_report"]["report"], second, user)
			self.assertIsNone(view["delivered_report"]["correction"], user)
			self.assertEqual({v["version_number"] for v in view["delivered_report"]["versions"]}, {1, 2}, user)
			self.assertEqual(self.report(user, version=self.first)["report"], self.first, user)  # the earlier version stays readable
			self.assertEqual(self.report(user)["report"], second, user)
