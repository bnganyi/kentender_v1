# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — service contract tests (TDD)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_home.services.home_actions import (
	ACTION_LIMIT,
	ALLOWED_ACTION_LABELS,
	_sort_key,
	_urgency,
)
from kentender_procurement.procurement_home.services.home_pipeline import PIPELINE_STAGES
from kentender_procurement.procurement_home.services.home_portfolio import (
	_finance_sums_for_context,
)
from kentender_procurement.procurement_home.services.home_service import build_procurement_home
from frappe.utils import getdate


class TestHomeServiceContract(IntegrationTestCase):
	def test_action_urgency_and_sort_order(self):
		today = getdate()
		from datetime import timedelta

		self.assertEqual(_urgency(today - timedelta(days=1), today), "Overdue")
		self.assertEqual(_urgency(today + timedelta(days=2), today), "Due soon")
		self.assertEqual(_urgency(today + timedelta(days=10), today), "Other")
		items = [
			{"urgency": "Other", "_due_date": today + timedelta(days=10)},
			{"urgency": "Overdue", "_due_date": today - timedelta(days=1)},
			{"urgency": "Due soon", "_due_date": today + timedelta(days=1)},
			{"urgency": "Other", "_due_date": None, "_modified": "2020-01-01"},
		]
		items.sort(key=lambda i: _sort_key(i, today))
		self.assertEqual(items[0]["urgency"], "Overdue")
		self.assertEqual(items[1]["urgency"], "Due soon")

	def test_pipeline_has_exactly_six_stages_no_eval_award(self):
		self.assertEqual(len(PIPELINE_STAGES), 6)
		labels = " ".join(s[1].lower() for s in PIPELINE_STAGES)
		self.assertNotIn("evaluation", labels)
		self.assertNotIn("award", labels)
		self.assertNotIn("contract", labels)

	def test_build_home_shape_for_administrator(self):
		frappe.set_user("Administrator")
		payload = build_procurement_home()
		self.assertTrue(payload.get("ok"))
		self.assertIn("context", payload)
		self.assertIn("procuring_entity", payload["context"])
		self.assertIn("fiscal_year", payload["context"])
		self.assertIn("actions", payload)
		self.assertIn("pipeline", payload)
		self.assertIn("deadlines", payload)
		self.assertIn("portfolio", payload)
		self.assertIn("visibility", payload)
		actions = payload["actions"]
		self.assertLessEqual(len(actions.get("items") or []), ACTION_LIMIT)
		for item in actions.get("items") or []:
			self.assertIn(item.get("action_label"), ALLOWED_ACTION_LABELS)
			self.assertNotIn("Approve", item.get("action_label") or "")
			self.assertNotIn("Reject", item.get("action_label") or "")
		stages = (payload.get("pipeline") or {}).get("stages") or []
		self.assertEqual(len(stages), 6)
		# Bid confidentiality — no bid counts in JSON
		blob = frappe.as_json(payload).lower()
		self.assertNotIn("bid_count", blob)
		self.assertNotIn("bidder_name", blob)

	def test_unauthorized_entity_rejected(self):
		frappe.set_user("Administrator")
		# Use a nonsense PE that is not in scope for a scoped user when possible.
		# Administrator is break-glass; create a synthetic check via resolve.
		from kentender_procurement.procurement_home.services import home_context

		entities = home_context.list_available_entities("Administrator")
		if len(entities) < 1:
			self.skipTest("No Procuring Entity on site")
		# Guest cannot call
		frappe.set_user("Guest")
		with self.assertRaises(Exception):
			build_procurement_home()

	def test_whitelist_api(self):
		frappe.set_user("Administrator")
		from kentender_procurement.procurement_home.api.home import get_procurement_home

		payload = get_procurement_home()
		self.assertTrue(payload.get("ok"))
		self.assertEqual(len((payload.get("pipeline") or {}).get("stages") or []), 6)

	def test_deadline_items_include_stitch_action_icons(self):
		frappe.set_user("Administrator")
		payload = build_procurement_home()
		for item in (payload.get("deadlines") or {}).get("items") or []:
			self.assertIn(item.get("action_icon"), {"open_in_new", "visibility", "rate_review"})
			self.assertTrue(item.get("action_label"))

	def test_finance_sums_ignore_draft_allocations(self):
		"""Draft budgets must not inflate allocated/available while approved stays 0."""
		budgets = [
			{
				"name": "BUD-DRAFT",
				"status": "Draft",
				"fiscal_year": 2026,
				"procuring_entity": "PE-MOH",
				"total_budget_amount": 8_000_000,
				"allocated_amount": 100_000,
			},
			{
				"name": "BUD-OTHER-PE",
				"status": "Approved",
				"fiscal_year": 2026,
				"procuring_entity": "PE-DOE",
				"total_budget_amount": 5_000_000,
				"allocated_amount": 2_000_000,
			},
		]
		approved, allocated, available = _finance_sums_for_context(budgets, "PE-MOH", 2026)
		self.assertEqual(approved, 0.0)
		self.assertEqual(allocated, 0.0)
		self.assertEqual(available, 0.0)

	def test_finance_sums_approved_pe_fy_and_aliases(self):
		budgets = [
			{
				"name": "BUD-MOH",
				"status": "Approved",
				"fiscal_year": 2026,
				"procuring_entity": "MOH",  # alias of PE-MOH
				"total_budget_amount": 8_000_000,
				"allocated_amount": 100_000,
			},
			{
				"name": "BUD-OLD-FY",
				"status": "Approved",
				"fiscal_year": 2025,
				"procuring_entity": "PE-MOH",
				"total_budget_amount": 1_000_000,
				"allocated_amount": 500_000,
			},
		]
		approved, allocated, available = _finance_sums_for_context(budgets, "PE-MOH", 2026)
		self.assertEqual(approved, 8_000_000.0)
		self.assertEqual(allocated, 100_000.0)
		self.assertEqual(available, 7_900_000.0)

	def test_portfolio_figures_are_internally_consistent(self):
		"""Live Home: allocated must not exceed approved; available = approved − allocated."""
		frappe.set_user("Administrator")
		payload = build_procurement_home()
		figures = {
			f["key"]: f["value"]
			for f in ((payload.get("portfolio") or {}).get("figures") or [])
			if "key" in f
		}
		if "approved_budget" not in figures:
			self.skipTest("Portfolio finance figures not visible for this user")
		approved = float(figures["approved_budget"] or 0)
		allocated = float(figures["allocated_plans"] or 0)
		available = float(figures["available_balance"] or 0)
		self.assertLessEqual(allocated, approved + 0.001)
		self.assertAlmostEqual(available, max(0.0, approved - allocated), places=2)
