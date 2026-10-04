# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A Need accepted after its department's plan — owner decision 26 Sep 2026.

Accepting a Need puts it in the department's Draft plan by itself. When the
plan is already accepted, or is with Procurement, it is left as it is, so the
Need is in no plan until the department creates an update. Found live:
NDS-MOH-2027-0005 was accepted after Digital Health's plan was, and every
screen treated the plan as finished — the plan's next step said "Done", the
Planning workspace offered nothing, and the Need's own page said nothing.

Proved here against genuine Needs, end to end: the department is told on the
plan, the workspace, My Work and the Need's own page (through the position
Planning projects back to Departmental Needs), and every prompt clears the
moment the update carries the Need.
"""

from __future__ import annotations

import frappe

from kentender_core.services import next_step as ns
from kentender_procurement.departmental_needs.services.usage import planning_intake_detail
from kentender_procurement.procurement_planning.services import (
	dpp_lifecycle,
	dpp_read,
	dpp_validation,
	my_work_provider,
	workspace,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_publication import RealNeedsCase, key


class TestLateAcceptedNeed(RealNeedsCase):
	def _submitted_plan(self, needs: list[str]) -> tuple[str, str, dict[str, str]]:
		"""The department's plan carrying `needs`, funded and submitted."""
		opened, entries = self._dpp_with_needs(needs)
		version = opened["record_version"]
		entry_ids = {}
		for need, entry in entries.items():
			entry_id = frappe.db.get_value("Departmental Plan Entry", entry, "entry_id")
			funded = dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"], entry_id=entry_id, budget_line=fx.BUDGET_LINE, indicative_amount=500000,
				expected_record_version=version, idempotency_key=key(),
			)
			version = funded["record_version"]
			entry_ids[need] = entry_id
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=version, idempotency_key=key(),
		)
		return opened["dpp_reference"], submitted["task"], entry_ids

	def _accept(self, task_reference: str, entry_ids: dict[str, str]) -> None:
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": task_reference})
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(
			task=task.name, classifications={entry_id: "Goods" for entry_id in entry_ids.values()},
			task_token=task.task_token, idempotency_key=key(),
		)

	def _late_after_acceptance(self) -> tuple[str, str, str]:
		"""(plan reference, the Need in it, the Need accepted after it)."""
		first = self._accepted_need("Accepted before the plan")
		reference, task, entry_ids = self._submitted_plan([first])
		self._accept(task, entry_ids)
		late = self._accepted_need("Accepted after the plan")
		return reference, first, late

	@staticmethod
	def _position(need: str, user: str):
		revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
		return planning_intake_detail(need, revision, user=user)

	@staticmethod
	def _plan(reference: str, user: str) -> dict:
		frappe.set_user(user)
		return dpp_read.get_departmental_plan(dpp_reference=reference, user=user)

	def _create_update(self, reference: str) -> dict:
		frappe.set_user(fx.HOD)
		view = dpp_read.get_departmental_plan(dpp_reference=reference)
		return dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=reference, expected_record_version=view["record_version"], idempotency_key=key(),
		)

	# ------------------------------------------------------------------

	def test_the_department_is_told_on_the_plan_the_workspace_my_work_and_the_need(self):
		reference, first, late = self._late_after_acceptance()

		# The Need's own page (through Departmental Needs' projection).
		self.assertIsNone(self._position(first, fx.AUTHOR), "a Need the plan carries has nothing to report")
		mine = self._position(late, fx.AUTHOR)
		self.assertEqual(mine["position"], "Update required")
		self.assertEqual(mine["departmental_plan"], reference)
		self.assertEqual(mine["carried_revision_number"], 0)
		self.assertTrue(mine["can_update"])
		self.assertFalse(self._position(late, fx.PLANNER)["can_update"])

		# The plan: the department's turn, not "Done".
		for user in (fx.AUTHOR, fx.HOD):
			view = self._plan(reference, user)
			step = view["next_step"]
			self.assertEqual(step["kind"], ns.KIND_YOUR_TURN, user)
			self.assertEqual(step["primary_action"], "create_update")
			self.assertEqual(step["headline"], f"Add {late} to this plan")
			self.assertTrue(view["can_create_update"])
			self.assertNotIn("update_notice", view, "the next step replaces the separate notice")
			# Owner instruction 28 Sep 2026 — the tracker agrees with the turn:
			# the update starts at Preparation, not with every stage Done.
			self.assertEqual(step["stage"], "preparation")
			self.assertEqual(view["journey"]["current"], "preparation")
			self.assertIn("preparation", [s["code"] for s in view["journey"]["stages"] if s["marker"] == "current"])
		planner = self._plan(reference, fx.PLANNER)["next_step"]
		self.assertEqual(planner["kind"], ns.KIND_WAITING)
		self.assertEqual(planner["headline"], f"Waiting for the department to add {late} to its plan")
		self.assertTrue(planner["since"], "since is the late Need's acceptance")
		self.assertEqual(self._plan(reference, fx.AUDITOR)["next_step"]["kind"], ns.KIND_NOT_INVOLVED)
		technical = self._plan(reference, "Administrator")["next_step"]
		self.assertEqual(technical["kind"], ns.KIND_WAITING)
		self.assertFalse(technical["primary_action"])

		# The Planning workspace: a task for the department, and the register says so.
		frappe.set_user(fx.HOD)
		board = workspace.get_planning_workspace(financial_year=fx.FY_OPEN, user=fx.HOD)
		task = next((a for a in board["actionable"] if a["action"] == "Create update"), None)
		self.assertIsNotNone(task, board["actionable"])
		self.assertEqual(task["headline"], f"Add {late} to the departmental plan")
		self.assertEqual(task["supporting"], f"Accepted after {fx.OU_ALPHA_NAME}'s departmental plan was accepted.")
		self.assertEqual(task["route"], ["departmental-procurement-plan", reference])
		row = next(r for r in board["departmental_plans"] if r["dpp_reference"] == reference)
		self.assertEqual(row["status"], "Accepted · 1 accepted need not in plan")

		# My Work names the Need.
		item = next(r for r in my_work_provider.my_work_rows(user=fx.HOD)["assigned"] if r["task_type"] == "planning.dpp_update_required")
		self.assertEqual(item["stage"], f"{late} not in plan")
		self.assertEqual(item["route"], ["departmental-procurement-plan", reference])

	def test_creating_the_update_carries_the_need_and_clears_every_prompt(self):
		reference, _first, late = self._late_after_acceptance()
		update = self._create_update(reference)

		self.assertTrue(frappe.db.exists("Departmental Plan Entry", {"dpp_version": update["current_version"], "need": late}))
		self.assertIsNone(self._position(late, fx.AUTHOR))
		step = self._plan(reference, fx.HOD)["next_step"]
		self.assertEqual(step["kind"], ns.KIND_YOUR_TURN)
		self.assertNotEqual(step["primary_action"], "create_update")
		frappe.set_user(fx.HOD)
		board = workspace.get_planning_workspace(financial_year=fx.FY_OPEN, user=fx.HOD)
		self.assertFalse([a for a in board["actionable"] if a["action"] == "Create update"])
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=fx.HOD)["assigned"] if r["task_type"] == "planning.dpp_update_required"])

	def test_withdrawing_the_update_brings_the_prompt_back(self):
		reference, _first, late = self._late_after_acceptance()
		update = self._create_update(reference)
		frappe.set_user(fx.HOD)
		dpp_lifecycle.withdraw_departmental_submission(
			dpp_version=update["current_version"], reason="Not ready to change the plan yet.",
			expected_record_version=update["record_version"], idempotency_key=key(),
		)
		self.assertEqual(self._position(late, fx.AUTHOR)["position"], "Update required")
		self.assertEqual(self._plan(reference, fx.HOD)["next_step"]["headline"], f"Add {late} to this plan")

	def test_a_need_accepted_while_the_plan_is_with_procurement_waits_for_that_submission(self):
		first = self._accepted_need("Submitted with the plan")
		_reference, task, entry_ids = self._submitted_plan([first])
		late = self._accepted_need("Accepted during the review")

		waiting = self._position(late, fx.AUTHOR)
		self.assertEqual(waiting["position"], "After current submission")
		self.assertFalse(waiting["can_update"], "nothing to update until Procurement decides")

		self._accept(task, entry_ids)
		self.assertEqual(self._position(late, fx.AUTHOR)["position"], "Update required")
