# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Opening and the tender-security intake duty (Project Owner, 10 October 2026):
on the same Tender they exclude each other, in both directions; the opening
access boundary opens only when the opening starts; opening appointment alone
gives no intake access."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
import frappe

from kentender_procurement.bid_opening.services import appointment, picker_sources
from kentender_procurement.bid_opening.tests.support import AO, CHAIR, INDEPENDENT, MEMBER, OpeningCase
from kentender_procurement.bid_submission.services import records, security_duty, security_matching
from kentender_procurement.tenders.tests import fixtures as tender_fx

OFFICER = tender_fx.AUDITOR  # an existing person (a site-wide responsibility) with no opening or evaluation appointment


class TestIntakeDutyAndOpening(OpeningCase):
	def assign(self, officer=OFFICER):
		return security_duty.assign_intake_officer(tender_reference=self.reference, officer=officer, user=tender_fx.HOPF)

	def test_committee_members_cannot_be_assigned_the_duty_and_say_which_duty_is_incompatible(self):
		self.prepared()
		for member in (MEMBER, INDEPENDENT):
			with self.subTest(member=member), self.assertRaises(Exception) as caught:
				self.assign(member)
			self.assertIn("is on the opening committee for this Tender, so cannot also take its tender-security intake", str(caught.exception))
			for word in ("supplier", "Afya", "bid"):
				self.assertNotIn(word, str(caught.exception).lower().replace("tender-security intake", ""))

	def test_an_appointment_is_refused_for_the_officer_who_holds_the_duty_and_works_again_once_it_is_unused_and_revoked(self):
		self.prepare_case()
		given = self.assign()
		roster = [{"user": CHAIR, "committee_role": "Chair and recorder"}, {"user": OFFICER, "committee_role": "Member"}, {"user": INDEPENDENT, "committee_role": "Independent member"}]
		refused = self.appoint(roster)
		self.assertFalse(refused["ok"])
		self.assertIn("holds or has held the tender-security intake duty for this Tender", refused["errors"][OFFICER])
		# the picker lists the person unavailable, in the command's own words: a person missing from the list with no explanation is worse than a refusal
		offered = {c["id"]: c for c in picker_sources.committee_members(query="", context={"tender": self.name, "role": "Member"}, actor=AO, limit=20)}
		self.assertEqual(offered[OFFICER]["disabled_reason"], refused["errors"][OFFICER])
		self.assertIn("holds or has held the tender-security intake duty for this Tender", offered[OFFICER]["disabled_reason"])
		security_duty.revoke_intake_officer(assignment=given["assignment"], reason="Assigned in error before the committee was named.", user=tender_fx.HOPF)
		after = {c["id"]: c for c in picker_sources.committee_members(query="", context={"tender": self.name, "role": "Member"}, actor=AO, limit=20)}
		self.assertIsNone(after[OFFICER]["disabled_reason"])  # once the duty is revoked and unused, they are choosable again
		self.assertTrue(self.appoint(roster)["ok"])
		self.assertIn(OFFICER, [m["member_user"] for m in appointment.roster(frappe.db.get_value("Bid Opening Case", {"tender": self.name}, "name"))])

	def test_an_officer_who_used_the_duty_stays_ineligible_after_it_ends(self):
		self.prepare_case()
		given = self.assign()
		with records.atomic("exposure"):
			security_duty.record_exposure(self.name, self.reference, OFFICER, security_duty.VIEWED)
		security_duty.revoke_intake_officer(assignment=given["assignment"], reason="The duty ended once the deadline had passed.", user=tender_fx.HOPF)
		roster = [{"user": CHAIR, "committee_role": "Chair and recorder"}, {"user": OFFICER, "committee_role": "Member"}, {"user": INDEPENDENT, "committee_role": "Independent member"}]
		refused = self.appoint(roster)
		self.assertFalse(refused["ok"])
		self.assertIn("holds or has held", refused["errors"][OFFICER])

	def test_an_opening_appointment_alone_gives_no_intake_access(self):
		self.prepared()
		for user in (CHAIR, MEMBER, INDEPENDENT, AO):
			with self.subTest(user=user):
				self.assertFalse(security_duty.holds_duty(user, self.reference))
				with self.assertRaises(frappe.PermissionError):
					security_duty.require_officer(user, self.reference)

	def test_the_boundary_is_crossed_only_when_the_opening_starts(self):
		self.prepared()
		self.assertFalse(security_matching.opening_crossed(self.name))
		frappe.db.set_value("Bid Opening Case", {"tender": self.name}, "started_at", W("2027-06-12 11:00:12"))
		self.assertTrue(security_matching.opening_crossed(self.name))
