# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Restrictions and §5.10 outcomes (AWD-CHG-001 v0.4 §5.6, §5.10; AWD-AC-016, AC-030;
tracker AWD4-802)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import eligibility, issues, restrictions, state, tender_events
from kentender_procurement.award.services.errors import AwardError, InputError
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import HOP, AwardCase


class TestRestrictions(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.awarded()
		self.at("2027-06-20 11:00:00")

	def _order(self, basis="Authoritative order"):
		return self.run_as(HOP, restrictions.record_external, award=self.case().name, basis=basis, source="Review Board suspension notice",
			received_at="2027-06-20 11:00:00", evidence="PPARB/2027/33" if basis == "Authoritative order" else "", reason="Suspension received.")["issue"]

	def test_order_hold(self):
		issue = self._order()
		row = issues.open_issues(self.case(), issue_type="Review/order")[0]
		self.assertEqual((row.name, row.basis, row.holds, row.title), (issue, "Authoritative order", 1, "This award is on hold."))
		self.assertFalse(eligibility.conditions(self.case())["6"]["met"])
		self.assertEqual(restrictions.applicable(row), ("Restriction ended", "Further action required"))
		with self.assertRaises(InputError):
			self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=issue, outcome="Reported challenge not substantiated", reason="x", evidence="y")
		with self.assertRaises(InputError):
			self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=issue, outcome="Override", reason="x", evidence="y")
		self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=issue, outcome="Restriction ended", reason="The Board released the suspension.",
			evidence="PPARB/2027/33 release")
		self.assertEqual(issues.open_issues(self.case(), issue_type="Review/order"), [])

	def test_order_needs_evidence(self):
		with self.assertRaises(InputError):
			self.run_as(HOP, restrictions.record_external, award=self.case().name, basis="Authoritative order", source="Board", received_at="2027-06-20 11:00:00",
				reason="x", evidence="")

	def test_precautionary_hold_is_distinct_and_clears_only_itself(self):
		order = self._order()
		challenge = self._order("Reported challenge")
		self.assertEqual(restrictions.applicable(state.reload(self.case()) and __import__("frappe").get_doc(state.ISSUE, challenge)),
			("Reported challenge not substantiated", "Further action required"))
		self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=challenge, outcome="Reported challenge not substantiated",
			reason="The complainant withdrew.", evidence="Letter of withdrawal")
		self.assertEqual([i.name for i in issues.open_issues(self.case(), issue_type="Review/order")], [order])

	def test_order_cannot_end_while_another_order_continues(self):
		first = self._order()
		self._order()
		with self.assertRaises(AwardError) as ctx:
			self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=first, outcome="Restriction ended", reason="x", evidence="y")
		self.assertEqual(ctx.exception.code, "AWD_ON_HOLD")

	def test_no_timer_clears_a_hold(self):
		self._order()
		self.at("2027-09-01 09:00:00")
		eligibility.refresh_case(self.case().name)
		self.assertEqual(len(issues.open_issues(self.case(), issue_type="Review/order")), 1)

	# -- an order Tenders sent is ended only by Tenders' release (AUD-AWD-003) ----------------
	def _tenders_order(self):
		syn.add_event(self.case().tender, {"event_key": "EVT-SUSP-1", "kind": "Suspension", "authority": "Review Board", "effective_at": "2027-06-20 10:00:00",
			"source_reference": "PPARB/2027/77", "reason": "The Board suspended the procurement."})
		tender_events.consume_case(self.case().name)
		(row,) = issues.open_issues(self.case(), issue_type="Review/order")
		self.assertEqual(row.source_event, "tender-event:EVT-SUSP-1")
		return row

	def test_a_tenders_order_cannot_be_ended_by_free_text(self):
		row = self._tenders_order()
		with self.assertRaises(AwardError) as ctx:
			self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=row.name, outcome="Restriction ended", reason="The Board released it.",
				evidence="I was told by phone that it was released")
		self.assertEqual((ctx.exception.code, ctx.exception.detail["reason"]), ("AWD_ON_HOLD", "no_release_evidence"))
		self.assertEqual(len(issues.open_issues(self.case(), issue_type="Review/order")), 1)

	def test_a_tenders_order_ends_on_the_release_tenders_reported(self):
		row = self._tenders_order()
		syn.add_event(self.case().tender, {"event_key": "EVT-RES-1", "kind": "Resumption", "source_reference": "PPARB/2027/77-RELEASE"})
		tender_events.consume_case(self.case().name)
		out = self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=row.name, outcome="Restriction ended", reason="The Board released the suspension.")
		self.assertTrue(out["ok"])
		ended = frappe.get_doc(state.ISSUE, row.name)
		self.assertEqual((ended.state, ended.disposition_evidence), ("Resolved", "Tenders release PPARB/2027/77-RELEASE"))
