# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Smoke: kentender_budget shell after MVP-1 teardown + core rebuild."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_bench_path


def _teardown_inventory_path() -> Path:
	return (
		Path(get_bench_path())
		/ "apps"
		/ "kentender_v1"
		/ "docs"
		/ "mvp-1"
		/ "02_budget"
		/ "05_Budget_Teardown_Dependency_Inventory.md"
	)


def _section_6(source: str) -> str:
	marker = "## 6."
	idx = source.find(marker)
	if idx < 0:
		return ""
	return source[idx:]


class TestMvp1BudgetTeardownShell(FrappeTestCase):
	def test_legacy_only_budget_doctypes_absent(self):
		"""Pre-MVP-1-only DocTypes stay dropped; core Budget/Line are rebuilt."""
		for name in (
			"Budget Allocation",
			"Budget Reservation",
			"Funding Source",
			"Budget Navigation",
		):
			self.assertFalse(
				frappe.db.exists("DocType", name),
				f"Legacy-only DocType {name} should remain dropped",
			)
		for name in ("Budget", "Budget Line"):
			self.assertTrue(
				frappe.db.exists("DocType", name),
				f"MVP-1 DocType {name} should exist after core rebuild",
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

	def test_teardown_inventory_section_6_reflects_rebuild(self):
		"""BUD-SUP-007 — §6 must not claim MVP-1 Budget is unimplemented."""
		path = _teardown_inventory_path()
		self.assertTrue(path.is_file(), msg=f"missing teardown inventory at {path}")
		source = path.read_text(encoding="utf-8")
		self.assertIn("04_Budget_Cross_Module_Lifecycle_Tracker.md", source)
		self.assertIn("MOH_MVP_V1", source)
		section = _section_6(source)
		self.assertTrue(section, msg="## 6. section not found")
		self.assertIn("core rebuild", section.lower())
		self.assertNotIn(
			"not yet implemented",
			section.lower(),
			msg="§6 must not claim MVP-1 Budget is not yet implemented",
		)
