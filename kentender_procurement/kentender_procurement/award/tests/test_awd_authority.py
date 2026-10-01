# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""GetAwardAuthorityStatus and the issue/cancellation boundary (AWD-CHG-001
v0.4 §5.4, §7; AWD-AC-010, AC-018; tracker AWD4-504)."""

from __future__ import annotations

from kentender_procurement.award.services import authority, simulation, state
from kentender_procurement.award.tests.support import AwardCase


class TestAuthority(AwardCase):
	def test_status_before_and_after_decision(self):
		self.deliver()
		tender = self.case().tender
		self.assertEqual(authority.status(tender=tender)["decision_status"], "No decision recorded")
		self.assertEqual(authority.tender_status(tender=tender)["status"], "No award decision recorded")
		self.assertEqual(authority.cancellation_guard(tender=tender), "")
		self.awarded()
		s = authority.status(tender=tender)
		self.assertEqual((s["decision_status"], s["notification_status"]), ("Award recorded", "Issued"))
		self.assertEqual(authority.tender_status(tender=tender)["status"], "Award decision recorded")
		self.assertEqual(authority.cancellation_guard(tender=tender), "Award notices have been issued. The pre-notification cancellation route is unavailable.")

	def test_no_case_is_not_a_negative_answer_from_award(self):
		self.assertIsNone(authority.tender_status(tender="SYN-NO-SUCH-TENDER"))

	def test_issue_in_progress_or_unknown_refuses_cancellation(self):
		self.deliver()
		doc = self.case()
		from kentender_procurement.award.services import records

		records.bump(doc, notification_status="Unknown")
		self.assertIn("could not be confirmed", authority.cancellation_guard(tender=doc.tender))
		records.bump(state.reload(doc), notification_status="Issue in progress")
		self.assertIn("pre-notification cancellation route is unavailable", authority.cancellation_guard(tender=doc.tender))

	def test_status_unavailable(self):
		from kentender_procurement.award.services import checks, issues

		simulation.set_controls(status_service_down=1)
		self.deliver()
		self.assertEqual(len(issues.open_issues(self.case(), subtype=checks.STATUS_UNAVAILABLE)), 1)
