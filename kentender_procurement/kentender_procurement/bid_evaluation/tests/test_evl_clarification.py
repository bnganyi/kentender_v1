# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Written clarification (EVL-CHG-001 v0.4 §5.3, §7.2, §7.3 rows 7–9, §8
EVL_REPLY_CLOSED, EVL_CLARIFICATION_NOTICE_FAILED, EVL_REPLY_OVERDUE; tracker
EVL4-701…708; acceptance EVL-A07 (service part); boards D05-CHAIR, D06-SEND,
D06-SUPPLIER, D06-RECEIVED, D06-DELIVERY, D06-LATE, D06-CLOSED, D06-OUTCOME,
D06-NO-REPLY, D06-CHANGED-OFFER, D06-WITHDRAW, D06-FINAL-CLOSED).

The chair authorises the exact question in session, the secretary sends it
unchanged, the supplier's own authorised users alone see it and send one
reply (on time or labelled late), the committee's disposition closes it
atomically, after which nothing more is accepted; a failed notice is true
and retried for the same request; a replacement is a new linked request and
the withdrawn one stays readable."""

from __future__ import annotations

from datetime import timedelta

import frappe

from kentender_procurement.bid_evaluation.services import aggregate, checks, clarification, findings, my_work_provider, reads, simulation
from kentender_procurement.bid_evaluation.services.errors import EvaluationError, InputError
from kentender_procurement.bid_evaluation.tests.support import CHAIR, MEMBER, SECRETARY, EvaluationCase
from kentender_procurement.bid_submission.tests.support import DAVID, MARY, PETER, key

QUESTION = "Please identify the page and section of your submitted Kenya service-centre details that gives the Nairobi service address."
SCOPE = "Explain the submitted evidence. Do not change your offer or add a new service arrangement."


def titles(user, kind="assigned"):
	return [r["title"] for r in my_work_provider.my_work_rows(user)[kind] if r["module"] == "Bid Evaluation"]


class ClarificationCase(EvaluationCase):
	def setUp(self):
		super().setUp()
		self.case = self.reviewing()
		service = self.requirement(self.case, "Service location")
		self.bid, self.key_ = service["bid"], service["requirement_key"]
		findings.record_evidence_finding(tender=self.name, bid=self.bid, requirement_key=self.key_, result="Needs review",
			reason="The submitted evidence does not clearly identify the service address.", idempotency_key=key(), user=MEMBER)
		self.now = frappe.utils.get_datetime(frappe.flags.kt_evl_clock)

	def evl_authorise(self, replaces="", replacement_reason=""):
		self.session()
		out = clarification.authorise(tender=self.name, bid=self.bid, requirement_key=self.key_, question=QUESTION, reply_scope=SCOPE,
			reply_deadline=str(self.now + timedelta(days=1)), replaces=replaces, replacement_reason=replacement_reason, idempotency_key=key(), user=CHAIR)
		self.end_session()
		return out["clarification"]

	def evl_send(self, request):
		return clarification.send(tender=self.name, clarification=request, idempotency_key=key(), user=SECRETARY)

	def evl_reply(self, request, user=DAVID, body="The service address is on page 2, section 3 of Kenya service-centre details."):
		return clarification.submit_reply(tender=self.name, clarification=request, body=body, idempotency_key=key(), user=user)

	def evl_dispose(self, request, disposition="Considered", result="Meets", reason="The address is present in the original submitted document and is within Kenya."):
		self.session()
		out = clarification.record_disposition(tender=self.name, clarification=request, disposition=disposition, result=result, reason=reason,
			idempotency_key=key(), user=CHAIR)
		self.end_session()
		return out

	def refused(self, fn, *args, **kwargs):
		with self.assertRaises(EvaluationError) as ctx:
			fn(*args, **kwargs)
		return ctx.exception


class TestOrdinaryClarification(ClarificationCase):
	def test_authorise_send_reply_and_close(self):
		request = self.evl_authorise()
		self.assertEqual(frappe.db.get_value("Evaluation Discussion Item", {"evaluation_case": self.case}, "resolution_kind"), "Clarification")
		self.assertIn(f"Send clarification for Afya Digital Supplies Limited", titles(SECRETARY))
		with self.assertRaises(frappe.DoesNotExistError):
			reads.own_clarification(tender_reference=self.reference, clarification=request, user=DAVID)  # not visible before it is sent
		sent = self.evl_send(request)
		self.assertEqual(sent["notice_state"], "Delivered")
		own = reads.own_clarification(tender_reference=self.reference, clarification=request, user=DAVID)
		self.assertEqual((own["question"], own["reply_scope"], own["status"]), (QUESTION, SCOPE, "Sent"))
		self.assertFalse(set(own) & {"findings", "ranking", "comparison", "committee"})
		with self.assertRaises(frappe.DoesNotExistError):
			reads.own_clarification(tender_reference=self.reference, clarification=request, user=PETER)  # another supplier
		draft = clarification.save_draft(tender=self.name, clarification=request, body="Draft wording", idempotency_key=key(), user=DAVID)
		self.assertEqual(draft["state"], "Draft")
		out = self.evl_reply(request, user=MARY)
		self.assertEqual((out["state"], out["timeliness"]), ("Sent", "On time"))
		self.assertEqual(self.refused(self.evl_reply, request).code, "EVL_REPLY_CLOSED")  # one reply
		self.assertIn("Review clarification outcome for Afya Digital Supplies Limited", titles(CHAIR))
		self.evl_dispose(request)
		row = frappe.get_doc("Evaluation Clarification", request)
		self.assertEqual((row.status, row.closure_reason, row.disposition), ("Closed", "Final disposition", "Considered"))
		self.assertEqual(self.requirement(self.case, "Service location")["result"], "Meets")
		self.assertEqual(self.refused(clarification.save_draft, tender=self.name, clarification=request, body="x", idempotency_key=key(), user=DAVID).code,
			"EVL_REPLY_CLOSED")


class TestSupplierPortal(ClarificationCase):
	def test_the_portal_page_link_and_attachments(self):
		import base64

		from kentender_procurement.bid_evaluation import portal
		from kentender_procurement.bid_submission import portal as bds_portal

		request = self.evl_authorise()
		self.assertEqual(portal.tender_links(tender_reference=self.reference, user=DAVID), [])  # nothing before it is sent
		self.evl_send(request)
		[link] = portal.tender_links(tender_reference=self.reference, user=DAVID)
		self.assertEqual(link["href"], f"/tenders/{self.reference}/bid/evaluation-clarifications/{request}")
		self.assertEqual(portal.tender_links(tender_reference=self.reference, user=PETER), [])  # another supplier sees nothing
		page = bds_portal.resolve(path=link["href"], query={}, user=DAVID)
		self.assertEqual((page["verdict"], page["payload"]["screen"]), ("OK", "evaluation-clarification"))
		self.assertEqual(bds_portal.resolve(path=link["href"], query={}, user=PETER)["verdict"], "NOT_FOUND")
		self.assertEqual(bds_portal.resolve(path=link["href"], query={}, user="Guest")["verdict"], "SIGN_IN")
		pdf = {"filename": "address.pdf", "media_type": "application/pdf", "content_base64": base64.b64encode(b"%PDF-1.4 address").decode()}
		with self.assertRaises(InputError) as ctx:
			clarification.save_draft(tender=self.name, clarification=request, body="Draft", idempotency_key=key(), user=DAVID,
				attachments=[{**pdf, "media_type": "application/zip"}])
		self.assertIn("attachments", ctx.exception.fields)
		clarification.save_draft(tender=self.name, clarification=request, body="Draft", attachments=[pdf], idempotency_key=key(), user=DAVID)
		own = reads.own_clarification(tender_reference=self.reference, clarification=request, user=DAVID)
		self.assertEqual(own["reply"]["attachments"], [{"filename": "address.pdf", "size": 16}])  # names and sizes only
		self.assertEqual(own["organisation_name"], "Afya Digital Supplies Limited")


class TestLateAndMissingReplies(ClarificationCase):
	def test_a_late_reply_is_labelled_and_no_reply_is_disposed(self):
		request = self.evl_authorise()
		self.evl_send(request)
		self.at(str(self.now + timedelta(days=1, minutes=5)))
		self.assertTrue(clarification.overdue(frappe.get_doc("Evaluation Clarification", request)))
		out = self.evl_reply(request)
		self.assertEqual(out["timeliness"], "Received late")
		with self.assertRaises(InputError) as ctx:  # a reply exists: it must be dispositioned, not ignored
			self.evl_dispose(request, disposition="No reply")
		self.assertIn("disposition", ctx.exception.fields)

	def test_no_reply_closes_and_leaves_the_requirement_open(self):
		request = self.evl_authorise()
		self.evl_send(request)
		self.at(str(self.now + timedelta(days=2)))
		self.evl_dispose(request, disposition="No reply", result="Needs review", reason="No reply was received; assess the original evidence.")
		self.assertEqual(frappe.db.get_value("Evaluation Clarification", request, "status"), "Closed")
		self.assertEqual(self.refused(self.evl_reply, request).code, "EVL_REPLY_CLOSED")


class TestNoticeAndReplacement(ClarificationCase):
	def test_a_failed_notice_is_true_and_retried_for_the_same_request(self):
		request = self.evl_authorise()
		simulation.set_controls(notice_outcome="Failed")
		sent = self.evl_send(request)
		self.assertEqual((sent["notice_state"], sent["notice_code"]), ("Delivery problem", "EVL_CLARIFICATION_NOTICE_FAILED"))
		self.assertEqual(reads.own_clarification(tender_reference=self.reference, clarification=request, user=DAVID)["status"], "Sent")  # still available
		simulation.set_controls(notice_outcome="")
		again = clarification.retry_notice(tender=self.name, clarification=request, idempotency_key=key(), user=SECRETARY)
		self.assertEqual(again["notice_state"], "Delivered")
		self.assertEqual(frappe.db.count("Evaluation Clarification", {"evaluation_case": self.case}), 1)

	def test_a_replacement_is_a_new_linked_request(self):
		first = self.evl_authorise()
		self.evl_send(first)
		clarification.save_draft(tender=self.name, clarification=first, body="Unsent words", idempotency_key=key(), user=DAVID)
		with self.assertRaises(InputError) as ctx:  # a replacement carries the chair's reason
			self.evl_authorise(replaces=first)
		self.assertIn("replacement_reason", ctx.exception.fields)
		self.end_session()
		second = self.evl_authorise(replaces=first, replacement_reason="Clarify the document reference.")
		replaced = next(c for c in reads.resolve(tender_reference=self.reference, user=SECRETARY)["work"]["clarifications"] if c["name"] == second)
		self.assertEqual(replaced["replace_reason"], "Clarify the document reference.")
		clarification.withdraw(tender=self.name, clarification=first, reason="Clarify the document reference.", idempotency_key=key(), user=SECRETARY)
		self.evl_send(second)
		own = reads.own_clarification(tender_reference=self.reference, clarification=first, user=DAVID)
		self.assertEqual((own["status"], own["withdrawal_reason"], own["reply"]["state"]), ("Withdrawn", "Clarify the document reference.", "Draft"))
		self.assertEqual(own["replacement"]["clarification"], second)
		self.assertEqual(self.refused(self.evl_reply, first).code, "EVL_REPLY_CLOSED")
		self.assertEqual(self.evl_reply(second)["state"], "Sent")
