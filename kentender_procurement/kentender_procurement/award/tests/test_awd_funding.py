# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding is read from Budget at decision time and fails closed (AWD-CHG-001
v0.5 §5.1, §5.5, AWD-IF-07; AUD-AWD-002), and a funding restriction is cleared
by Budget's own confirmation, never by free text (§5.10; AUD-AWD-003).

The synthetic Budget answer (`award/test_services/sources.py`) stands in for
Budget's published `get_funding_lineage`; the real provider's reading of that
contract is covered by `TestEvaluationSourceFunding`."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_procurement.award.services import checks, decision, issues, notices, restrictions, sources
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, CASE, HOP, AwardCase

TENDER = "SYN-TND-AWT-2100-033"
REASON = "I accept the recommendation in the signed evaluation report and professional opinion."


class TestFundingAtDecision(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")

	def award(self):
		return self.run_as(AO, decision.record, award=CASE, outcome="Award", reason=REASON, expected_version=self.version())

	def test_budget_unavailable_refuses_a_positive_award(self):
		syn.set_fact(TENDER, funding_down=True)
		with self.assertRaises(AwardError) as ctx:
			self.award()
		self.assertEqual(ctx.exception.code, "AWD_STATUS_UNAVAILABLE")
		self.assertEqual(ctx.exception.detail["check"], "funding")
		self.assertEqual(self.case().decision_status, "No decision recorded")

	def test_an_absent_funding_block_in_the_report_is_not_treated_as_not_restricted(self):
		self.deliver("037", overrides={"funding": {}})
		self.signed_opinion("AWD-AWT-2100-037")
		syn.set_fact("SYN-TND-AWT-2100-037", funding_down=True)
		with self.assertRaises(AwardError) as ctx:
			self.run_as(AO, decision.record, award="AWD-AWT-2100-037", outcome="Award", reason=REASON, expected_version=self.version("AWD-AWT-2100-037"))
		self.assertEqual(ctx.exception.code, "AWD_STATUS_UNAVAILABLE")

	def test_funding_withdrawn_after_the_report_was_signed_refuses_the_award(self):
		# the signed report said 50,000,000 was available; Budget now holds less than the evaluated 46,400,000
		syn.set_fact(TENDER, funding_available="30000000.00")
		with self.assertRaises(AwardError) as ctx:
			self.award()
		self.assertEqual(ctx.exception.code, "AWD_ON_HOLD")
		self.assertEqual(ctx.exception.detail["shortfall"], "16400000.00")

	def test_confirmed_funding_allows_the_award(self):
		self.assertTrue(self.award()["ok"])
		self.assertEqual(self.case().decision_status, "Award recorded")

	def test_no_award_and_return_do_not_need_funding(self):
		syn.set_fact(TENDER, funding_down=True)
		out = self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Funding could not be confirmed.", next_action="Ask Budget to confirm funding",
			expected_version=self.version())
		self.assertTrue(out["ok"])

	def test_notice_issue_rechecks_funding(self):
		syn.set_fact(TENDER, funding_down=True)
		doc = self.case()
		self.assertEqual(notices._stop_reasons(doc), ["funding"])
		syn.set_fact(TENDER, funding_down=False)
		self.assertEqual(notices._stop_reasons(doc), [])

	def test_the_live_position_replaces_the_frozen_report_figure(self):
		self.assertEqual(checks.funding_stop(self.case()), "")
		syn.set_fact(TENDER, funding_available="1.00")
		self.assertEqual(checks.funding_stop(self.case()), "restricted")
		syn.set_fact(TENDER, funding_down=True)
		self.assertEqual(checks.funding_stop(self.case()), "unknown")


class TestFundingRestrictionEvidence(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		syn.set_fact(TENDER, funding_available="30000000.00")
		checks.sync(self.case())

	def funding_issue(self):
		return issues.open_issues(self.case(), subtype=checks.FUNDING)

	def dispose(self, **kwargs):
		return self.run_as(HOP, restrictions.disposition, award=CASE, issue=kwargs.pop("issue"), outcome="Owner correction confirmed", reason="Budget has corrected it.",
			evidence="Email from Budget, 14 June", **kwargs)

	def test_free_text_does_not_clear_a_funding_restriction(self):
		(issue,) = self.funding_issue()
		with self.assertRaises(AwardError) as ctx:
			self.dispose(issue=issue.name)
		self.assertEqual((ctx.exception.code, ctx.exception.detail["reason"]), ("AWD_ON_HOLD", "funding_not_confirmed"))
		self.assertEqual(len(self.funding_issue()), 1)

	def test_budget_unavailable_does_not_clear_it_either(self):
		(issue,) = self.funding_issue()
		syn.set_fact(TENDER, funding_down=True)
		with self.assertRaises(AwardError):
			self.dispose(issue=issue.name)
		self.assertEqual(len(self.funding_issue()), 1)

	def test_budget_confirmation_clears_it_and_a_later_shortfall_reopens_it(self):
		(issue,) = self.funding_issue()
		syn.set_fact(TENDER, funding_available="50000000.00")
		out = self.dispose(issue=issue.name)
		self.assertTrue(out["ok"])
		self.assertEqual(self.funding_issue(), [])
		# funding is withdrawn again: the restriction is raised again, not hidden behind the resolved issue
		syn.set_fact(TENDER, funding_available="20000000.00")
		checks.sync(self.case())
		self.assertEqual(len(self.funding_issue()), 1)

	def test_the_system_clears_a_funding_restriction_when_budget_confirms(self):
		syn.set_fact(TENDER, funding_available="50000000.00")
		checks.sync(self.case())
		self.assertEqual(self.funding_issue(), [])


class TestEvaluationSourceFunding(AwardCase):
	"""The real provider reads Budget's published `get_funding_lineage` and never invents a position."""

	def lineage(self, *rows, status="Active"):
		return {"rows": [{"reservation": {"code": f"R-{n}", "status": status, "remaining_amount": amount}} for n, amount in enumerate(rows, 1)]}

	def read(self, reservations, lineage):
		provider = sources.EvaluationSource()
		with mock.patch("kentender_procurement.tenders.services.award_seam.funding_reservations", return_value=reservations), \
				mock.patch("kentender_budget.services.budget_downstream_contracts.get_funding_lineage", side_effect=lineage):
			return provider.funding("ANY-TENDER")

	def test_it_sums_the_remaining_amount_of_the_tenders_reservations(self):
		out = self.read(["A", "B"], [self.lineage("30000000.00"), self.lineage("20000000.50")])
		self.assertEqual((out["known"], out["available"], out["reservations"]), (True, "50000000.50", ["R-1", "R-1"]))

	def test_a_released_reservation_adds_nothing(self):
		out = self.read(["A"], [self.lineage("30000000.00", status="Released")])
		self.assertEqual((out["known"], out["available"]), (True, "0.00"))

	def test_no_reservation_is_unknown_not_unrestricted(self):
		self.assertFalse(self.read([], [])["known"])

	def test_a_reservation_budget_cannot_confirm_is_unknown(self):
		self.assertFalse(self.read(["A"], [{"rows": []}])["known"])

	def test_a_budget_failure_is_unknown(self):
		self.assertFalse(self.read(["A"], [frappe.PermissionError("no scope")])["known"])
