# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The supplier's award notice (AWD-CHG-001 v0.4 §5.5, §5.6; AWD-AC-011, AC-012;
tracker AWD4-601–602)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import eligibility, issues, state, supplier
from kentender_procurement.award.services.errors import AwardError, InputError
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import DAVID, HOP, MARY, AwardCase


class TestRespond(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.awarded()
		self.notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 09:00:00")

	def test_accept(self):
		view = self.run_as(MARY, lambda user, idempotency_key: supplier.notice_view(notice=self.notice.name, user=user))
		self.assertTrue(view["can_respond"])
		self.assertEqual((view["next_step"]["headline"], view["reply_deadline"], view["not_a_contract"]),
			("Your tender was successful.", "24 Jun 2027, 17:00 EAT", "Accepting this award does not create a contract."))
		self.assertEqual(view["accept_wording"], "I accept Award notice 1 on behalf of Afya Digital Supplies Limited.")
		out = self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Accept", notice_version=1)
		self.assertTrue(out["ok"])
		r = state.operative_response(frappe.get_doc(state.NOTICE, self.notice.name))
		self.assertEqual((r.response, r.responder, r.late, str(r.received_at)), ("Accept", MARY, 0, "2027-06-18 09:00:00"))
		self.assertTrue(r.authority_evidence)

	def test_representative_cannot_respond(self):
		view = self.run_as(DAVID, lambda user, idempotency_key: supplier.notice_view(notice=self.notice.name, user=user))
		self.assertFalse(view["can_respond"])
		self.assertEqual(view["next_step"]["sentence"], "Mary Wanjiku must respond for Afya Digital Supplies Limited.")
		with self.assertRaises(AwardError) as ctx:
			self.run_as(DAVID, supplier.respond, notice=self.notice.name, response="Accept", notice_version=1)
		self.assertEqual(ctx.exception.code, "AWD_AUTHORITY_REQUIRED")
		self.assertEqual(state.responses(self.notice), [])

	def test_other_people_see_nothing(self):
		with self.assertRaises(frappe.DoesNotExistError):
			self.run_as(HOP, lambda user, idempotency_key: supplier.notice_view(notice=self.notice.name, user=user))

	def test_expired_authority_and_stale_notice_have_no_side_effect(self):
		with self.assertRaises(AwardError) as ctx:
			self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Accept", notice_version=2)
		self.assertEqual(ctx.exception.code, "AWD_NOTICE_CHANGED")
		syn.revoke_signatory(MARY, self.notice.organisation)
		with self.assertRaises((AwardError, frappe.DoesNotExistError)):
			self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Accept", notice_version=1)
		self.assertEqual(state.responses(self.notice), [])

	def test_decline_task(self):
		with self.assertRaises(InputError):
			self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Decline", notice_version=1, reason="")
		self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Decline", notice_version=1, reason="We cannot meet the delivery commitment.")
		found = issues.open_issues(self.case(), subtype=eligibility.RESPONSE_SUBTYPE_DECLINED)
		self.assertEqual((found[0].title, found[0].reason), ("Review the supplier’s response.", "We cannot meet the delivery commitment."))
		self.assertEqual(self.case().stage, "Waiting to proceed")
		self.assertFalse(frappe.db.exists("Award Contracting Package", {"award_case": self.case().name, "status": "Delivered"}))

	def test_late_response(self):
		self.at("2027-06-24 17:01:00")
		out = self.run_as(MARY, supplier.respond, notice=self.notice.name, response="Accept", notice_version=1)
		self.assertEqual((out["late"], out["message"]), (True, "Your response was received after the deadline. It cannot be used to proceed with this award."))
		self.assertIsNone(state.operative_response(frappe.get_doc(state.NOTICE, self.notice.name)))
		self.assertEqual(len(issues.open_issues(self.case(), subtype=eligibility.RESPONSE_SUBTYPE_OVERDUE)), 1)
		view = self.run_as(MARY, lambda user, idempotency_key: supplier.notice_view(notice=self.notice.name, user=user))
		self.assertEqual(view["next_step"]["headline"], "Your response was received after the deadline. It cannot be used to proceed with this award.")
		self.assertFalse(view["can_respond"])

	def test_request_explanation(self):
		out = self.run_as(DAVID, supplier.request_explanation, notice=self.notice.name, request="Please explain the recorded award result.")
		self.assertTrue(out["ok"])
		c = frappe.get_doc(state.CORRESPONDENCE, out["request"])
		self.assertEqual((c.state, c.requested_by, c.organisation_name), ("Open", DAVID, "Afya Digital Supplies Limited"))
