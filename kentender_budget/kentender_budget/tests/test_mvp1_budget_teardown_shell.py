# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Smoke: kentender_budget app shell after MVP-1 preparatory teardown."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMvp1BudgetTeardownShell(FrappeTestCase):
	def test_legacy_budget_doctypes_absent(self):
		for name in (
			"Budget",
			"Budget Line",
			"Budget Allocation",
			"Budget Reservation",
			"Funding Source",
			"Budget Navigation",
		):
			self.assertFalse(
				frappe.db.exists("DocType", name),
				f"Legacy DocType {name} should be dropped",
			)

	def test_legacy_budget_pages_absent(self):
		for name in ("budget-hub", "budget-workbench"):
			self.assertFalse(
				frappe.db.exists("Page", name),
				f"Legacy Page {name} should be dropped",
			)

	def test_budget_management_placeholder_workspace(self):
		self.assertTrue(frappe.db.exists("Workspace", "Budget Management"))
		row = frappe.db.get_value(
			"Workspace",
			"Budget Management",
			["public", "is_hidden", "label"],
			as_dict=True,
		)
		self.assertEqual(int(row.public or 0), 1)
		self.assertEqual(int(row.is_hidden or 0), 0)
		self.assertEqual(row.label, "Budget & Funding")

	def test_seed_upsert_skips(self):
		from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget

		result = upsert_works_master_budget()
		self.assertTrue(result.get("ok"))
		self.assertTrue(result.get("skipped"))
		self.assertEqual(result.get("reason"), "mvp1-budget-teardown")
