# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Notices (AWD-CHG-001 v0.4 §5.4; AWD-AC-007–009, AC-014; tracker AWD4-501–503)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import checks, clocks, decision, issues, notices, simulation, state
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, CASE, AwardCase

NAME37 = "AWD-AWT-2100-037"


class TestDelivery(AwardCase):
	def test_one_action_authorises_and_issues_the_exact_batch(self):
		self.deliver()
		self.awarded()
		batch = state.current_batch(self.case())
		n = state.notices(batch)[0]
		self.assertEqual((n.result, n.status, n.version), ("Successful", "Given", 1))
		body = frappe.parse_json(n.content_json)
		self.assertEqual(body["notice"], "Award notice 1")
		self.assertEqual(body["reply_deadline"], "24 Jun 2027, 17:00 EAT")
		self.assertIn("Accepting this award does not create a contract.", n.letter_html)
		self.assertEqual(len(frappe.parse_json(n.evidence_json)), 2)  # portal published (not giving) + email delivered (giving)
		self.assertEqual(str(clocks.current(self.case(), "Minimum wait", n.name)[0].deadline), "2027-07-02 09:00:00")

	def test_two_bidders_each_get_their_own_result(self):
		self.deliver("037")
		self.awarded(NAME37)
		batch = state.current_batch(self.case(NAME37))
		by = {n.organisation_name: n for n in state.notices(batch)}
		self.assertEqual(by["Jirani Office Supplies Limited"].result, "Successful")
		afya = frappe.parse_json(by["Afya Digital Supplies Limited"].content_json)
		self.assertEqual((afya["result"], afya["successful_supplier"], afya["award_amount"], afya["own_amount"]),
			("Unsuccessful", "Jirani Office Supplies Limited", "KES 45,900,000", "KES 46,400,000"))
		self.assertEqual(afya["reason"], "Your tender met the requirements. Another responsive tender had a lower evaluated price.")
		self.assertNotIn("reply_deadline", afya)

	def test_failed_address_task(self):
		self.deliver("037")
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		self.awarded(NAME37)
		doc = self.case(NAME37)
		self.assertEqual(doc.stage, "Notices")
		found = issues.open_issues(doc, subtype=notices.DELIVERY_SUBTYPE)
		self.assertEqual((len(found), found[0].title, found[0].reason), (1, "A required notice is not yet confirmed.", "The notice address was rejected."))
		failed = [n for n in state.notices(state.current_batch(doc)) if n.status == "Failed"][0]
		first_digest = failed.content_digest
		# the contact owner corrects the address; the same notice is retried
		syn.correct_contact(failed.bid, "bids@afyadigital.example")
		simulation.set_controls(email_failure_organisations="")
		self.assertEqual(notices.retry(doc, failed), "Delivered")
		again = frappe.get_doc(state.NOTICE, failed.name)
		self.assertEqual((again.status, again.contact_email, again.content_digest), ("Given", "bids@afyadigital.example", first_digest))
		self.assertEqual(len(frappe.parse_json(again.contact_history_json)), 2)
		self.assertEqual(len(frappe.parse_json(again.attempts_json)), 2)
		self.assertEqual(self.case(NAME37).stage, "Waiting to proceed")
		self.assertEqual(frappe.db.count(state.NOTICE, {"award_case": NAME37}), 2)

	def test_service_failure_names_the_technical_owner(self):
		self.deliver()
		simulation.set_controls(email_service_down=1)
		self.awarded()
		found = issues.open_issues(self.case(), subtype=notices.SERVICE_SUBTYPE)
		self.assertEqual(found[0].owner_role, "Technical Operator")
		self.assertTrue(frappe.db.exists("Support Issue", {"module": "Award", "subject": "Restore notice delivery", "status": "Open"}))
		simulation.set_controls(email_service_down=0)
		self.assertEqual(notices.retry_failed(), 1)
		self.assertFalse(frappe.db.exists("Support Issue", {"module": "Award", "subject": "Restore notice delivery", "status": "Open"}))

	def test_validity_expiring_before_issue_stops_the_batch(self):
		self.deliver()
		self.signed_opinion()
		doc = self.case()
		syn.set_fact(doc.tender, validity_end="2027-06-17 09:59:00")
		self.at("2027-06-17 10:00:00")
		with self.assertRaises(AwardError) as ctx:
			self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="ok", expected_version=self.version())
		self.assertIn("AWD_VALIDITY_EXPIRED", [r["code"] for r in ctx.exception.reasons])
		self.assertEqual(self.case().notification_status, "Not issued")


class TestProfile(AwardCase):
	def test_unverified_profile(self):
		simulation.set_controls(rule_unverified=1)
		self.deliver()
		found = issues.open_issues(self.case(), subtype=checks.RULES_UNVERIFIED)
		self.assertEqual(found[0].title, "The applicable rules have not been confirmed. The award cannot proceed yet.")
		simulation.set_controls(rule_unverified=0)
		checks.sync(self.case())
		self.assertEqual(issues.open_issues(self.case(), subtype=checks.RULES_UNVERIFIED), [])
