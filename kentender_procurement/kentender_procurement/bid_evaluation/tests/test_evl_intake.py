# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Intake and automatic checks (EVL-CHG-001 v0.4 §5.1, §7.1, §7.3 row 5, §8
EVL_SOURCE_INCOMPLETE; tracker EVL4-501…504, EVL4-510; acceptance EVL-A02,
EVL-A16 (service parts); boards D08-SOURCE, S-CHECKS, D02-NO-BIDS,
D02-INTAKE-FIRST).

One valid nonempty opening creates one intake and one check run and enters
Reviewing with no click; a replay changes nothing; intake before appointment
still runs the checks without giving anyone bid access; a failed intake
records one support issue that every retry reuses, and only success clears
it; a final no-bids opening closes an existing preparation as No evaluation
required; an incomplete opening triggers neither."""

from __future__ import annotations

import frappe

from kentender_core.services import support_issues
from kentender_procurement.bid_evaluation.services import appointment, checks, declaration, intake, my_work_provider, preparation, simulation, sweep
from kentender_procurement.bid_evaluation.tests.support import AO, CHAIR, MEMBER, MEMBER_2, EvaluationCase
from kentender_procurement.bid_submission.tests.support import key

ROSTER = [{"user": CHAIR, "department": "HRM", "capacity": "Chair"}, {"user": MEMBER, "department": "ICT", "capacity": "Member"},
	{"user": MEMBER_2, "department": "Finance", "capacity": "Member"}]


def titles(user: str) -> list[str]:
	return [r["title"] for r in my_work_provider.my_work_rows(user)["assigned"] if r["module"] == "Bid Evaluation"]


class TestIntake(EvaluationCase):
	def case(self):
		return frappe.get_doc("Evaluation Case", {"tender": self.name})

	def test_one_completed_opening_gives_one_intake_one_run_and_reviewing(self):
		preparation.ensure_preparation(tender=self.name)
		self.completed_opening()
		out = intake.receive_opening_package(tender=self.name)
		self.assertTrue(out["received"], out)
		doc = self.case()
		self.assertEqual(doc.state, "Reviewing")
		bids = frappe.get_all("Evaluation Bid", filters={"evaluation_case": doc.name}, fields=["tenderer_name", "submitted_total", "currency", "entry_number"])
		self.assertEqual(len(bids), 1)
		self.assertEqual((bids[0].tenderer_name, bids[0].currency, bids[0].entry_number), ("Afya Digital Supplies Limited", "KES", 1))
		self.assertTrue(bids[0].submitted_total)
		self.assertEqual(frappe.db.get_value("Evaluation Handoff", doc.opening_handoff, "delivery_status"), "Delivered")
		run = checks.current_run(doc.name)
		self.assertGreater(frappe.db.count("Evaluation Check Result", {"check_run": run}), 50)
		# a replay and a sweep change nothing
		again = intake.receive_opening_package(tender=self.name)
		self.assertTrue(again["received"])
		sweep.sweep_tender(self.name)
		self.assertEqual(frappe.db.count("Evaluation Check Run", {"evaluation_case": doc.name}), 1)
		self.assertEqual(frappe.db.count("Evaluation Bid", {"evaluation_case": doc.name}), 1)

	def test_intake_before_appointment_runs_checks_and_gives_no_bid_access(self):
		self.completed_opening()
		self.assertFalse(frappe.db.exists("Evaluation Case", {"tender": self.name}))
		sweep.sweep_tender(self.name)  # recovery path: preparation, then intake
		doc = self.case()
		self.assertEqual((doc.state, doc.prepared_from), ("Reviewing", "Publication"))
		self.assertTrue(checks.current_run(doc.name))
		self.assertIn(f"Appoint evaluation committee for {self.reference}", titles(AO))
		appointment.appoint_committee(tender=self.name, members=ROSTER, appointment_reference="MOH/EVAL/TEST", expected_version=doc.record_version,
			idempotency_key=key(), user=AO)
		self.assertNotIn(f"Review bids for {self.reference}", titles(MEMBER))  # not before the member's own declaration
		declaration.declare_interest(tender=self.name, choice="No conflict to declare", confidentiality_accepted=True, idempotency_key=key(), user=MEMBER)
		self.assertIn(f"Review bids for {self.reference}", titles(MEMBER))
		self.assertEqual(frappe.db.count("Notification Log", {"for_user": MEMBER, "subject": f"Review bids for {self.reference}"}), 1)
		self.assertEqual(frappe.db.count("Evaluation Check Run", {"evaluation_case": doc.name}), 1)  # no second check run

	def test_a_failed_intake_has_one_issue_until_it_succeeds(self):
		preparation.ensure_preparation(tender=self.name)
		self.completed_opening()
		simulation.set_controls(intake_outcome="Unavailable")
		failed = intake.receive_opening_package(tender=self.name)
		self.assertEqual((failed["ok"], failed["code"], failed["message"]), (False, "EVL_SOURCE_INCOMPLETE", "Some opened bid information could not be loaded."))
		again = intake.receive_opening_package(tender=self.name)
		self.assertEqual(again["issue"], failed["issue"])
		issue = support_issues.get(failed["issue"])
		self.assertEqual(issue["status"], "Open")
		self.assertNotIn("Afya", issue["subject"] + issue["safe_detail"])  # no bid content in a support issue
		doc = self.case()
		self.assertEqual((doc.state, frappe.db.get_value("Evaluation Source Intake", failed["intake"], "attempts")), ("Preparing", 2))
		simulation.set_controls(intake_outcome="")
		ok = intake.receive_opening_package(tender=self.name)
		self.assertTrue(ok["received"], ok)
		self.assertEqual(support_issues.get(failed["issue"])["status"], "Resolved")
		self.assertEqual(self.case().state, "Reviewing")


class TestNoBidsAfterPreparation(EvaluationCase):
	"""The preparation exists before the opening ends with no bids, so this
	world is built for the test itself."""

	shared_world = False

	def case(self):
		return frappe.get_doc("Evaluation Case", {"tender": self.name})

	def test_a_final_no_bids_opening_closes_the_preparation(self):
		preparation.ensure_preparation(tender=self.name)
		appointment.appoint_committee(tender=self.name, members=ROSTER, appointment_reference="MOH/EVAL/TEST", expected_version=self.case().record_version,
			idempotency_key=key(), user=AO)
		self.completed_empty_opening()
		sweep.sweep_tender(self.name)
		doc = self.case()
		self.assertEqual((doc.state, doc.closed_reason), ("No evaluation required", "No bids were received. No evaluation is required."))
		self.assertTrue(frappe.db.exists("Evaluation Appointment", {"evaluation_case": doc.name}))  # history kept
		self.assertEqual(titles(MEMBER), [])
		self.assertEqual(titles(AO), [])
		self.assertFalse(frappe.db.exists("Evaluation Check Run", {"evaluation_case": doc.name}))


class TestEmptyWithoutPreparation(EvaluationCase):
	world = "empty"

	def test_no_case_is_created_for_an_empty_opening(self):
		self.completed_empty_opening()
		self.assertEqual(intake.receive_empty_outcome(tender=self.name)["reason"], "no_preparation")
		self.assertEqual(preparation.ensure_preparation(tender=self.name)["reason"], "no_bids")  # the final outcome takes precedence
		self.assertFalse(frappe.db.exists("Evaluation Case", {"tender": self.name}))


class TestIncompleteOpening(EvaluationCase):
	world = "open"

	def test_an_incomplete_opening_is_never_an_empty_one(self):
		preparation.ensure_preparation(tender=self.name)
		self.prepared()
		self.assertEqual(intake.receive_empty_outcome(tender=self.name)["reason"], "not_a_final_empty_opening")
		self.assertEqual(intake.receive_opening_package(tender=self.name)["reason"], "no_completed_opening")
		self.assertEqual(frappe.db.get_value("Evaluation Case", {"tender": self.name}, "state"), "Preparing")
