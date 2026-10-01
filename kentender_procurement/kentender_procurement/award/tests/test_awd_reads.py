# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reads, next steps, journey markers and work items (AWD-CHG-001 v0.4 §5.9,
§6; AWD-AC-022, AC-028; tracker AWD4-304, AWD4-305). Each scenario states the
viewer's §5.9 headline, the board's journey code and the task list."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import (
	corrections, decision, eligibility, next_steps, opinion, reads, restrictions, simulation, state, supplier, tasks,
)
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, CASE, DANIEL, DAVID, HOP, MARY, NAOMI, AwardCase


def headline(user: str, name: str = CASE) -> str:
	return next_steps.answer(frappe.get_doc("Award Case", name), user)["headline"]


def code(name: str = CASE) -> str:
	return next_steps.journey(frappe.get_doc("Award Case", name))["code"]


def task_names(user: str) -> list[str]:
	return [t["task"] for t in tasks.all_for_user(user) if t["award"].startswith("AWD-AWT")]


class TestNextSteps(AwardCase):
	def test_opinion_d02(self):
		self.deliver()
		self.assertEqual((headline(HOP), code(), task_names(HOP)), ("Prepare the professional opinion.", "CNNNN", ["Prepare professional opinion"]))
		journey = next_steps.journey(self.case())
		self.assertEqual(journey["stages"][0]["holder"], "Charles Mutiso")
		self.assertEqual(task_names(AO), [])

	def test_decision_d03(self):
		self.deliver()
		self.signed_opinion()
		self.assertEqual((headline(AO), code(), task_names(AO)), ("Decide the award.", "DCNNN", ["Decide award"]))
		self.assertEqual(task_names(HOP), [])

	def test_wait_d05_and_delivered_d06(self):
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.assertEqual(headline(HOP), "The supplier must reply by the date in the notice.")
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=1)
		self.at("2027-06-18 09:05:00")
		self.assertEqual((headline(HOP), code()), ("The required waiting period is still running.", "DDDCN"))
		self.at("2027-07-02 09:00:00")
		eligibility.refresh_case(CASE)
		self.assertEqual((headline(HOP), code()), ("Contracting has received the award.", "DDDDD"))

	def test_receiver_down_v10(self):
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=1)
		simulation.set_controls(contracting_down=1)
		self.at("2027-07-02 09:01:00")
		eligibility.refresh_case(CASE)
		self.assertEqual((headline(HOP), code()), ("Contracting is unavailable. KenTender will check that the award can still proceed before sending it.", "DDDDB"))

	def test_returned_v01(self):
		self.deliver()
		self.signed_opinion()
		self.run_as(AO, decision.record, award=CASE, outcome="Return for correction", reason="Explain the unresolved funding concern before recommending an award.",
			expected_version=self.version())
		self.assertEqual((headline(HOP), code(), task_names(HOP)), ("Resolve the Accounting Officer’s comments.", "CNNNN", ["Resolve returned decision"]))

	def test_source_v02_and_rules_v15(self):
		self.deliver(overrides={"missing_annex": True})
		a = next_steps.answer(self.case(), HOP)
		self.assertEqual((a["kind"], a["headline"], a["sentence"], code()), ("your_turn_blocked", "The evaluation report is incomplete. The Head of Procurement has been notified.",
			"One required annex is unavailable.", "BNNNN"))
		self.assertEqual([f["label"] for f in a["fixes"]], ["View source issue", "Return report"])

	def test_expired_v03_and_no_award_v04(self):
		self.at("2027-10-11 09:00:00")
		self.deliver(overrides={"validity_end": "2027-10-10 11:00:00"})
		self.assertEqual(headline(HOP), "Tender validity has expired. No award can proceed.")
		self.signed_opinion(conclusion="No current recommendation", reason="Tender validity expired before an award could be notified.")
		self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Tender validity expired before an award could be notified.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		a = next_steps.answer(self.case(), HOP)
		self.assertEqual((a["headline"], a["sentence"], code()), ("No award was made.", "Next: Charles Mutiso to review whether the tender should be cancelled.", "DDNNN"))
		self.assertEqual(task_names(HOP), ["Review whether the tender should be cancelled"])

	def test_tie_v18(self):
		self.deliver("036")
		self.assertEqual(headline(HOP, "AWD-AWT-2100-036"), "Review the equal-price outcome.")

	def test_delivery_failure_v05(self):
		self.deliver()
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		self.awarded()
		a = next_steps.answer(self.case(), HOP)
		self.assertEqual((a["headline"], a["sentence"], code(), [f["label"] for f in a["fixes"]]),
			("A required notice is not yet confirmed.", "The notice address was rejected.", "DDBNN", ["Correct contact"]))
		self.assertIn("Resolve notice delivery", task_names(HOP))

	def test_declined_v06_no_response_v07_hold_v08(self):
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=notice.name, response="Decline", notice_version=1, reason="We cannot meet the delivery commitment.")
		self.assertEqual((headline(HOP), code()), ("Review the supplier’s response.", "DDDBN"))
		self.assertIn("Resolve supplier response", task_names(HOP))
		self.at("2027-06-20 11:00:00")
		self.run_as(HOP, restrictions.record_external, award=CASE, basis="Authoritative order", source="Review Board suspension notice", received_at="2027-06-20 11:00:00",
			evidence="PPARB/2027/33", reason="Suspension")
		a = next_steps.answer(self.case(), HOP)
		self.assertEqual((a["headline"], a["sentence"]), ("This award is on hold.", "Review Board suspension notice received 20 Jun 2027, 11:00 EAT"))

	def test_correction_v09_v17_v19(self):
		from kentender_procurement.award.tests.test_awd_corrections import CORRECTION

		self.deliver()
		self.awarded()
		self.at("2027-06-18 10:00:00")
		syn.add_correction(self.case().tender, CORRECTION)
		corrections.pull_case(CASE)
		self.assertEqual((headline(HOP), code()), ("Review the report correction before this award proceeds.", "DDDBN"))
		issue = [o for o in next_steps.outstanding(self.case()) if o.get("issue")][0]["issue"]
		self.run_as(HOP, restrictions.disposition, award=CASE, issue=issue, outcome="Request corrected evaluation",
			reason="The reported calculation issue may affect the recommendation.", evidence="CN-1", next_action="Request a corrected evaluation report addressing the calculation issue.")
		self.assertEqual((headline(AO), task_names(AO)), ("Decide the reported correction.", ["Decide correction"]))
		self.run_as(AO, corrections.record, award=CASE, outcome="Request corrected evaluation", reason="The reported calculation issue may affect the recommendation.",
			expected_version=self.version())
		self.assertEqual((headline(HOP), code()), ("Evaluation is correcting the report.", "BNNNN"))

	def test_cancelled_v11(self):
		from kentender_procurement.award.services import tender_events
		from kentender_procurement.award.tests.test_awd_cancellation import EVENT

		self.deliver()
		self.signed_opinion()
		syn.set_fact(self.case().tender, cancelled=True)
		syn.add_event(self.case().tender, EVENT)
		tender_events.consume_case(CASE)
		a = next_steps.answer(self.case(), HOP)
		self.assertEqual((a["headline"], a["label"], code(), task_names(HOP)), ("This tender was cancelled. Award ended.", "Closed", "DBNNN", []))

	def test_signing_unavailable_v12(self):
		self.deliver()
		self.run_as(HOP, opinion.save, award=CASE, conclusion="Recommend award", reason="ok", expected_version=self.version())
		simulation.set_controls(signing_outcome="Unavailable")
		self.run_as(HOP, opinion.sign, award=CASE, expected_version=self.version())
		a = next_steps.answer(self.case(), HOP)
		self.assertEqual((a["headline"], a["sentence"], code()), ("Signing is unavailable. Your draft has been saved.",
			"Technical operator Daniel Otieno is restoring signing.", "BNNNN"))

	def test_debrief_d07_leads_the_wait(self):
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=1)
		self.run_as(DAVID, supplier.request_explanation, notice=notice.name, request="Please explain the recorded award result.")
		self.assertEqual((headline(HOP), code()), ("Respond to the bidder’s request.", "DDDCN"))
		self.assertIn("Respond to request", task_names(HOP))


class TestReads(AwardCase):
	def test_record_and_access(self):
		self.deliver()
		out = reads.record(award=CASE, user=HOP)
		self.assertEqual((out["report"]["signatures"], out["report"]["valid_until"], out["report"]["recommended"]["submitted"]),
			("3 of 3", "10 Oct 2027, 11:00 EAT", "KES 46,400,000"))
		self.assertTrue(out["actions"]["sign_opinion"])
		self.assertFalse(reads.record(award=CASE, user=AO)["actions"]["sign_opinion"])
		naomi = reads.record(award=CASE, user=NAOMI)
		self.assertFalse(any(naomi["actions"].values()))
		tech = reads.record(award=CASE, user=DANIEL)
		self.assertTrue(tech["technical"])
		self.assertNotIn("report", tech)
		for outsider in (MARY, "Guest"):
			with self.assertRaises(frappe.DoesNotExistError):
				reads.record(award=CASE, user=outsider)

	def test_workspace(self):
		self.deliver()
		ws = reads.workspace(user=HOP)
		mine = [t for t in ws["tasks"] if t["award"] == CASE]
		self.assertEqual(mine, [{"award": CASE, "tender_title": "Supply and delivery of business laptops", "tender_reference": "TND-AWT-2100-033",
			"task": "Prepare professional opinion", "holder": "Charles Mutiso"}])
		self.assertTrue(reads.workspace(user=MARY)["forbidden"])


class TestDissent(AwardCase):
	def test_the_accounting_officer_sees_a_recorded_dissent(self):
		dissent = [{"member": "Ruth Achieng", "statement": "The warranty evidence should have been clarified.", "at": "16 Jun 2027, 13:50 EAT"}]
		self.deliver(overrides={"dissent": dissent})
		self.signed_opinion()
		out = reads.record(award=CASE, user=AO)
		self.assertEqual(out["report"]["dissent"], dissent)
		self.assertEqual((out["report"]["recommended"]["submitted"], out["report"]["recommended"]["evaluated"]), ("KES 46,400,000", "KES 46,400,000"))
