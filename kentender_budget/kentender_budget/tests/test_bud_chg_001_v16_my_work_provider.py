# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.6 §10 "Approval tasks" — surfaced through the shared My
Work queue via `kt_my_work_providers`, plus the workspace/detail
`pending_version` action that gives the Budget Approver an in-app route to
a Submitted version (found missing in the 2026-09-06 end-to-end pass: an
Approver had no way to reach a successor's approval task except a
hand-typed URL)."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, nowdate

from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_my_work_provider import my_work_rows
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import FUNDING_SOURCE, _BudgetLifecycleTestBase


class _SubmittedDraftMixin:
	def _create_submitted_draft(self) -> tuple[str, str]:
		"""Officer registers + submits one baseline on a fresh Fiscal Year,
		left undecided. Returns (budget, version) docnames. Assumes the
		calling test already set the acting Officer via `_as`."""
		actor = frappe.session.user
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"MYWORK-{self.suffix}",
				"approval_date": add_days(nowdate(), -3),
				"authorised_total": 1_000_000,
				"approval_document": "/files/test-approval.pdf",
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		budget, version = result["budget"]["id"], result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", budget)
		lines = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version,
				"lines": [{"title": "My Work test line", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 1_000_000}],
			}
		)
		self.assertTrue(lines["ok"], lines.get("errors"))
		for line in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", line)
		self._as(actor)
		submitted = readiness.submit_budget_version({"budget_version": version})
		self.assertTrue(submitted["ok"], submitted.get("blockers"))
		return budget, version


class TestBudgetMyWorkProvider(_SubmittedDraftMixin, _BudgetLifecycleTestBase):
	def test_provider_is_registered_through_the_core_hook(self):
		self.assertIn(
			"kentender_budget.services.budget_my_work_provider.my_work_rows",
			frappe.get_hooks("kt_my_work_providers") or [],
		)

	def test_submitted_version_reaches_the_approver_and_nobody_else(self):
		self._as(self.officer)
		budget, version = self._create_submitted_draft()

		rows = my_work_rows(user=self.approver)["assigned"]
		mine = [r for r in rows if r["task_id"] == version]
		self.assertEqual(len(mine), 1)
		self.assertEqual(mine[0]["route"], ["budget-funding", "review", version])
		self.assertEqual(mine[0]["module"], "Budget & Funding")
		self.assertEqual(mine[0]["stage"], "Initial baseline approval")

		# The submitting Officer never sees their own submission as a decision.
		self.assertEqual([r for r in my_work_rows(user=self.officer)["assigned"] if r["task_id"] == version], [])
		# A user with no Budget assignment sees nothing.
		self.assertEqual(my_work_rows(user="Guest"), {"assigned": [], "claimable": [], "waiting": []})

		# Once decided, the row disappears.
		self._as(self.approver)
		self.assertTrue(readiness.approve_budget_version({"budget_version": version})["ok"])
		self.assertEqual([r for r in my_work_rows(user=self.approver)["assigned"] if r["task_id"] == version], [])

	def test_dual_role_submitter_does_not_see_own_submission(self):
		self._as(self.dual)
		budget, version = self._create_submitted_draft()
		self.assertEqual([r for r in my_work_rows(user=self.dual)["assigned"] if r["task_id"] == version], [])
		self.assertEqual(len([r for r in my_work_rows(user=self.approver)["assigned"] if r["task_id"] == version]), 1)

	def test_workspace_and_detail_expose_the_server_decided_pending_action(self):
		self._as(self.officer)
		budget, version = self._create_active_baseline()
		self._as(self.officer)
		fy = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		successor = contracts.create_budget_successor_version(budget, {"revision_type": "Correction"})["version"]["id"]

		# Draft successor: the Officer continues it, the Approver gets nothing.
		self.assertEqual(contracts.get_budget_workspace(fy)["pending_version"]["action"], "open_draft")
		self.assertTrue(contracts.get_budget_detail(budget)["pending_version"]["is_successor"])
		self._as(self.approver)
		self.assertNotIn("pending_version", contracts.get_budget_workspace(fy))
		self.assertIsNone(contracts.get_budget_detail(budget)["pending_version"])

		# Submitted successor: the Approver opens the task, the Officer views it.
		self._as(self.officer)
		self.assertTrue(readiness.submit_budget_version({"budget_version": successor})["ok"])
		self.assertEqual(contracts.get_budget_workspace(fy)["pending_version"]["action"], "view_submission")
		self._as(self.approver)
		pending = contracts.get_budget_workspace(fy)["pending_version"]
		self.assertEqual(pending["action"], "open_task")
		self.assertEqual(pending["id"], successor)
		self.assertEqual(contracts.get_budget_detail(budget)["pending_version"]["action"], "open_task")

	def test_returned_draft_carries_the_reason_for_the_officer(self):
		self._as(self.officer)
		budget, version = self._create_submitted_draft()
		self._as(self.approver)
		reason = "Line titles must name the department before activation."
		self.assertTrue(readiness.return_budget_version({"budget_version": version, "return_reason": reason})["ok"])
		self._as(self.officer)
		returned = contracts.get_budget_version_draft(version)["returned"]
		self.assertEqual(returned["reason"], reason)
		self.assertTrue(returned["by"])
		self.assertTrue(returned["at"].endswith("EAT"))
		self.assertTrue(readiness.submit_budget_version({"budget_version": version})["ok"])
		self.assertIsNone(contracts.get_budget_version_draft(version)["returned"])


class TestDirectRouteVerdictsAsData(_SubmittedDraftMixin, _BudgetLifecycleTestBase):
	"""KT-STD-001 v1.2 §3A.2 / BUD-AC-039..041 and BUD-CHG-001 §12.5 — every
	direct-route read resolves Forbidden/Not-found as data so the page renders
	its inline panel and the framework never raises a modal on page load."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.auditor = cls._make_user("auditor", ("Auditor",))
		cls.nobody = cls._make_user("nobody", ())

	def test_unassigned_user_gets_forbidden_as_data_on_every_direct_route(self):
		self._as(self.officer)
		budget, version = self._create_active_baseline()
		line = frappe.get_all("Procurement Budget Line", filters={"budget": budget}, pluck="name")[0]
		self._as(self.nobody)
		for payload in (
			contracts.get_budget_detail(budget),
			contracts.get_budget_line_position(line),
			contracts.get_budget_version_draft(version),
			readiness.get_budget_approval_task(version),
			readiness.get_budget_approval_task_lines(version),
			readiness.get_budget_approval_task_changes(version),
		):
			self.assertEqual(payload.get("outcome"), "FORBIDDEN")
			self.assertNotIn("positions", payload)
			self.assertNotIn("rows", payload)

	def test_read_only_auditor_reads_records_but_is_denied_the_approval_task(self):
		self._as(self.officer)
		budget, version = self._create_submitted_draft()
		self._as(self.auditor)
		self.assertIsNone(contracts.get_budget_version_draft(version).get("outcome"))
		task = readiness.get_budget_approval_task(version)
		self.assertEqual(task.get("outcome"), "FORBIDDEN")
		self.assertIn("Budget Approver", task["forbidden"]["text"])
		self.assertEqual(readiness.get_budget_approval_task_lines(version).get("outcome"), "FORBIDDEN")
		self.assertEqual(readiness.get_budget_approval_task_changes(version).get("outcome"), "FORBIDDEN")
		# The Approver, and a technical reader, still open it.
		self._as(self.approver)
		self.assertIsNone(readiness.get_budget_approval_task(version).get("outcome"))
		frappe.set_user("Administrator")
		self.assertIsNone(readiness.get_budget_approval_task(version).get("outcome"))
		self.assertFalse(readiness.get_budget_approval_task(version)["capabilities"]["can_approve"])

	def test_unknown_identifiers_resolve_to_not_found_as_data(self):
		self._as(self.officer)
		self.assertEqual(contracts.get_budget_detail("NO-SUCH-BUDGET")["outcome"], "NOT_FOUND")
		self.assertEqual(contracts.get_budget_line_position("NO-SUCH-LINE")["outcome"], "NOT_FOUND")
		self.assertEqual(contracts.get_budget_version_draft("NO-SUCH-VERSION")["outcome"], "NOT_FOUND")
		self._as(self.approver)
		self.assertEqual(readiness.get_budget_approval_task("NO-SUCH-VERSION")["outcome"], "NOT_FOUND")
