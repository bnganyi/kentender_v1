# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Attention banner copy must not show Ready under Needs attention."""

from __future__ import annotations

from types import SimpleNamespace

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
	_attention_message,
)


class TestPlanItemEditorAttentionMessage(IntegrationTestCase):
	def test_ready_projection_hides_attention_banner(self) -> None:
		iv = SimpleNamespace(validation_projection="Ready")
		fields = {
			"lotting_decision": "Single lot",
			"ms_invitation_published": "2027-09-15",
			"ms_tender_opening": "2027-10-20",
			"ms_evaluation_completed": "2027-11-15",
			"ms_award_approval": "2027-12-15",
			"ms_contract_signature": "2028-01-15",
			"ms_delivery_completion": "2028-03-31",
		}
		self.assertEqual(_attention_message(iv=iv, fields=fields), "")

	def test_ready_never_used_as_banner_body(self) -> None:
		iv = SimpleNamespace(validation_projection="Ready")
		msg = _attention_message(iv=iv, fields={"lotting_decision": "Single lot"})
		# Missing milestones still produce guidance — but never the bare label "Ready".
		self.assertNotEqual(msg, "Ready")

	def test_needs_attention_uses_human_copy(self) -> None:
		iv = SimpleNamespace(validation_projection="Needs attention")
		fields = {
			"lotting_decision": "Single lot",
			"ms_invitation_published": "2027-09-15",
			"ms_tender_opening": "2027-10-20",
			"ms_evaluation_completed": "2027-11-15",
			"ms_award_approval": "2027-12-15",
			"ms_contract_signature": "2028-01-15",
			"ms_delivery_completion": "2028-03-31",
		}
		msg = _attention_message(iv=iv, fields=fields)
		self.assertTrue(msg)
		self.assertNotEqual(msg, "Ready")
		self.assertNotEqual(msg, "Needs attention")

	def test_chronology_field_issue_surfaces_in_banner(self) -> None:
		iv = SimpleNamespace(validation_projection="Blocked")
		fields = {
			"lotting_decision": "Single lot",
			"ms_invitation_published": "2027-09-15",
			"ms_tender_opening": "2027-10-20",
			"ms_evaluation_completed": "2027-10-10",
			"ms_award_approval": "2027-12-15",
			"ms_contract_signature": "2028-01-15",
			"ms_delivery_completion": "2028-03-31",
		}
		msg = _attention_message(
			iv=iv,
			fields=fields,
			field_issues={
				"ms_evaluation_completed": "Milestone dates must be in chronological order."
			},
		)
		self.assertIn("chronolog", msg.lower())
