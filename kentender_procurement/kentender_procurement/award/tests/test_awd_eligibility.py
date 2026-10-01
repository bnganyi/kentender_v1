# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clocks and RefreshAwardEligibility (AWD-CHG-001 v0.4 §5.5, §5.8; AWD-AC-012–014,
AC-028; tracker AWD4-701–702, AWD4-704)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import eligibility, issues, profile, restrictions, state, supplier
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import HOP, MARY, AwardCase


class Accepted(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.awarded()
		self.notice = state.successful_notice(state.current_batch(self.case()))


class TestWait(Accepted):
	def test_wait_boundary(self):
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Accept", notice_version=1)
		cond = eligibility.conditions(self.case())
		self.assertEqual([cond[str(n)]["met"] for n in range(1, 7)], [True, True, True, False, True, True])
		self.assertEqual(str(cond["4"]["earliest"]), "2027-07-02 09:00:00")
		self.at("2027-07-02 08:59:59")
		self.assertEqual(eligibility.refresh_case(self.case().name)["stage"], "Waiting to proceed")
		self.at("2027-07-02 09:00:00")
		out = eligibility.refresh_case(self.case().name)
		self.assertEqual(out["stage"], "Sent to Contracting")

	def test_profile_terms(self):
		deadline, _ = profile.reply_deadline("2027-06-17 10:00:00")
		earliest, _ = profile.earliest_permitted("2027-06-17 10:00:00")
		self.assertEqual((str(deadline), str(earliest)), ("2027-06-24 17:00:00", "2027-07-02 09:00:00"))
		# a later giving time moves the earliest instant to the following day
		self.assertEqual(str(profile.earliest_permitted("2027-06-17 09:00:00")[0]), "2027-07-01 09:00:00")


class TestReply(Accepted):
	def test_no_response_task(self):
		self.at("2027-06-24 17:00:00")
		eligibility.refresh_case(self.case().name)
		self.assertEqual(issues.open_issues(self.case(), subtype=eligibility.RESPONSE_SUBTYPE_OVERDUE), [])
		self.at("2027-06-24 17:01:00")
		eligibility.refresh_case(self.case().name)
		found = issues.open_issues(self.case(), subtype=eligibility.RESPONSE_SUBTYPE_OVERDUE)
		self.assertEqual(found[0].title, "The supplier has not replied by the deadline.")
		# Record next action: the outcome is fixed and the evidence attached by the server
		out = self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=found[0].name, reason="No reply by the deadline.",
			next_action="Refer to the Accounting Officer for the next procurement action")
		self.assertEqual(out["outcome"], "Request decision review")
		self.assertTrue(restrictions.proposals(self.case()))


class TestValidity(Accepted):
	def test_expiry_holds(self):
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Accept", notice_version=1)
		syn.set_fact(self.case().tender, validity_end="2027-06-30 11:00:00")
		self.at("2027-07-02 09:00:00")
		out = eligibility.refresh_case(self.case().name)
		self.assertEqual(out["stage"], "Waiting to proceed")
		self.assertTrue(issues.open_issues(self.case(), subtype="Validity expired"))
		self.assertFalse(eligibility.conditions(self.case())["5"]["met"])


class TestClockRevision(Accepted):
	def test_a_lawful_revision_keeps_the_earlier_calculation(self):
		from kentender_procurement.award.services import clocks

		doc = self.case()
		first = clocks.current(doc, "Minimum wait", self.notice.name)[0]
		revised = clocks.record(doc, kind="Minimum wait", notice=self.notice.name, trigger_at="2027-06-17 10:00:00",
			trigger_evidence="Revised by the verified profile", deadline="2027-07-05 09:00:00", rule="Revised treatment (test)")
		self.assertEqual((revised.revision, str(revised.deadline)), (2, "2027-07-05 09:00:00"))
		self.assertEqual(frappe.db.get_value("Award Clock", first.name, "state"), "Revised")
		self.assertEqual(str(eligibility.conditions(self.case())["4"]["earliest"]), "2027-07-05 09:00:00")
