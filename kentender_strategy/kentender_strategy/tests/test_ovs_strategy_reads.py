# Copyright (c) 2026, KenTender and contributors
"""The Accounting Officer, the Head of Procurement Function and a Head of User Department read approved
Strategy (OVS-CHG-001 v0.6 §4.1; plan Phase 10; tracker OVS6-1001; acceptance OVS-AC-008, OVS-AC-009).

"Active AO, HOPF and HoD responsibilities can read approved current and historical Strategy versions and
their recorded approval reasons. No general Draft or pending review access is added." Approved means a
version that is Current or Previous; a version awaiting approval, a draft and the approval task stay with
the people who already hold them. Strategy has no department attribution, so a Head of User Department
reads the same approved versions as the two offices (the approved-version read is not departmental)."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_strategy.services import strategy_ui_contracts as ui
from kentender_strategy.services.strategy_authorization import ROLE_STRATEGY_APPROVER, ROLE_STRATEGY_AUTHOR, ensure_strategy_governance_roles
from kentender_strategy.services.strategy_transitions import transition_plan_version
from kentender_strategy.tests.fixtures import ensure_fiscal_year, pin_review_date
from kentender_strategy.tests.test_str_technical_read import TechnicalReadTestBase

# The suite's usual 2040 window collides with Frappe's own `_Test Fiscal Year 2040` on a site that loaded test records;
# this suite uses a window nothing else occupies.
FY, START, END = "2060-2061", "2060-07-01", "2065-06-30"


class TestApprovedStrategyReads(TechnicalReadTestBase):
	def setUp(self):
		ensure_strategy_governance_roles()
		ensure_fiscal_year(2060)
		self.suffix = uuid4().hex[:8]
		self._cleanup = []
		patcher = patch("kentender_strategy.tests.test_str_technical_read.FY", FY)
		patcher.start()
		self.addCleanup(patcher.stop)
		pin_review_date(self)
		self.author = self._user("author")
		self.approver = self._user("approver")
		self._grant(self.author, ROLE_STRATEGY_AUTHOR)
		self._grant(self.approver, ROLE_STRATEGY_APPROVER)
		unit = frappe.db.get_value("Organisation Unit", {"status": "Active"}, "name")
		self.readers = {}
		for label, role, ou in (("ao", "Accounting Officer", ""), ("hopf", "Head of Procurement Function", ""), ("hod", "Head of User Department", unit)):
			user = self._user(label)
			outcome = administration.grant(
				user=user, business_role=role, organisation_unit=ou, fixture_namespace="STR_TECHREAD_TESTS", actor="Administrator")
			self._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))
			self.readers[label] = user
		self.outsider = self._user("outsider")
		self.pending_plan, self.pending = self._make("Pending", approve=False)
		self.approved_plan, self.approved = self._make("Approved", approve=True)

	def _make(self, label: str, *, approve: bool):
		plan = self._plan(title=f"OVS {label} {self.suffix}", period_start=START, period_end=END)
		version = self._version(plan, effective_from=START, effective_to=END)
		self._hierarchy(version)
		frappe.set_user(self.author)
		try:
			transition_plan_version(version.name, "Submit for approval")
		finally:
			frappe.set_user("Administrator")
		if approve:
			frappe.set_user(self.approver)
			try:
				transition_plan_version(version.name, "Approve")
			finally:
				frappe.set_user("Administrator")
		version.reload()
		return plan, version

	def as_user(self, user, fn, *args, **kwargs):
		frappe.set_user(user)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_the_three_readers_see_the_approved_plan_and_not_the_one_awaiting_approval(self):
		self.assertEqual(self.approved.status, "Active")
		for label, user in self.readers.items():
			portfolio = self.as_user(user, ui.get_strategy_portfolio)
			self.assertFalse(portfolio["forbidden"], label)
			ids = [p["id"] for p in portfolio["plans"]]
			self.assertIn(self.approved_plan.name, ids, label)
			self.assertNotIn(self.pending_plan.name, ids, label)
			self.assertEqual(portfolio["my_work"], [], label)
			self.assertFalse(portfolio["can_create_plan"], label)
			self.assertEqual({o["value"] for o in portfolio["status_options"]}, {"Active", "Superseded"}, label)

	def test_they_open_the_approved_plan_its_structure_and_the_approval_history(self):
		for label, user in self.readers.items():
			workspace = self.as_user(user, ui.get_plan_workspace, self.approved_plan.plan_id)
			self.assertFalse(workspace.get("forbidden"), label)
			self.assertFalse(workspace.get("not_found"), label)
			self.assertFalse(workspace["capabilities"]["update_plan"], label)
			self.assertFalse(workspace["capabilities"]["submit"], label)
			tree = self.as_user(user, ui.get_strategy_tree, self.approved.name)
			self.assertFalse(tree.get("not_found"), label)
			events = [e["event"] for e in self.as_user(user, ui.get_plan_history, self.approved_plan.plan_id)]
			self.assertIn("Approve", events, label)

	def test_a_plan_version_not_yet_approved_is_not_found_to_them(self):
		for label, user in self.readers.items():
			self.assertTrue(self.as_user(user, ui.get_plan_workspace, self.pending_plan.plan_id).get("not_found"), label)
			self.assertTrue(self.as_user(user, ui.get_strategy_tree, self.pending.name).get("not_found"), label)
			self.assertEqual(self.as_user(user, ui.get_version_history, self.pending.name), [], label)
			self.assertEqual(self.as_user(user, ui.get_plan_history, self.pending_plan.plan_id), [], label)

	def test_the_approval_task_and_the_comparison_stay_with_the_people_who_hold_them(self):
		for label, user in self.readers.items():
			self.assertTrue(self.as_user(user, ui.get_version_review_overview, self.approved.name).get("forbidden"), label)
			self.assertTrue(self.as_user(user, ui.diff_strategy_versions, None, self.approved.name).get("not_found"), label)

	def test_a_person_with_no_responsibility_is_still_forbidden(self):
		self.assertTrue(self.as_user(self.outsider, ui.get_strategy_portfolio)["forbidden"])
		self.assertTrue(self.as_user(self.outsider, ui.get_plan_workspace, self.approved_plan.plan_id).get("forbidden"))

	def test_the_existing_readers_still_see_the_pending_plan(self):
		ids = [p["id"] for p in self.as_user(self.approver, ui.get_strategy_portfolio)["plans"]]
		self.assertIn(self.pending_plan.name, ids)
