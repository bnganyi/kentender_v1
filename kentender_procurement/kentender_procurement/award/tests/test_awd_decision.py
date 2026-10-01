# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RecordAwardDecision and AwardDecisionRecorded v1 (AWD-CHG-001 v0.4 §5.3,
§5.8; AWD-AC-004, AC-005, AC-007, AC-031; tracker AWD4-401, AWD4-402)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import decision, opinion, simulation, state
from kentender_procurement.award.services.errors import AwardError, InputError
from kentender_procurement.award.tests.support import AO, CASE, HOP, AwardCase


class TestDecision(AwardCase):
	def test_award_queues_batch(self):
		self.deliver()
		out = self.awarded()
		self.assertTrue(out["ok"])
		doc = self.case()
		d = state.committed_decision(doc)
		self.assertEqual((d.outcome, d.supplier_name, d.submitted_amount, d.evaluated_amount, d.decided_by), ("Award", "Afya Digital Supplies Limited",
			"46400000.00", "46400000.00", AO))
		self.assertEqual(doc.decision_status, "Award recorded")
		self.assertEqual(doc.notification_status, "Issued")
		batch = state.current_batch(doc)
		self.assertEqual((batch.state, batch.status, batch.authorised_by), ("Issued", "Issued", AO))
		self.assertEqual([n.status for n in state.notices(batch)], ["Given"])
		self.assertEqual(doc.stage, "Waiting to proceed")
		self.assertEqual(frappe.db.count(state.EVENT, {"award_case": CASE}), 1)
		event = frappe.get_doc(state.EVENT, {"decision": d.name})
		self.assertEqual(event.status, "Delivered")
		self.assertIn('"outcome": "Award"', event.payload_json)

	def test_only_the_accounting_officer_decides(self):
		self.deliver()
		self.signed_opinion()
		with self.assertRaises(AwardError) as ctx:
			self.run_as(HOP, decision.record, award=CASE, outcome="Award", reason="x", expected_version=self.version())
		self.assertEqual(ctx.exception.code, "AWD_AUTHORITY_REQUIRED")

	def test_no_award_follow_up(self):
		self.deliver()
		self.signed_opinion()
		with self.assertRaises(InputError):
			self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Tender validity expired.", next_action="", expected_version=self.version())
		out = self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Tender validity expired before an award could be notified.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		doc = self.case()
		self.assertEqual((doc.stage, doc.outcome, doc.decision_status, doc.notification_status), ("Closed", "No award", "No award recorded", "Not issued"))
		d = state.committed_decision(doc)
		self.assertEqual((d.next_action, d.next_action_owner, d.next_action_state), ("Review whether the tender should be cancelled", HOP, "Open"))
		event = frappe.get_doc(state.EVENT, {"decision": d.name})
		self.assertNotIn("supplier", event.payload_json)
		self.assertEqual(frappe.db.count("Award Test Contracting Inbox", {"reference": event.event_id, "publication_obligation": 1}), 0)
		self.assertTrue(out["ok"])

	def test_return_creates_one_task_and_no_event(self):
		self.deliver()
		self.signed_opinion()
		self.run_as(AO, decision.record, award=CASE, outcome="Return for correction", reason="Explain the unresolved funding concern before recommending an award.",
			expected_version=self.version())
		doc = self.case()
		self.assertEqual(doc.stage, "Opinion")
		self.assertEqual(doc.decision_status, "No decision recorded")
		self.assertEqual(frappe.db.count(state.EVENT, {"award_case": CASE}), 0)
		self.assertEqual(state.opinions(doc)[0].state, "Superseded")
		# a fresh opinion returns to the AO
		self.signed_opinion()
		self.assertEqual(self.case().stage, "Decision")
		self.assertEqual(len(state.opinions(self.case())), 2)

	def test_tie_blocks_the_positive_decision(self):
		self.deliver("036")
		name = "AWD-AWT-2100-036"
		self.signed_opinion(name, conclusion="No current recommendation", reason="Refer the unresolved tie to the Accounting Officer for a lawful next step.")
		with self.assertRaises(AwardError) as ctx:
			self.run_as(AO, decision.record, award=name, outcome="Award", reason="x", expected_version=self.version(name))
		self.assertIn("AWD_NO_SUPPORTED_AWARD", [r["code"] for r in ctx.exception.reasons])
		self.assertTrue(self.run_as(AO, decision.record, award=name, outcome="No award", reason="The tie is unresolved.",
			next_action="Prepare a lawful next procurement step for the Accounting Officer's decision", expected_version=self.version(name))["ok"])

	def test_expired_validity_blocks_award_but_allows_no_award(self):
		self.deliver()
		self.signed_opinion()
		self.at("2027-10-11 09:00:00")
		with self.assertRaises(AwardError) as ctx:
			self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="x", expected_version=self.version())
		self.assertIn("AWD_VALIDITY_EXPIRED", [r["code"] for r in ctx.exception.reasons])
		self.assertTrue(self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Tender validity expired before an award could be notified.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())["ok"])

	def test_a_retry_returns_the_original_decision_and_event(self):
		self.deliver()
		self.signed_opinion()
		key, expected = self.key("dec"), self.version()
		first = self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="ok", expected_version=expected, idempotency_key=key)
		again = self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="ok", expected_version=expected, idempotency_key=key)
		self.assertEqual(first, again)
		self.assertEqual(frappe.db.count(state.DECISION, {"award_case": CASE}), 1)
		self.assertEqual(frappe.db.count(state.EVENT, {"award_case": CASE}), 1)

	def test_event_delivery_failure_keeps_the_event_for_retry(self):
		from kentender_procurement.award.services import events

		self.deliver()
		self.signed_opinion()
		simulation.set_controls(event_delivery_down=1)
		self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="ok", expected_version=self.version())
		event = frappe.get_doc(state.EVENT, {"award_case": CASE})
		self.assertEqual(event.status, "Failed")
		simulation.set_controls(event_delivery_down=0)
		self.assertEqual(events.retry_pending(), 1)
		self.assertEqual(frappe.db.get_value(state.EVENT, event.name, "status"), "Delivered")
		self.assertEqual(frappe.db.count(state.EVENT, {"award_case": CASE}), 1)
