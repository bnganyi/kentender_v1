# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Decision cycles (AWD-CHG-001 v0.4 §5.7, §5.9 correction-cycle table; AWD-AC-029,
AC-031; tracker AWD4-902)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import corrections, decision, issues, profile, restrictions, simulation, state
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, HOP, AwardCase
from kentender_procurement.award.tests.test_awd_corrections import CORRECTION


class TestCycles(AwardCase):
	def _to_cycle_two(self):
		self.deliver()
		self.awarded()
		self.at("2027-06-18 10:00:00")
		syn.add_correction(self.case().tender, CORRECTION)
		corrections.pull_case(self.case().name)
		issue = issues.open_issues(self.case(), issue_type="Source correction")[0]
		self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=issue.name, outcome="Request corrected evaluation",
			reason="The reported calculation issue may affect the recommendation.", evidence="CN-1", next_action="Request a corrected evaluation report.")
		self.run_as(AO, corrections.record, award=self.case().name, outcome="Request corrected evaluation",
			reason="The reported calculation issue may affect the recommendation.", expected_version=self.version())
		self.at("2027-06-19 09:00:00")
		self.deliver(version=2, delivered_at="2027-06-19 09:00:00")

	def test_successor_cycle(self):
		self._to_cycle_two()
		doc = self.case()
		c2 = state.cycle(doc)
		self.assertEqual((c2.number, c2.awaiting_report, state.current_report(doc).version_number), (2, 0, 2))
		self.assertEqual(state.opinions(doc), [])
		out = self.signed_opinion(conclusion="No current recommendation", reason="The calculation discrepancy remains unresolved.")
		self.assertEqual(out["task"], "Decide correction")
		self.run_as(AO, corrections.record, award=doc.name, outcome="Record no award", reason="The calculation discrepancy remains unresolved.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		doc = self.case()
		self.assertEqual((doc.stage, doc.decision_status, doc.current_cycle), ("Closed", "No award recorded", 2))
		self.assertEqual(state.cycle(doc, 1).decision, state.committed_decision(doc, 1).name)  # cycle 1 unchanged
		self.assertEqual(frappe.db.count(state.EVENT, {"award_case": doc.name}), 2)  # one per committed decision
		self.assertEqual(issues.open_issues(doc, issue_type="Source correction"), [])

	def _held(self):
		self._to_cycle_two()
		self.signed_opinion(reason="The corrected report confirms the recommendation.")
		simulation.set_controls(revised_treatment_unverified=1)
		self.at("2027-06-19 10:00:00")
		self.run_as(AO, corrections.record, award=self.case().name, outcome="Record corrected award", reason="The corrected report confirms the recommendation.",
			expected_version=self.version())
		doc = self.case()
		d = state.committed_decision(doc)
		self.assertEqual((doc.stage, d.kind, d.notices_authorised), ("Notices", "Correction", 0))
		found = issues.open_issues(doc, subtype=corrections.REVISED_TREATMENT)
		self.assertEqual(found[0].title, "Confirm the required notice treatment before this award proceeds.")
		self.assertEqual(frappe.db.count(state.BATCH, {"award_case": doc.name}), 1)  # only the original batch
		return d

	def test_revised_notices_held(self):
		self._held()

	def test_authorise_revised_notices(self):
		d = self._held()
		simulation.set_controls(revised_treatment_unverified=0)
		self.run_as(AO, corrections.record, award=self.case().name, outcome="Authorise revised notices", expected_version=self.version())
		doc = self.case()
		batch = state.current_batch(doc)
		self.assertEqual((batch.kind, batch.version, batch.decision), ("Revised", 2, d.name))
		self.assertEqual(frappe.parse_json(state.notices(batch)[0].content_json)["notice"], "Revised notice 2")
		self.assertEqual(frappe.db.count(state.DECISION, {"award_case": doc.name, "committed": 1}), 2)  # no duplicate decision
		self.assertEqual(frappe.db.count(state.EVENT, {"award_case": doc.name}), 2)

	def test_corrected_award_and_notify_in_one_action(self):
		self._to_cycle_two()
		self.signed_opinion(reason="The corrected report confirms the recommendation.")
		out = self.run_as(AO, corrections.record, award=self.case().name, outcome="Record corrected award", reason="The corrected report confirms the recommendation.",
			expected_version=self.version())
		self.assertTrue(out["batch"])
		self.assertEqual(state.current_batch(self.case()).kind, "Revised")

	def test_returned_successor_opinion(self):
		self._to_cycle_two()
		self.signed_opinion(reason="The corrected report confirms the recommendation.")
		self.run_as(AO, corrections.record, award=self.case().name, outcome="Return for correction", reason="Explain the corrected amount.",
			expected_version=self.version())
		doc = self.case()
		self.assertEqual((doc.stage, doc.current_cycle), ("Opinion", 2))
		out = self.signed_opinion(reason="The corrected amount is explained.")
		self.assertEqual(out["task"], "Decide correction")

	def test_correction_after_no_award(self):
		self.deliver()
		self.signed_opinion(conclusion="No current recommendation", reason="Tender validity expired before an award could be notified.")
		self.run_as(AO, decision.record, award=self.case().name, outcome="No award", reason="Tender validity expired before an award could be notified.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		self.at("2027-10-11 10:00:00")
		syn.add_correction(self.case().tender, CORRECTION)
		corrections.pull_case(self.case().name)
		doc = self.case()
		found = issues.open_issues(doc, issue_type="Source correction")
		self.assertEqual((doc.stage, found[0].title, found[0].holds), ("Closed", "Review the correction to the closed award record.", 0))
