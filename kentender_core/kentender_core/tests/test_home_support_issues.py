# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — a Technical Operator's support issues on Home (owner decision 5 Oct 2026, FU-HOME-46: they were on
My Work and must not be lost when My Work is retired).

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_home_support_issues
"""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, support_issues
from kentender_core.services import home_workspace as hw
from kentender_core.services.home_support_issues import entries
from kentender_core.tests import test_support_issues as base

NOW = datetime(2027, 6, 18, 10, 0)


class TestHomeSupportIssues(IntegrationTestCase):
	"""Reuses the support-issue fixture (a Technical Operator and an unrelated user) without re-running its tests."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		base.TestSupportIssues.setUpClass()  # the users and the Technical Operator grant
		cls.addClassCleanup(base.TestSupportIssues._remove)

	def setUp(self):
		self.addCleanup(base.TestSupportIssues._remove_issues)
		home_support.reset()

	open = base.TestSupportIssues.open

	def rows(self, user, region="my_work"):
		home_support.reset()
		return entries(user=user, region=region)

	def test_the_holder_gets_one_my_work_row_per_open_issue_in_the_owners_words(self):
		issue = self.open()
		(row,) = [r for r in self.rows(base.HOLDER) if r["root"] == issue["issue_id"]]
		self.assertEqual((row["region"], row["owner"], row["action_id"]), ("my_work", "support", "resolve"))
		self.assertEqual((row["title"], row["reference"]), ("Resolve evaluation issue for TND-TEST-001", issue["issue_id"]))
		self.assertEqual(row["action"], "Repair the failed operation")
		self.assertEqual((row["entered_verb"], row["entered_at"]), ("Opened", issue["opened_at"]))
		self.assertEqual(row["destination"], {"route": ["Form", "Support Issue", issue["issue_id"]], "route_options": {}})
		self.assertNotIn("could not be loaded", repr(row))  # the safe detail is for the issue's own page, never the Home row

	def test_a_resolved_issue_is_no_longer_work(self):
		issue = self.open()
		support_issues.resolve_on_success(module="Bid Evaluation", operation_correlation="EVL-INTAKE-TEST-1")
		self.assertEqual([r for r in self.rows(base.HOLDER) if r["root"] == issue["issue_id"]], [])

	def test_only_my_work_for_the_holder_and_nothing_for_anyone_else(self):
		self.open()
		for region in ("coming_up", "waiting", "oversight", "completed"):
			self.assertIsNone(self.rows(base.HOLDER, region), region)
		self.assertIsNone(self.rows(base.OTHER))  # not a Technical Operator: this provider does not apply

	def test_through_home_the_holder_sees_it_as_technical_work_with_a_form_link_and_no_counts(self):
		issue = self.open()
		result = hw.get_workspace(base.HOLDER, providers=[], technical_providers=[entries], at=NOW)
		self.assertTrue(result["viewer"]["technical"])
		self.assertFalse(result["summary_visible"])
		mine = [r for r in result["regions"]["my_work"]["entries"] if r["reference"] == issue["issue_id"]]
		self.assertEqual(len(mine), 1)
		self.assertEqual((mine[0]["module"], mine[0]["destination"]["route"]), ("Support issues", ["Form", "Support Issue", issue["issue_id"]]))

	def test_the_hook_registers_the_provider_for_technical_readers_only(self):
		self.assertIn("kentender_core.services.home_support_issues.entries", frappe.get_hooks("kt_home_technical_providers"))
		self.assertNotIn("kentender_core.services.home_support_issues.entries", frappe.get_hooks("kt_home_providers"))

	def test_reading_writes_nothing(self):
		issue = self.open()
		before = support_issues.get(issue["issue_id"])
		self.rows(base.HOLDER)
		self.assertEqual(support_issues.get(issue["issue_id"]), before)
