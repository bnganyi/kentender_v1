# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The report, signing, delivery and what follows (EVL-CHG-001 v0.4 §5.5–§5.7,
§7.3 rows 13–19, §8; tracker EVL4-901…914; acceptance EVL-A10, EVL-A11,
EVL-A13 (service parts); boards D07-*, D08-CORRECTION, D08-PAUSED,
D08-CANCELLED).

Send for signing lists every unresolved item together; once resolved, it
freezes one exact version with a signature target for every current member;
each member signs personally; a stale version or an unconfirmed proof counts
for nothing; the last signature delivers once to the Head of Procurement
with no further click; a failed delivery keeps the signatures and is retried
under the same identity; a concern ends signature collection and a new
version needs fresh signatures; the Head returns a report before any
downstream decision, and never when the decision status is unknown; after an
award decision only a correction notice follows; a suspension pauses work
and a cancellation ends it without a false completion."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_evaluation.services import (
	correction, findings, my_work_provider, report, signing, simulation, tender_events,
)
from kentender_procurement.bid_evaluation.services.errors import EvaluationError
from kentender_procurement.bid_evaluation.tests.support import AO, CHAIR, HOP, MEMBER, MEMBER_2, SECRETARY, EvaluationCase
from kentender_procurement.bid_submission.tests.support import key

MEMBERS = (CHAIR, MEMBER, MEMBER_2)


def titles(user, kind="assigned"):
	return [r["title"] for r in my_work_provider.my_work_rows(user)[kind] if r["module"] == "Bid Evaluation"]


def award_titles(user):
	"""AWD-CHG-001 v0.4 §3: the delivered report's review is Award's work item."""
	from kentender_procurement.award.services import tasks

	return [r["title"] for r in tasks.my_work_rows(user)["assigned"]]


class ReportCase(EvaluationCase):
	def setUp(self):
		super().setUp()
		self.case = self.reviewing()

	def evl_doc(self):
		return frappe.get_doc("Evaluation Case", self.case)

	def evl_ready(self):
		self.resolve_all(self.case)

	def evl_freeze(self):
		draft = report.draft(self.evl_doc())
		return signing.send_for_signing(tender=self.name, expected_version=draft.record_version, idempotency_key=key(), user=SECRETARY)

	def evl_sign(self, user, version=None):
		version = version or signing.signing_version(self.evl_doc()).name
		return signing.sign(tender=self.name, report_version=version, idempotency_key=key(), user=user)

	def refused(self, fn, *args, **kwargs):
		with self.assertRaises(EvaluationError) as ctx:
			fn(*args, **kwargs)
		return ctx.exception


class TestSendAndSign(ReportCase):
	def test_every_unresolved_item_is_listed_together(self):
		error = self.refused(self.evl_freeze)
		self.assertEqual(error.code, "EVL_REPORT_INCOMPLETE")
		issues = error.detail["issues"]
		self.assertGreater(len(issues), 3)
		self.assertTrue(all(i["holder"] == CHAIR for i in issues))
		self.assertEqual(self.evl_doc().state, "Reviewing")
		self.assertFalse(frappe.db.exists("Evaluation Report Version", {"evaluation_case": self.case, "state": "Signing"}))

	def test_the_ordinary_path_to_report_sent(self):
		self.evl_ready()
		built = report.build(self.evl_doc())
		self.assertEqual(built["summary"]["outcome"], "Recommendation")
		self.assertTrue(built["summary"]["recommendation"].startswith("Recommendation: Afya Digital Supplies Limited"))
		self.assertIn("This report does not constitute an award.", built["recommendation"]["statement"])
		self.assertTrue(self.evl_freeze()["ok"])
		self.assertEqual(self.evl_doc().state, "Signing")
		for user in MEMBERS:
			self.assertIn(f"Review and sign report for {self.reference}", titles(user))
		self.assertIn("Waiting for committee signatures", titles(SECRETARY, "waiting"))
		self.evl_sign(CHAIR)
		self.assertEqual(self.evl_doc().state, "Signing")
		self.evl_sign(MEMBER)
		out = self.evl_sign(MEMBER_2)
		self.assertEqual(out["delivery"]["status"], "Delivered")
		self.assertEqual(self.evl_doc().state, "Report sent")
		self.assertEqual(frappe.db.count("Evaluation Report Delivery", {"evaluation_case": self.case}), 1)
		# AWD-CHG-001 v0.4 §3 entry contract: Award received the report, and the
		# recipient's review task is Award's opinion task — one work item, not two.
		self.assertNotIn(f"Review evaluation report for {self.reference}", titles(HOP))
		self.assertIn(f"Prepare professional opinion for {self.reference}", award_titles(HOP))
		self.assertEqual(titles(MEMBER), [])
		delivered = frappe.db.get_value("Evaluation Report Version", {"evaluation_case": self.case, "state": "Delivered"}, "name")
		with self.assertRaises(frappe.DoesNotExistError):
			self.evl_sign(SECRETARY, version=delivered)  # the secretary never signs

	def test_a_stale_version_or_unconfirmed_proof_counts_for_nothing(self):
		self.evl_ready()
		first = self.evl_freeze()["report"]
		signing.raise_report_concern(tender=self.name, reason="The report refers to page 3; the service address is on page 2.", idempotency_key=key(), user=MEMBER)
		self.assertEqual(self.evl_doc().state, "Reviewing")
		self.assertIn(f"Resolve report concern for {self.reference}", titles(CHAIR))
		self.evl_freeze()
		self.assertEqual(self.refused(self.evl_sign, CHAIR, version=first).code, "EVL_TARGET_CHANGED")
		self._flag("kt_prc_signing_outcome", "Indeterminate")
		out = self.evl_sign(CHAIR)
		self.assertEqual((out["ok"], out["code"]), (False, "EVL_SIGNATURE_UNCONFIRMED"))
		self.assertIn(f"Review and sign report for {self.reference}", titles(CHAIR))  # still owed

	def test_a_failed_delivery_keeps_the_signatures(self):
		self.evl_ready()
		self.evl_freeze()
		simulation.set_controls(delivery_outcome="Failed")
		for user in MEMBERS:
			out = self.evl_sign(user)
		self.assertEqual((out["delivery"]["status"], out["delivery"]["code"]), ("Failed", "EVL_REPORT_DELIVERY_FAILED"))
		self.assertEqual(self.evl_doc().state, "Signing")
		simulation.set_controls(delivery_outcome="")
		retried = signing.retry_delivery(tender=self.name, idempotency_key=key(), user=SECRETARY)
		self.assertEqual(retried["status"], "Delivered")
		self.assertEqual(self.evl_doc().state, "Report sent")
		self.assertEqual(frappe.db.count("Evaluation Report Delivery", {"evaluation_case": self.case}), 1)


class TestAfterDelivery(ReportCase):
	def setUp(self):
		super().setUp()
		self.evl_ready()
		self.evl_freeze()
		for user in MEMBERS:
			self.evl_sign(user)

	def test_return_before_a_decision_and_never_on_an_unknown_status(self):
		simulation.set_controls(downstream_status="Unknown")
		self.assertEqual(self.refused(correction.return_report, tender=self.name, comment="Correct the page reference.", idempotency_key=key(), user=HOP).code,
			"EVL_DECISION_STATUS_UNKNOWN")
		simulation.set_controls(downstream_status="")
		out = correction.return_report(tender=self.name, comment="Correct the service-address page reference from page 3 to page 2.", idempotency_key=key(),
			user=HOP)
		self.assertTrue(out["ok"])
		self.assertEqual(self.evl_doc().state, "Reviewing")
		self.assertIn(f"Correct evaluation report for {self.reference}: Correct the service-address page reference from page 3 to page 2.", titles(SECRETARY))
		self.assertEqual(frappe.db.get_value("Evaluation Report Version", {"evaluation_case": self.case, "version_number": 1}, "state"), "Returned")

	def test_an_unknown_decision_status_is_reported_to_support(self):
		from kentender_core.services import support_issues

		simulation.set_controls(downstream_status="Unknown")
		with self.assertRaises(frappe.DoesNotExistError):
			correction.report_status_issue(tender=self.name, description="x", idempotency_key=key(), user=MEMBER)  # the Head or the chair only
		out = correction.report_status_issue(tender=self.name, description="The later decision could not be checked.", idempotency_key=key(), user=HOP)
		issue = support_issues.get(out["issue"])
		self.assertEqual((issue["status"], issue["holder_role"]), ("Open", "Evaluation Technical Support"))
		# KT-STD-001 v1.13 §8.3: Evaluation's own support holder, not the Technical Operator's work
		self.assertFalse(set(issue["holder_users"]) & set(support_issues.holders("Technical Operator")))
		self.assertNotIn("Afya", issue["subject"] + issue["safe_detail"])
		again = correction.report_status_issue(tender=self.name, description="Still unknown.", idempotency_key=key(), user=CHAIR)
		self.assertEqual(again["issue"], out["issue"])  # one issue for the one operation
		simulation.set_controls(downstream_status="")
		correction.return_report(tender=self.name, comment="Correct the service-address page reference from page 3 to page 2.", idempotency_key=key(), user=HOP)
		self.assertEqual(support_issues.get(out["issue"])["status"], "Resolved")  # the status could be read again

	def test_after_an_award_decision_only_a_correction_notice(self):
		tender_events.record_simulated_event(tender=self.name, kind="Award decision", instruction_reference="MOH/AWARD/TEST", authority=AO,
			effective_at=str(frappe.flags.kt_evl_clock))
		self.assertEqual(self.refused(correction.return_report, tender=self.name, comment="x", idempotency_key=key(), user=HOP).code, "EVL_VERSION_CONFLICT")
		out = correction.record_correction_notice(tender=self.name, reason="The report gives the wrong page reference for the service address.",
			correction="Read page 2, section 3, instead of page 3.", idempotency_key=key(), user=CHAIR)
		self.assertEqual(out["downstream_status"], "Award decision recorded")
		self.assertIn(f"Review report correction for {self.reference}", titles(HOP) + award_titles(HOP))
		self.assertEqual(self.evl_doc().state, "Report sent")  # never reopened


class TestPauseAndCancel(ReportCase):
	def test_a_suspension_pauses_and_a_cancellation_ends(self):
		tender_events.record_simulated_event(tender=self.name, kind="Suspension", instruction_reference="MOH/REVIEW/TEST", authority=AO)
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")
		requirement = self.requirement(self.case, "Memory")["requirement_key"]
		error = self.refused(findings.record_evidence_finding, tender=self.name, bid=bid, requirement_key=requirement, result="Meets", reason="x",
			idempotency_key=key(), user=MEMBER)
		self.assertEqual((error.code, error.detail["instruction"]), ("EVL_SUSPENDED", "MOH/REVIEW/TEST"))
		tender_events.record_simulated_event(tender=self.name, kind="Resumption", instruction_reference="MOH/REVIEW/TEST-R", authority=AO)
		self.assertTrue(findings.record_evidence_finding(tender=self.name, bid=bid, requirement_key=requirement, result="Meets", reason="Reviewed.",
			idempotency_key=key(), user=MEMBER)["ok"])
		tender_events.record_simulated_event(tender=self.name, kind="Cancellation", instruction_reference="MOH/CANCEL/TEST", authority=AO,
			reason="Procurement proceedings terminated under the recorded decision.")
		doc = self.evl_doc()
		self.assertEqual(doc.state, "Cancelled")
		self.assertEqual(frappe.db.get_value("Proceeding", doc.proceeding, "state"), "Aborted after start")
		self.assertEqual(titles(MEMBER), [])
		self.assertEqual(titles(CHAIR), [])
		self.assertFalse(frappe.db.exists("Evaluation Report Delivery", {"evaluation_case": self.case}))
