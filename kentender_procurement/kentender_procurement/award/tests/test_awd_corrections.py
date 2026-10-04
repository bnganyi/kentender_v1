# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-decision correction review (AWD-CHG-001 v0.4 §5.7, §5.10; AWD-AC-017;
tracker AWD4-901)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import corrections, eligibility, issues, restrictions, state
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, HOP, AwardCase

CORRECTION = {"source_event": "SYN-CN:1", "kind": "Report correction", "reference": "SYN-CN-1", "reason": "Evaluation reported a material calculation issue.",
	"detail": "The line total was recalculated.", "effective_at": "2027-06-18 09:30:00"}


class TestCorrection(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.awarded()
		self.at("2027-06-18 10:00:00")
		syn.add_correction(self.case().tender, CORRECTION)
		corrections.pull_case(self.case().name)
		self.issue = issues.open_issues(self.case(), issue_type="Source correction")[0]

	def test_correction_holds(self):
		self.assertEqual((self.issue.title, self.issue.holds, self.issue.reason),
			("Review the report correction before this award proceeds.", 1, "Evaluation reported a material calculation issue."))
		self.assertFalse(eligibility.conditions(self.case())["6"]["met"])
		self.assertEqual(state.committed_decision(self.case()).outcome, "Award")  # the original decision is kept
		corrections.pull_case(self.case().name)
		self.assertEqual(len(issues.open_issues(self.case(), issue_type="Source correction")), 1)

	def test_no_material_effect_closes_only_that_issue(self):
		self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=self.issue.name, outcome="No material effect",
			reason="The recalculated total is unchanged.", evidence="Correction notice CN-1")
		self.assertEqual(issues.open_issues(self.case(), issue_type="Source correction"), [])
		self.assertEqual(self.case().current_cycle, 1)

	def test_ao_request_corrected_evaluation(self):
		self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=self.issue.name, outcome="Request corrected evaluation",
			reason="The reported calculation issue may affect the recommendation.", evidence="Correction notice CN-1",
			next_action="Request a corrected evaluation report addressing the calculation issue.")
		self.assertTrue(restrictions.proposals(self.case()))
		with self.assertRaises(AwardError):
			self.run_as(HOP, corrections.record, award=self.case().name, outcome="Request corrected evaluation", reason="x", expected_version=self.version())
		self.at("2027-06-18 10:05:00")
		out = self.run_as(AO, corrections.record, award=self.case().name, outcome="Request corrected evaluation",
			reason="The reported calculation issue may affect the recommendation.", expected_version=self.version())
		self.assertEqual(out["cycle"], 2)
		doc = self.case()
		c2, c1 = state.cycle(doc), state.cycle(doc, 1)
		self.assertEqual((doc.current_cycle, doc.stage, c2.awaiting_report, c2.predecessor), (2, "Opinion", 1, c1.name))
		self.assertEqual((c1.stage, c1.decision), ("Waiting to proceed", state.committed_decision(doc, 1).name))
		self.assertEqual(doc.decision_status, "Award recorded")  # history retained; a new cycle is not "no decision"
		self.assertEqual(frappe.db.count(state.EVENT, {"award_case": doc.name}), 1)  # an instruction creates no decision event
		self.assertEqual(len(issues.open_issues(doc, issue_type="Source correction")), 1)  # the hold is retained

	def test_decline_reconsideration(self):
		self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=self.issue.name, outcome="Request decision review",
			reason="Possible effect.", evidence="CN-1", next_action="Decide whether to reconsider.")
		self.run_as(AO, corrections.record, award=self.case().name, outcome="Decline reconsideration", reason="The recommendation stands.",
			expected_version=self.version())
		doc = self.case()
		self.assertEqual((doc.current_cycle, issues.open_issues(doc, issue_type="Source correction")), (1, []))
