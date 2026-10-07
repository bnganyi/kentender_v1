# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Findings, concerns and committee discussion (EVL-CHG-001 v0.4 §4.3, §5.2,
§7.2, §7.3 row 6; tracker EVL4-601…608; acceptance EVL-A05, EVL-A17 (service
parts); boards D04, D04-CONCERN, D05, D05-START, D05-ABSENT, D05-CONCLUSION,
D05-CONCLUSION-Q, D05-MEMBER, D05-DISAGREE, D08-RULE).

A member's evidence finding completes a requirement with no second
approval; Needs review opens one chair item for that bid and requirement;
Start records the chair's attendance; everyone else joins personally; a
conclusion needs the whole current eligible roster present, resolves or
qualifies, cannot waive a failed requirement, and clears the item once; the
secretary records but decides nothing alone; disagreement keeps its author;
a lapse removes a member from the decision until they rejoin; a reported
rule issue passes the item to support and is resolved only by the corrected
run."""

from __future__ import annotations

import frappe

from kentender_core.services import support_issues
from kentender_procurement.bid_evaluation.services import (
	checks, comparison, conclusion, discussion, findings, issues, my_work_provider, report, signing,
)
from kentender_procurement.bid_evaluation.services.errors import EvaluationError, InputError
from kentender_procurement.bid_evaluation.tests.support import CHAIR, MEMBER, MEMBER_2, OUTSIDER, SECRETARY, EvaluationCase
from kentender_procurement.bid_submission.tests.support import key


def titles(user: str, kind: str = "assigned") -> list[str]:
	return [r["title"] for r in my_work_provider.my_work_rows(user)[kind] if r["module"] == "Bid Evaluation"]


class DiscussionCase(EvaluationCase):
	def setUp(self):
		super().setUp()
		self.case = self.reviewing()
		self.service = self.requirement(self.case, "Service location")
		self.bid = self.service["bid"]

	def evl_find(self, label, result, reason="Recorded evidence reviewed.", user=MEMBER):
		return findings.record_evidence_finding(tender=self.name, bid=self.bid, requirement_key=self.requirement(self.case, label)["requirement_key"],
			result=result, reason=reason, evidence_reference="Kenya service-centre details", idempotency_key=key(), user=user)

	def evl_start(self):
		return discussion.start_discussion(tender=self.name, subject="Service-location evidence", idempotency_key=key(), user=CHAIR)

	def evl_join(self, user):
		return discussion.join_discussion(tender=self.name, idempotency_key=key(), user=user)

	def evl_conclude(self, result="Meets", reason="Page 2, section 3 identifies the Nairobi service address.", qualified=False, user=CHAIR, label="Service location"):
		return conclusion.record_conclusion(tender=self.name, bid=self.bid, requirement_key=self.requirement(self.case, label)["requirement_key"], result=result,
			reason=reason, qualified=qualified, idempotency_key=key(), user=user)

	def refused(self, fn, *args, **kwargs):
		with self.assertRaises((EvaluationError, InputError)) as ctx:
			fn(*args, **kwargs)
		return ctx.exception


class TestFindings(DiscussionCase):
	def test_a_member_finding_completes_evidence_without_a_second_approval(self):
		self.assertEqual(self.requirement(self.case, "Memory")["result"], "Needs review")
		self.assertTrue(self.evl_find("Memory", "Meets")["ok"])
		memory = self.requirement(self.case, "Memory")
		self.assertEqual((memory["result"], memory["basis"]), ("Meets", "Member evidence finding"))
		self.assertNotIn(f"Resolve evaluation concern for {self.reference}", titles(CHAIR))  # nothing for the chair to approve

	def test_needs_review_opens_one_chair_item(self):
		first = self.evl_find("Service location", "Needs review", "The submitted evidence does not clearly identify the service address.")
		second = findings.raise_concern(tender=self.name, bid=self.bid, requirement_key=self.service["requirement_key"],
			reason="The datasheet and offered response need to be compared.", idempotency_key=key(), user=MEMBER_2)
		self.assertEqual(first["discussion_item"], second["discussion_item"])
		self.assertEqual(frappe.db.count("Evaluation Discussion Item", {"evaluation_case": self.case, "status": "Open"}), 1)
		self.assertEqual([t for t in titles(CHAIR) if t.startswith("Resolve")], [f"Resolve evaluation concern for {self.reference}"])
		self.assertIn("Waiting for committee response", titles(MEMBER, "waiting"))
		self.assertEqual(self.requirement(self.case, "Service location")["result"], "Needs review")

	def test_only_eligible_members_record_findings(self):
		with self.assertRaises(frappe.DoesNotExistError):
			self.evl_find("Memory", "Meets", user=OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			self.evl_find("Memory", "Meets", user=SECRETARY)  # the secretary decides nothing
		error = self.refused(self.evl_find, "Memory", "Perhaps")
		self.assertIn("result", error.fields)


class TestDiscussion(DiscussionCase):
	def test_the_ordinary_conclusion(self):
		self.evl_find("Service location", "Needs review", "The submitted evidence does not clearly identify the service address.")
		started = self.evl_start()
		self.assertTrue(started["ok"])
		self.assertEqual(discussion.present(frappe.get_doc("Evaluation Case", self.case)), [CHAIR])  # Start records the chair's attendance
		self.evl_join(MEMBER)
		self.evl_join(SECRETARY)
		error = self.refused(self.evl_conclude)
		self.assertEqual((error.code, error.detail["absent"]), ("EVL_MEMBERS_ABSENT", [MEMBER_2]))
		self.evl_join(MEMBER_2)
		out = self.evl_conclude(user=SECRETARY)  # the secretary records the collective outcome
		self.assertEqual(sorted(out["participants"]), sorted([CHAIR, MEMBER, MEMBER_2, SECRETARY]))
		service = self.requirement(self.case, "Service location")
		self.assertEqual((service["result"], service["basis"]), ("Meets", "Committee conclusion"))
		self.assertEqual(frappe.db.get_value("Evaluation Discussion Item", {"evaluation_case": self.case}, "status"), "Resolved")
		self.assertNotIn(f"Resolve evaluation concern for {self.reference}", titles(CHAIR))
		discussion.end_discussion(tender=self.name, idempotency_key=key(), user=CHAIR)
		self.assertEqual(discussion.present(frappe.get_doc("Evaluation Case", self.case)), [])

	def test_a_departure_pauses_decisions_but_not_notes(self):
		self.evl_start()
		for user in (MEMBER, MEMBER_2, SECRETARY):
			self.evl_join(user)
		discussion.leave_discussion(tender=self.name, idempotency_key=key(), user=MEMBER_2)
		self.assertEqual(self.refused(self.evl_conclude).detail["absent"], [MEMBER_2])
		note = discussion.record_note(tender=self.name, subject="Afya service-location evidence", note="Ask the bidder to identify the address.",
			reason="The supporting document is unclear.", idempotency_key=key(), user=SECRETARY)
		self.assertTrue(note["ok"])
		self.evl_join(MEMBER_2)
		self.assertTrue(self.evl_conclude()["ok"])

	def test_a_lapsed_member_is_not_present(self):
		self.set_lapse(60)
		self.at("2027-06-14 09:00:00")
		self.evl_start()
		for user in (MEMBER, MEMBER_2):
			self.evl_join(user)
		self.at("2027-06-14 09:05:00")
		for user in (CHAIR, MEMBER):
			discussion.heartbeat(tender=self.name, user=user)
		self.assertEqual(self.refused(self.evl_conclude).detail["absent"], [MEMBER_2])
		self.evl_join(MEMBER_2)
		self.assertTrue(self.evl_conclude()["ok"])

	def test_resolve_or_qualify_but_never_waive(self):
		self.evl_start()
		for user in (MEMBER, MEMBER_2):
			self.evl_join(user)
		self.assertIn("result", self.refused(self.evl_conclude, result="Needs review").fields)
		out = self.evl_conclude(result="Needs review", reason="The committee cannot establish the address from the submitted evidence.", qualified=True)
		self.assertEqual(out["kind"], "Qualified report")
		with self.assertRaises(frappe.DoesNotExistError):
			self.evl_conclude(user=MEMBER)  # a member does not record conclusions

	def test_disagreement_keeps_its_author(self):
		self.evl_start()
		for user in (MEMBER, MEMBER_2):
			self.evl_join(user)
		recorded = self.evl_conclude()
		said = conclusion.record_disagreement(tender=self.name, statement="The address should be verified against the original document.",
			conclusion=recorded["conclusion"], idempotency_key=key(), user=MEMBER_2)
		row = frappe.get_doc("Evaluation Disagreement", said["disagreement"])
		self.assertEqual((row.member_user, row.statement), (MEMBER_2, "The address should be verified against the original document."))
		self.assertEqual(frappe.db.get_value("Proceeding Event", row.proceeding_event, "actor"), MEMBER_2)
		with self.assertRaises(frappe.DoesNotExistError):
			conclusion.record_disagreement(tender=self.name, statement="On behalf of a member", conclusion=recorded["conclusion"], idempotency_key=key(),
				user=SECRETARY)


class TestRuleIssue(DiscussionCase):
	def test_a_rule_issue_goes_to_support_and_clears_on_the_corrected_run(self):
		out = issues.report_issue(tender=self.name, bid=self.bid, requirement_key=self.requirement(self.case, "Storage capacity")["requirement_key"],
			description="The automatic comparison rule is unavailable.", idempotency_key=key(), user=CHAIR)
		self.assertEqual(support_issues.get(out["issue"])["status"], "Open")
		self.assertEqual(frappe.db.get_value("Evaluation Discussion Item", {"evaluation_case": self.case}, ["status", "resolution_kind"]),
			("Transferred", "Support issue"))
		run = checks.current_run(self.case)
		frappe.db.set_value("Evaluation Check Run", run, "rules_digest", "the-defective-rules")  # as if the rules were corrected since
		self.assertTrue(issues.reconcile_rules(self.name)["ok"])
		self.assertNotEqual(checks.current_run(self.case), run)
		self.assertEqual(frappe.db.get_value("Evaluation Check Run", run, "superseded_by"), checks.current_run(self.case))  # the earlier run is kept
		self.assertEqual(support_issues.get(out["issue"])["status"], "Resolved")


class TestFailedRequirement(DiscussionCase):
	overrides = {"memory": 8}

	def test_a_failed_requirement_cannot_be_waived(self):
		contrary = self.evl_find("Memory", "Meets", "The datasheet shows 16 GB.")
		self.assertEqual(contrary["kind"], "Contrary finding")
		self.assertTrue(contrary["discussion_item"])
		self.assertEqual(self.requirement(self.case, "Memory")["result"], "Does not meet")
		self.evl_start()
		for user in (MEMBER, MEMBER_2):
			self.evl_join(user)
		self.assertIn("cannot be waived", self.refused(self.evl_conclude, label="Memory").fields["result"])
		self.assertEqual(comparison.compare(self.case, with_funding=False)["outcome"], "No responsive bids")


PRICE = "Tender price"
DISCREPANCY = "The submitted total 46000000.00 differs from the calculated 46400000.00."


class TestPriceDiscrepancy(DiscussionCase):
	"""EVL §4.4: an arithmetic discrepancy stays visible; a committee explanation cannot
	substitute for a missing legal or published basis (AUD-EVL-003), so it can only be
	qualified in the report (AUD-EVL-002)."""

	def setUp(self):
		super().setUp()
		frappe.db.set_value("Evaluation Check Result", {"check_run": checks.current_run(self.case), "check_kind": "calculation"},
			{"result": "Needs review", "reason": DISCREPANCY})  # the Tender's published calculation disagrees with the submitted total
		self.resolve_all(self.case, skip=(PRICE,))

	def test_a_member_finding_cannot_resolve_the_discrepancy(self):
		self.assertEqual(self.requirement(self.case, PRICE)["result"], "Needs review")
		self.assertIn("arithmetic discrepancy", self.refused(self.evl_find, PRICE, "Meets", "The totals are close enough.").fields["result"])
		self.assertFalse(frappe.db.exists("Evaluation Finding", {"evaluation_case": self.case, "requirement_key": self.requirement(self.case, PRICE)["requirement_key"]}))
		price = self.requirement(self.case, PRICE)
		self.assertEqual((price["result"], price["basis"]), ("Needs review", "Automatic check"))
		row = comparison.compare(self.case, with_funding=False)["rows"][0]
		self.assertEqual((row["evaluated_total"], row["position"]), ("Needs review", "Not ranked"))  # never ranked on the submitted total

	def test_even_a_committee_conclusion_cannot_resolve_it_but_can_qualify_it(self):
		self.evl_start()
		for user in (MEMBER, MEMBER_2):
			self.evl_join(user)
		self.assertIn("arithmetic discrepancy", self.refused(self.evl_conclude, label=PRICE).fields["result"])
		self.assertEqual(self.requirement(self.case, PRICE)["result"], "Needs review")
		out = self.evl_conclude(label=PRICE, result="Needs review", qualified=True, reason="The Tender publishes no disposition for a total that differs from the calculation.")
		self.assertEqual(out["kind"], "Qualified report")
		table = comparison.compare(self.case, with_funding=False)
		self.assertEqual((table["outcome"], table["recommended"]), ("Qualified report", None))
		self.assertFalse(table["provisional"])


class TestQualifiedReport(DiscussionCase):
	"""EVL §5.5 (AUD-EVL-002): a requirement recorded for a qualified report freezes as one."""

	def test_a_qualified_unresolved_requirement_can_be_frozen_for_signing(self):
		self.resolve_all(self.case, skip=("Service location",))
		draft = report.draft(frappe.get_doc("Evaluation Case", self.case))
		error = self.refused(signing.send_for_signing, tender=self.name, expected_version=draft.record_version, idempotency_key=key(), user=SECRETARY)
		self.assertEqual(error.code, "EVL_REPORT_INCOMPLETE")  # still unresolved with no committee disposition
		self.evl_start()
		for user in (MEMBER, MEMBER_2):
			self.evl_join(user)
		self.evl_conclude(result="Needs review", qualified=True, reason="The committee cannot establish the service address from the submitted evidence.")
		doc = frappe.get_doc("Evaluation Case", self.case)
		built = report.build(doc)
		self.assertEqual(built["recommendation"]["outcome"], "Qualified report")
		self.assertIsNone(built["recommendation"]["recommended"])
		self.assertFalse(built["recommendation"]["provisional"])
		# a discussion left active blocks freezing (§5.5), so it ends first
		discussion.end_discussion(tender=self.name, idempotency_key=key(), user=CHAIR)
		out = signing.send_for_signing(tender=self.name, expected_version=report.draft(doc).record_version, idempotency_key=key(), user=SECRETARY)
		self.assertTrue(out["ok"], out)
		self.assertEqual(frappe.get_doc("Evaluation Case", self.case).state, "Signing")
		self.assertEqual(frappe.db.get_value("Evaluation Report Version", out["report"], "outcome"), "Qualified report")
