# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Debrief correspondence (AWD-CHG-001 v0.4 §5.6; AWD-AC-015; tracker AWD4-801)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import explanation, simulation, state, supplier
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.tests.support import DAVID, HOP, AwardCase

REPLY = "The recorded result follows the signed evaluation report. Your tender was successful at KES 46,400,000."


class TestExplanation(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 10:00:00")
		self.request = self.run_as(DAVID, supplier.request_explanation, notice=notice.name, request="Please explain the recorded award result.")["request"]

	def test_send_and_close(self):
		self.run_as(HOP, explanation.save, award=self.case().name, request=self.request, reply=REPLY)
		self.at("2027-06-18 10:15:00")
		out = self.run_as(HOP, explanation.send, award=self.case().name, request=self.request)
		self.assertEqual(out["message"], "This request is closed.")
		c = frappe.get_doc(state.CORRESPONDENCE, self.request)
		self.assertEqual((c.state, c.reply_text, str(c.closed_at)), ("Closed", REPLY, "2027-06-18 10:15:00"))
		with self.assertRaises(AwardError):
			self.run_as(HOP, explanation.save, award=self.case().name, request=self.request, reply="changed")

	def test_failed_dispatch_keeps_the_request_open_and_the_same_reply(self):
		simulation.set_controls(email_service_down=1)
		out = self.run_as(HOP, explanation.send, award=self.case().name, request=self.request, reply=REPLY)
		self.assertEqual((out["ok"], out["message"]), (False, "The reply has not been sent. This request remains open."))
		c = frappe.get_doc(state.CORRESPONDENCE, self.request)
		self.assertEqual((c.state, c.reply_state, c.reply_text), ("Open", "Sending", REPLY))
		simulation.set_controls(email_service_down=0)
		self.run_as(HOP, explanation.send, award=self.case().name, request=self.request, reply="a different text is ignored")
		c = frappe.get_doc(state.CORRESPONDENCE, self.request)
		self.assertEqual((c.state, c.reply_text), ("Closed", REPLY))

	def test_later_request_is_linked_not_merged(self):
		self.run_as(HOP, explanation.send, award=self.case().name, request=self.request, reply=REPLY)
		notice = state.successful_notice(state.current_batch(self.case()))
		second = self.run_as(DAVID, supplier.request_explanation, notice=notice.name, request="A follow-up question.")["request"]
		self.assertEqual(frappe.db.get_value(state.CORRESPONDENCE, second, "predecessor"), self.request)
		self.assertEqual(frappe.db.get_value(state.CORRESPONDENCE, self.request, "reply_text"), REPLY)
