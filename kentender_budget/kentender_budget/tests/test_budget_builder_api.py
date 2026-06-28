# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""W5-02 — Regression tests for get_budget_builder_data payload completeness.

Asserts that the builder endpoint returns all fields required by the Budget
Workbench (Zone 1 header, Zone 2 line cards, totals bar).

Run:
  bench --site kentender.midas.com run-tests \
    --app kentender_budget \
    --module kentender_budget.tests.test_budget_builder_api
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

from kentender_budget.api.builder import get_budget_builder_data


class TestBudgetBuilderApiPayload(IntegrationTestCase):
	"""get_budget_builder_data must expose every field the workbench needs."""

	# ── Fixtures ──────────────────────────────────────────────────────────────

	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"WB_{h}", f"Workbench Test Entity {h}")

		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan WB {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

		self.program = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan.name,
				"program_title": f"Program WB {h}",
				"order_index": 0,
			}
		).insert(ignore_permissions=True)

		self.budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"budget_name": f"Budget WB {h}",
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"strategic_plan": self.plan.name,
				"currency": "KES",
				"total_budget_amount": 500_000,
				"version_no": 1,
				"is_current_version": 1,
				"order_index": 0,
				"effective_date": "2026-01-01",
				"closing_date": "2026-12-31",
			}
		).insert(ignore_permissions=True)

		self.line = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"budget_line_code": f"BL-WB-{h}",
				"budget_line_name": f"Works Line {h}",
				"fiscal_year": 2026,
				"currency": "KES",
				"is_active": 1,
				"amount_allocated": 300_000,
				"amount_reserved": 100_000,
				"amount_committed": 50_000,
				"amount_consumed": 20_000,
				"amount_available": 130_000,
				"economic_classification": "Works",
				"department": "Infrastructure Dept",
				"line_status": "Active",
				"funding_source": None,
				"strategic_plan": self.plan.name,
				"program": self.program.name,
			}
		).insert(ignore_permissions=True)

	# ── Header fields ──────────────────────────────────────────────────────────

	def test_budget_header_has_procuring_entity(self):
		"""Zone 1 needs procuring_entity to render the entity subtitle."""
		result = get_budget_builder_data(self.budget.name)
		self.assertEqual(result["budget"]["procuring_entity"], self.entity)

	def test_budget_header_has_fiscal_year(self):
		"""Zone 1 needs fiscal_year for the header metadata row."""
		result = get_budget_builder_data(self.budget.name)
		self.assertEqual(str(result["budget"]["fiscal_year"]), "2026")

	def test_budget_header_has_closing_date(self):
		"""Zone 1 may show closing date as a metadata chip."""
		result = get_budget_builder_data(self.budget.name)
		self.assertIsNotNone(result["budget"]["closing_date"])
		self.assertIn("2026-12-31", str(result["budget"]["closing_date"]))

	def test_budget_header_has_effective_date(self):
		"""Zone 1 may show effective date as a metadata chip."""
		result = get_budget_builder_data(self.budget.name)
		self.assertIsNotNone(result["budget"]["effective_date"])
		self.assertIn("2026-01-01", str(result["budget"]["effective_date"]))

	# ── Budget line fields ────────────────────────────────────────────────────

	def _get_line(self, result):
		matches = [l for l in result["budget_lines"] if l["name"] == self.line.name]
		self.assertEqual(len(matches), 1, "Expected exactly one matching budget line")
		return matches[0]

	def test_line_has_department(self):
		"""Zone 2 line cards display the department label."""
		line = self._get_line(get_budget_builder_data(self.budget.name))
		self.assertEqual(line["department"], "Infrastructure Dept")

	def test_line_has_economic_classification(self):
		"""Zone 2 line cards display the economic classification (Works/Goods/etc)."""
		line = self._get_line(get_budget_builder_data(self.budget.name))
		self.assertEqual(line["economic_classification"], "Works")

	def test_line_has_line_status(self):
		"""Zone 2 line cards show the line_status pill."""
		line = self._get_line(get_budget_builder_data(self.budget.name))
		self.assertEqual(line["line_status"], "Active")

	# ── Totals ────────────────────────────────────────────────────────────────

	def test_totals_has_committed_sum(self):
		"""Zone 1 summary cards need committed_sum to render the Committed card."""
		result = get_budget_builder_data(self.budget.name)
		totals = result["totals"]
		self.assertIn("committed_sum", totals)
		self.assertGreaterEqual(flt(totals["committed_sum"]), 0)

	def test_totals_committed_sum_matches_active_lines(self):
		"""committed_sum must equal sum of amount_committed for active lines only."""
		result = get_budget_builder_data(self.budget.name)
		self.assertEqual(flt(result["totals"]["committed_sum"]), 50_000.0)
