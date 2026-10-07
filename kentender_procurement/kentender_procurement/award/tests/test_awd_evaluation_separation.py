# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-15 / AUD-AWD-001 — the same-tender separation, Award's side (owner decision 7 Oct 2026).

The deciding Accounting Officer is not on the tender's evaluation panel and did not sign its
report; the Head of Procurement who prepares and signs the professional opinion is not a member
or chair of that evaluation (the Head may have been its secretary). Typed refusals, from the
delivered report's recorded panel and signatures."""

from __future__ import annotations

from kentender_procurement.award.services import decision, opinion
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.tests.support import AO, CASE, HOP, AwardCase


def _panel(*, members=(), secretary="", signers=None):
	signers = list(signers if signers is not None else members)
	return {
		"panel": {"members": [{"user": u, "capacity": "Member"} for u in members], "chair": members[0] if members else "", "secretary": secretary},
		"signatures": {"required": len(signers), "signed": len(signers), "members": [{"user": u, "name": u, "signed_at": "2027-06-16 14:07:01"} for u in signers]},
	}


class TestAwardSeparationFromTheEvaluation(AwardCase):
	def decide(self):
		return self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="I accept the recommendation in the signed evaluation report and opinion.", expected_version=self.version())

	def refused(self, fn):
		with self.assertRaises(AwardError) as ctx:
			fn()
		self.assertEqual((ctx.exception.code, ctx.exception.detail["reason"]), ("AWD_AUTHORITY_REQUIRED", "segregation_of_duties"))
		return ctx.exception

	def test_an_accounting_officer_who_sat_on_the_panel_cannot_decide(self):
		self.deliver(overrides=_panel(members=["grace.wambui@moh.example.test", AO]))
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")
		before = self.version()
		self.refused(self.decide)
		self.assertEqual(self.version(), before)

	def test_an_accounting_officer_who_was_the_secretary_cannot_decide(self):
		self.deliver(overrides=_panel(members=["grace.wambui@moh.example.test"], secretary=AO))
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")
		self.refused(self.decide)

	def test_an_accounting_officer_who_signed_the_report_cannot_decide(self):
		self.deliver(overrides=_panel(members=["grace.wambui@moh.example.test"], signers=["grace.wambui@moh.example.test", AO]))
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")
		self.refused(self.decide)

	def test_a_head_who_evaluated_the_tender_cannot_prepare_or_sign_the_opinion(self):
		self.deliver(overrides=_panel(members=["grace.wambui@moh.example.test", HOP]))
		self.at("2027-06-17 09:00:00")
		self.refused(lambda: self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason="x", expected_version=self.version()))
		self.refused(lambda: self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version()))

	def test_a_head_who_was_only_the_secretary_still_prepares_the_opinion(self):
		self.deliver(overrides=_panel(members=["grace.wambui@moh.example.test", "peter.mugo@moh.example.test"], secretary=HOP))
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")
		self.assertTrue(self.decide()["ok"])

	def test_a_panel_that_does_not_include_either_office_changes_nothing(self):
		self.deliver(overrides=_panel(members=["grace.wambui@moh.example.test", "peter.mugo@moh.example.test", "ruth.achieng@moh.example.test"]))
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")
		self.assertTrue(self.decide()["ok"])
