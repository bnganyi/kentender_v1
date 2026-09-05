# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §12.1 workspace read-model tests (Phase 3).

The read-offer parity rules (NDS-807/NDS-911 class): every open task the
actor may decide appears as a row, nothing is offered that the command layer
would refuse, and a read creates no record."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	needs_intake,
	workspace,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class WorkspaceCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		for target, attr, value in (
			(budget_gateway, "eligible_line_ids", {fx.BUDGET_LINE}),
			(needs_intake, "current_accepted_sources", []),
		):
			patched = patch.object(target, attr, return_value=value)
			patched.start()
			self.addCleanup(patched.stop)

	def load(self, user):
		frappe.set_user(user)
		return workspace.get_planning_workspace(financial_year=fx.FY_OPEN, user=user)

	def submitted(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		return dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)


class TestWorkspace(WorkspaceCase):
	def test_no_responsibility_resolves_to_the_forbidden_panel_without_record_creation(self):
		"""PLN-AC-111/112 — the verdict resolves before anything renders."""
		before = frappe.db.count("Departmental Plan")
		nobody = "plnt.nobody@example.test"
		fx._user(nobody, "PLNT Nobody")
		result = self.load(nobody)
		self.assertEqual(result["outcome"], "FORBIDDEN")
		self.assertEqual(result["forbidden"]["heading"], "You do not have access to Procurement Planning")
		self.assertIn("Procurement Planner, Finance Confirmation Officer, Accounting Officer", result["forbidden"]["text"])
		self.assertIn("KenTender administrator", result["forbidden"]["text"])
		self.assertEqual(frappe.db.count("Departmental Plan"), before)
		# an Author elsewhere sees an OK page with nothing of Alpha's
		other = self.load(fx.OUTSIDER)
		self.assertEqual(other["outcome"], "OK")
		self.assertEqual(other["departmental_plans"], [])

	def test_author_is_offered_their_departments_plan_and_only_theirs(self):
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		result = self.load(fx.AUTHOR)
		self.assertEqual(result["outcome"], "OK")
		departments = [row["department"] for row in result["departmental_plans"]]
		self.assertEqual(departments, [fx.OU_ALPHA_NAME])
		headlines = [row["headline"] for row in result["actionable"]]
		self.assertIn("Continue departmental plan", headlines)
		self.assertIsNone(result["schedule_health"])  # PLN-AC-129: absent, not zero

	def test_every_open_validation_task_is_offered_to_the_planner(self):
		self.submitted()
		result = self.load(fx.PLANNER)
		validate_rows = [row for row in result["actionable"] if row["headline"] == "Validate departmental plan"]
		open_tasks = frappe.db.count("Departmental Plan Validation Task", {"fiscal_year": fx.FY_OPEN, "status": "Open"})
		self.assertEqual(len(validate_rows), open_tasks)
		self.assertGreater(open_tasks, 0)
		self.assertEqual(validate_rows[0]["supporting"], fx.OU_ALPHA_NAME)
		self.assertEqual(validate_rows[0]["route"][1], "dpp-review")

	def test_auditor_sees_rows_but_is_offered_no_work(self):
		self.submitted()
		result = self.load(fx.AUDITOR)
		self.assertEqual(result["outcome"], "OK")
		self.assertEqual(result["actionable"], [])
		self.assertEqual(len(result["departmental_plans"]), 1)

	def test_finance_and_governance_oversight_roles_see_rows_without_a_dead_end_view_link(self):
		"""Finance Confirmation Officer/Accounting Officer/Plan Statutory Approver are
		classified as Site-wide oversight so they see every departmental plan's
		status, but `dpp_read._access` never authorises them to open the DPP
		page itself — offering a route there is the NDS-807 read-offer-vs-
		command class of defect (PLN-CHG-001 v1.2 §6, §12.1 route table)."""
		self.submitted()
		for user in (fx.FINANCE_OFFICER, fx.ACCOUNTING_OFFICER, fx.STATUTORY):
			with self.subTest(user=user):
				result = self.load(user)
				self.assertEqual(result["outcome"], "OK")
				self.assertEqual(len(result["departmental_plans"]), 1)
				self.assertFalse(result["departmental_plans"][0].get("route"))

	def test_planner_and_auditor_keep_the_dpp_view_route(self):
		self.submitted()
		for user in (fx.PLANNER, fx.AUDITOR):
			with self.subTest(user=user):
				result = self.load(user)
				self.assertTrue(result["departmental_plans"][0].get("route"))

	def test_workspace_read_creates_nothing(self):
		counts = {
			d: frappe.db.count(d)
			for d in ("Departmental Plan", "Annual Plan", "Planning Command Journal")
		}
		self.load(fx.PLANNER)
		for doctype, count in counts.items():
			self.assertEqual(frappe.db.count(doctype), count, doctype)

	def test_closed_window_shows_not_included_and_critical_status(self):
		self._sources = patch.object(needs_intake, "current_accepted_sources", return_value=[fx.accepted_source()])
		self._sources.start()
		self.addCleanup(self._sources.stop)
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		fx.close_test_intake()
		self.addCleanup(fx.open_test_intake)
		result = self.load(fx.PLANNER)
		self.assertFalse(result["window_open"])
		self.assertIn("not included in any departmental plan", result["not_included"]["title"])
		self.assertIn("submission window closed before they were added", result["not_included"]["text"])
		self.assertIn(fx.OU_ALPHA_NAME, result["not_included"]["text"])
		row = result["departmental_plans"][0]
		self.assertEqual(row["status"], "Not submitted — window closed")
		self.assertEqual(row["status_kind"], "critical")
