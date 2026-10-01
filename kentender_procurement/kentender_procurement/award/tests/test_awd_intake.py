# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ReceiveEvaluationReport (AWD-CHG-001 v0.4 §3, §5.1; AWD-AC-001, AC-002;
tracker AWD4-301) on the synthetic sources."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import checks, issues, records, state
from kentender_procurement.award.tests.support import CASE, HOP, AwardCase


class TestIntake(AwardCase):
	def test_delivery_creates_one_case_cycle_and_hop_task(self):
		out = self.deliver()
		self.assertTrue(out["ok"])
		doc = self.case()
		self.assertEqual((doc.stage, doc.current_cycle, doc.decision_status, doc.notification_status), ("Opinion", 1, "No decision recorded", "Not issued"))
		self.assertEqual(frappe.db.count(state.CYCLE, {"award_case": CASE}), 1)
		self.assertEqual(state.snapshot(state.current_report(doc))["recommended"]["bidder"], "Afya Digital Supplies Limited")
		self.assertEqual(issues.hop_for(doc), HOP)

	def test_retry_returns_the_same_case_without_duplicates(self):
		first = self.deliver()
		from kentender_procurement.award.services import intake

		again = intake.receive(delivery="SYN-DLV:TND-AWT-2100-033:1", source_kind="Synthetic")
		self.assertEqual(first["award"], again["award"])
		self.assertEqual(frappe.db.count(state.REPORT, {"award_case": CASE}), 1)
		self.assertEqual(frappe.db.count(records.CASE, {"name": CASE}), 1)

	def test_incomplete_source_opens_the_exact_issue(self):
		self.deliver(overrides={"missing_annex": True})
		doc = self.case()
		found = issues.open_issues(doc, subtype=checks.SOURCE_INCOMPLETE)
		self.assertEqual(len(found), 1)
		self.assertEqual(found[0].title, "The evaluation report is incomplete. The Head of Procurement has been notified.")
		self.assertEqual(found[0].reason, "One required annex is unavailable.")
		self.assertEqual(found[0].owner_user, HOP)

	def test_missing_signature_is_a_source_issue(self):
		self.deliver(overrides={"signed": 2})
		self.assertEqual(issues.open_issues(self.case(), subtype=checks.SOURCE_INCOMPLETE)[0].reason, "A required committee signature is missing.")

	def test_expired_validity_is_recorded_at_receipt(self):
		self.at("2027-10-11 09:00:00")
		self.deliver(overrides={"validity_end": "2027-10-10 11:00:00"})
		self.assertEqual(issues.open_issues(self.case(), subtype=checks.VALIDITY_EXPIRED)[0].title, "Tender validity has expired. No award can proceed.")

	def test_unreadable_status_is_unknown_not_negative(self):
		from kentender_procurement.award.services import simulation

		simulation.set_controls(status_service_down=1)
		self.deliver()
		found = issues.open_issues(self.case(), subtype=checks.STATUS_UNAVAILABLE)
		self.assertEqual(len(found), 1)
		self.assertFalse(checks.tender_status(self.case())["known"])
		simulation.set_controls(status_service_down=0)
		checks.sync(self.case())
		self.assertEqual(issues.open_issues(self.case(), subtype=checks.STATUS_UNAVAILABLE), [])
