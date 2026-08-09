# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-01 workspace API contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.api import _action_for, list_demands_workspace


class TestDemandsWorkspaceApi(IntegrationTestCase):
	def test_list_demands_workspace_shape(self):
		frappe.set_user("Administrator")
		payload = list_demands_workspace(page=1, page_size=20)
		self.assertTrue(payload.get("ok"))
		self.assertIn("summary", payload)
		self.assertIn("rows", payload)
		summary = payload["summary"]
		for key in ("my_drafts", "returned_to_me", "my_approvals", "budget_confirmations"):
			self.assertIn(key, summary)
			self.assertIsInstance(summary[key], int)
		self.assertIsInstance(payload["rows"], list)
		self.assertEqual(payload["page"], 1)
		self.assertLessEqual(len(payload["rows"]), 20)

	def test_action_route_budget_return_opens_review_not_form(self):
		"""Budget Confirmation Return → Procurement Enrichment must not open demand-form."""
		label, route = _action_for(
			{"status": "Returned", "current_stage": "Procurement Enrichment"}
		)
		self.assertEqual(route, "demand-review")
		self.assertEqual(label, "Review")
		label2, route2 = _action_for(
			{"status": "Returned", "current_stage": "Request Preparation"}
		)
		self.assertEqual(route2, "demand-form")
		self.assertEqual(label2, "Resolve")

	def test_queue_my_drafts_filters_to_actor_drafts(self):
		frappe.set_user("Administrator")
		all_payload = list_demands_workspace(page=1, page_size=100)
		draft_queue = list_demands_workspace(queue="my_drafts", page=1, page_size=100)
		self.assertTrue(draft_queue.get("ok"))
		for row in draft_queue.get("rows") or []:
			self.assertEqual(row.get("status"), "Draft")
		# Summary is computed from scoped universe, not the filtered page alone.
		self.assertIn("my_drafts", all_payload["summary"])
		self.assertGreaterEqual(
			all_payload["summary"]["my_drafts"], len(draft_queue.get("rows") or [])
		)
