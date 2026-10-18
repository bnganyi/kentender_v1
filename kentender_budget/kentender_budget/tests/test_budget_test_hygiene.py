# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget test hygiene — what a Budget test class leaves on the site, and what the reference allocator does about leftovers.

Found 18 October 2026: the shared Budget test base removed a class's Budgets, Versions and Lines but never their Budget Line Versions. While the
clean-up was still rolled back nothing was deleted and nothing collided; once it committed (b174e984) every Budget class left its Line Versions
behind, the never-reuse counter re-synchronised from the surviving Lines only, and the next class's first line took a number whose version
reference (`MOH-BL-0065-V1`) still existed — twelve seam modules failed with a duplicate-key error on a clean canonical world.

Three rules, each pinned here: a tracked Budget's whole graph goes when its class is torn down; no Budget Line Version on the site is ever
left without its Budget Version; and a line number is never reissued while any record, Line or Line Version, still carries it (BUD-FR-020).
"""

from __future__ import annotations

import re

import frappe

from kentender_core.services.command_write_guard import purge_doc
from kentender_budget.services.budget_reference import allocate_budget_line_reference
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import _BudgetLifecycleTestBase

_NUMBER = re.compile(r"-BL-(\d{4})")


def _number(reference: str) -> int:
	return int(_NUMBER.search(reference).group(1))


def _orphan_line_versions() -> list[str]:
	return [
		row[0]
		for row in frappe.db.sql(
			"""select v.generated_reference from `tabProcurement Budget Line Version` v
			left join `tabProcurement Budget Version` bv on bv.name = v.budget_version where bv.name is null"""
		)
	]


class TestAClassCleanUpRemovesItsLineVersions(_BudgetLifecycleTestBase):
	"""The base's clean-up removes the Line Versions of every Budget it tracked, not only the Budget, its Versions and its Lines."""

	def test_the_tracked_budgets_line_versions_are_gone_after_the_clean_up(self):
		_, version = self._create_active_baseline()
		references = frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="generated_reference")
		self.assertEqual(len(references), 2, references)

		type(self)._purge_tracked()

		self.assertFalse(frappe.db.exists("Procurement Budget Version", version))
		self.assertEqual(
			frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="generated_reference"),
			[],
			"the class's Line Versions survived its clean-up",
		)
		for reference in references:
			self.assertNotIn(reference, _orphan_line_versions())


class TestNoLineVersionIsStranded(_BudgetLifecycleTestBase):
	"""Site-wide: every Budget Line Version still has its Budget Version. A failure names the stranded references; the seed's budget clear
	(`_delete_budget_graph`) or `purge_doc` removes them."""

	def test_every_line_version_on_the_site_has_its_budget_version(self):
		self.assertEqual(_orphan_line_versions(), [], "Budget Line Versions without a Budget Version are left on this site")


class TestNoAuditEventIsStranded(_BudgetLifecycleTestBase):
	"""Site-wide: every Budget Audit Event still has its Budget. The old clean-up removed a class's Budgets without their ledger rows."""

	def test_every_audit_event_on_the_site_has_its_budget(self):
		stranded = [
			row[0]
			for row in frappe.db.sql(
				"""select e.name from `tabBudget Audit Event` e left join `tabProcurement Budget` b on b.name = e.budget where b.name is null"""
			)
		]
		self.assertEqual(stranded, [], "Budget Audit Events without a Budget are left on this site")


class TestLineNumbersAreNeverReissued(_BudgetLifecycleTestBase):
	"""BUD-FR-020: a surviving Line Version keeps its number out of use even when its Line is gone (the shape the old clean-up left)."""

	def test_a_surviving_line_version_keeps_its_number_out_of_use(self):
		_, version = self._create_active_baseline()
		versions = frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, fields=["name", "generated_reference", "budget_line"])
		highest = max(_number(row.generated_reference) for row in versions)
		for row in versions:
			purge_doc("Procurement Budget Line", row.budget_line)  # the Line goes, the Line Version stays, as the old clean-up left things
		self.assertTrue(all(frappe.db.exists("Procurement Budget Line Version", row.name) for row in versions))

		reference = allocate_budget_line_reference()

		self.assertGreater(_number(reference), highest, f"{reference} reuses a number a surviving Line Version still carries")
