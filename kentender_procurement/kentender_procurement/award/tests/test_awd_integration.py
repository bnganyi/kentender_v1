# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The real Evaluation → Award hand-off, end to end (AWD-CHG-001 v0.4 §3,
§5.3, §5.7; AWD-AC-001, AC-006; plan rule 11; tracker AWD4-208).

One real Evaluation world per module (Evaluation's own shared test world:
the Tender, bid and opening are built once, years ≥ 2100): the committee
signs, Evaluation delivers, and Award receives — one case, one Head of
Procurement task, Evaluation's review row taken up; a retry changes nothing;
Award's Return report goes back through Evaluation's own return."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import intake, opinion, profile, records, sources, state, tasks
from kentender_procurement.bid_evaluation.services import report, signing
from kentender_procurement.bid_evaluation.tests.support import CHAIR, HOP, MEMBER, MEMBER_2, SECRETARY
from kentender_procurement.bid_evaluation.tests.test_evl_report import ReportCase, titles
from kentender_procurement.bid_submission.tests.support import key


class TestRealHandoff(ReportCase):
	def setUp(self):
		super().setUp()
		if frappe.conf.get("kt_bds_simulation_environment"):
			profile.install_test_profile(contracting_owner=HOP)
		self.resolve_all(self.case)
		draft = report.draft(frappe.get_doc("Evaluation Case", self.case))
		signing.send_for_signing(tender=self.name, expected_version=draft.record_version, idempotency_key=key(), user=SECRETARY)
		version = signing.signing_version(frappe.get_doc("Evaluation Case", self.case)).name
		for user in (CHAIR, MEMBER, MEMBER_2):
			signing.sign(tender=self.name, report_version=version, idempotency_key=key(), user=user)
		self.award = frappe.db.get_value(records.CASE, {"tender": self.name}, "name")

	def test_delivery_creates_one_case_and_one_task(self):
		self.assertTrue(self.award, "Award did not receive the delivered report")
		doc = frappe.get_doc(records.CASE, self.award)
		rep = state.current_report(doc)
		evl = frappe.get_doc("Evaluation Report Version", {"evaluation_case": self.case, "state": "Delivered"})
		self.assertEqual((doc.source_kind, doc.stage, rep.content_digest, rep.version_number), ("Evaluation", "Opinion", evl.content_digest, 1))
		self.assertEqual(doc.fixture_namespace, frappe.db.get_value("Evaluation Case", self.case, "fixture_namespace"))
		mine = [t["task"] for t in tasks.for_user(doc, HOP)]
		self.assertEqual(mine, ["Prepare professional opinion"])
		self.assertEqual(frappe.db.get_value("Evaluation Report Delivery", rep.source_delivery, "review_state"), "With Award")
		self.assertNotIn(f"Review evaluation report for {self.reference}", titles(HOP))
		again = intake.receive(delivery=rep.source_delivery, source_kind=sources.EVALUATION)
		self.assertEqual(again["award"], self.award)
		self.assertEqual(frappe.db.count(records.CASE, {"tender": self.name}), 1)
		self.assertEqual(frappe.db.count(state.REPORT, {"award_case": self.award}), 1)

	def test_return_report_goes_back_through_evaluation(self):
		doc = frappe.get_doc(records.CASE, self.award)
		out = opinion.return_report(award=self.award, reason="The service-address page reference must be corrected.", expected_version=doc.record_version,
			idempotency_key=key(), user=HOP)
		self.assertTrue(out["ok"], out)
		self.assertEqual(frappe.db.get_value("Evaluation Case", self.case, "state"), "Reviewing")
		self.assertEqual(frappe.db.get_value("Evaluation Report Delivery", state.current_report(frappe.get_doc(records.CASE, self.award)).source_delivery,
			"review_state"), "Returned")
		self.assertEqual(state.cycle(frappe.get_doc(records.CASE, self.award)).awaiting_report, 1)
