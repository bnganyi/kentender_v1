# Copyright (c) 2026, KenTender and contributors
"""KT-STD-001 v1.5 §3A.6 / AUTH-ADR-001 §8 — Strategy's technical-read gate.

Administrator and System Manager read every plan, task and history
read-only with every command capability False: never Forbidden, never
masked, never an empty list standing in for a denial. An Auditor assignment
gets the same universal read everywhere in this module EXCEPT the approval
task overview: STR-AC-021 draws that specific line at an Active Strategy
Approver assignment, and a technical reader is the only exception to it.
A business actor without a governing assignment still gets the Forbidden
verdict as data, unchanged.

Run:
  bench --site kentender.midas.com run-tests --app kentender_strategy \\
    --module kentender_strategy.tests.test_str_technical_read
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services import responsibility_administration as administration
from kentender_strategy.services import strategy_ui_contracts as ui
from kentender_strategy.services.strategy_authorization import (
	ROLE_STRATEGY_APPROVER,
	ROLE_STRATEGY_AUTHOR,
	ensure_strategy_governance_roles,
)
from kentender_strategy.services.strategy_transitions import transition_plan_version
from kentender_strategy.tests.fixtures import ensure_fiscal_year

FY = "2040-2041"


class TechnicalReadTestBase(FrappeTestCase):
	def setUp(self):
		ensure_strategy_governance_roles()
		ensure_fiscal_year(2040)
		self.suffix = uuid4().hex[:8]
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def _track(self, doc):
		self._cleanup.append((doc.doctype, doc.name))
		return doc

	def _user(self, label: str, roles: tuple[str, ...] = ()) -> str:
		email = f"kt.test.str.techread.{label}.{self.suffix}@test.local"
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": label,
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
		doc.add_roles("Desk User", *roles)
		self._track(doc)
		return email

	def _grant(self, user: str, business_role: str) -> str:
		outcome = administration.grant(
			user=user,
			business_role=business_role,
			organisation_unit="",
			fixture_namespace="STR_TECHREAD_TESTS",
			actor="Administrator",
		)
		self._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))
		return outcome["assignment"]

	def _plan(self, **kwargs):
		data = {
			"doctype": "Strategic Plan",
			"title": f"Tech Read Plan {self.suffix}",
			"plan_role": "Primary",
			"period_start": "2040-07-01",
			"period_end": "2045-06-30",
		}
		data.update(kwargs)
		return self._track(frappe.get_doc(data).insert(ignore_permissions=True))

	def _version(self, plan, **kwargs):
		data = {
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": "2040-07-01",
			"effective_to": "2045-06-30",
		}
		data.update(kwargs)
		return self._track(frappe.get_doc(data).insert(ignore_permissions=True))

	def _hierarchy(self, version):
		pillar = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": version.name,
					"node_type": "Pillar",
					"title": "Pillar",
					"display_order": 1,
				}
			).insert(ignore_permissions=True)
		)
		programme = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": version.name,
					"node_type": "Programme",
					"title": "Programme",
					"display_order": 2,
					"parent_node_id": pillar.name,
				}
			).insert(ignore_permissions=True)
		)
		objective = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": version.name,
					"node_type": "Strategic Objective",
					"title": "Objective",
					"display_order": 3,
					"parent_node_id": programme.name,
				}
			).insert(ignore_permissions=True)
		)
		indicator = self._track(
			frappe.get_doc(
				{
					"doctype": "Performance Indicator",
					"plan_version_id": version.name,
					"measures_node_id": objective.name,
					"indicator_name": "Indicator",
					"definition": "Definition",
					"unit": "Percentage",
				}
			).insert(ignore_permissions=True)
		)
		self._track(
			frappe.get_doc(
				{
					"doctype": "Performance Target",
					"indicator_id": indicator.name,
					"fiscal_year": FY,
					"comparison": "At least",
					"target_value": 80,
				}
			).insert(ignore_permissions=True)
		)

	def _submitted_version(self):
		"""A plan with one Submitted-for-approval version, authored and
		approver-assigned by two real business users (neither technical)."""
		author = self._user("author")
		approver_holder = self._user("approver")
		self._grant(author, ROLE_STRATEGY_AUTHOR)
		self._grant(approver_holder, ROLE_STRATEGY_APPROVER)
		plan = self._plan()
		version = self._version(plan)
		self._hierarchy(version)
		frappe.set_user(author)
		try:
			transition_plan_version(version.name, "Submit for approval")
		finally:
			frappe.set_user("Administrator")
		return plan, version


class TestUniversalReaders(TechnicalReadTestBase):
	def _assert_full_read_only_access(self, plan, version):
		"""Every read contract except the approval task overview succeeds
		with data, and every command capability inside it is False — no
		Forbidden, no masking, no [] standing in for a denial."""
		portfolio = ui.get_strategy_portfolio()
		self.assertFalse(portfolio["forbidden"])
		self.assertIn(plan.name, [p["id"] for p in portfolio["plans"]])

		workspace = ui.get_plan_workspace(plan.plan_id)
		self.assertFalse(workspace["forbidden"])
		self.assertFalse(workspace["not_found"])
		self.assertFalse(workspace["is_editable_draft"])
		self.assertFalse(workspace["capabilities"]["create_successor"])
		self.assertFalse(workspace["capabilities"]["edit_identity"])
		self.assertFalse(workspace["capabilities"]["submit"])

		plan_history = ui.get_plan_history(plan.plan_id)
		self.assertGreaterEqual(len(plan_history), 1)

		version_history = ui.get_version_history(version.plan_version_id)
		self.assertGreaterEqual(len(version_history), 1)

		tree = ui.get_strategy_tree(version.plan_version_id)
		self.assertNotIn("not_found", tree)
		self.assertEqual(tree["counts"]["pillars"], 1)

		diff = ui.diff_strategy_versions(None, version.plan_version_id)
		self.assertNotIn("not_found", diff)
		self.assertIn("changes", diff)

	def _assert_review_overview_open_read_only(self, version):
		"""KT-STD-001 §3A.6 — a technical reader's exception to STR-AC-021:
		the approval task overview opens read-only instead of Forbidden."""
		overview = ui.get_version_review_overview(version.plan_version_id)
		self.assertFalse(overview["forbidden"])
		self.assertNotIn("reason", overview)
		self.assertIsNone(overview["role"])
		self.assertEqual(overview["allowed_actions"], [])

	def test_administrator_reads_everything_read_only(self):
		plan, version = self._submitted_version()
		frappe.set_user("Administrator")
		self._assert_full_read_only_access(plan, version)
		self._assert_review_overview_open_read_only(version)

	def test_system_manager_only_user_reads_everything_read_only(self):
		plan, version = self._submitted_version()
		techie = self._user("techie", roles=("System Manager",))
		frappe.set_user(techie)
		try:
			self._assert_full_read_only_access(plan, version)
			self._assert_review_overview_open_read_only(version)
		finally:
			frappe.set_user("Administrator")

	def test_auditor_reads_everything_except_the_approval_task(self):
		"""STR-AC-021: read access alone — Auditor included — is not the
		approval task's gate. Only an Active Strategy Approver assignment,
		or KT-STD-001 §3A.6's technical exception, opens it."""
		plan, version = self._submitted_version()
		auditor = self._user("auditor")
		self._grant(auditor, "Auditor")
		frappe.set_user(auditor)
		try:
			self._assert_full_read_only_access(plan, version)
			overview = ui.get_version_review_overview(version.plan_version_id)
			self.assertTrue(overview["forbidden"])
			self.assertEqual(overview["reason"], "approver_required")
		finally:
			frappe.set_user("Administrator")


class TestBusinessActorWithoutAssignmentStaysForbidden(TechnicalReadTestBase):
	def test_denied_business_user_gets_forbidden_or_masked_not_found(self):
		plan, version = self._submitted_version()
		outsider = self._user("outsider")
		frappe.set_user(outsider)
		try:
			self.assertTrue(ui.get_strategy_portfolio()["forbidden"])

			workspace = ui.get_plan_workspace(plan.plan_id)
			self.assertTrue(workspace["forbidden"])

			# This outsider has no Strategy read access at all, so
			# `_can_read()` denies them before the approval task's own
			# `approver_required` reason is ever computed — that specific
			# reason, for a reader who can read but lacks the Approver
			# assignment, is asserted by `TestUniversalReaders`'s Auditor
			# case above (STR-AC-021).
			overview = ui.get_version_review_overview(version.plan_version_id)
			self.assertTrue(overview["forbidden"])

			self.assertEqual(ui.get_plan_history(plan.plan_id), [])
			self.assertEqual(ui.get_version_history(version.plan_version_id), [])
			self.assertTrue(ui.get_strategy_tree(version.plan_version_id).get("not_found"))
			self.assertTrue(
				ui.diff_strategy_versions(None, version.plan_version_id).get("not_found")
			)
		finally:
			frappe.set_user("Administrator")
