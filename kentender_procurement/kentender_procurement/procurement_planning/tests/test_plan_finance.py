# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.11/§5.2/§7.3/§8.2 — one plan-level funding
confirmation (PLN-AC-021/022/023/024/068/070/075/080/081/082/083/087).

Exercises the REAL `check_plan_affordability` Budget contract (never mocked)
against a real Active Budget Version + Budget Line Version graph, and proves
that no Planning command creates, holds or releases a reservation."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_read,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class PlanFinanceCase(IntegrationTestCase):
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
		patched = patch.object(needs_intake, "current_accepted_sources", return_value=[])
		patched.start()
		self.addCleanup(patched.stop)
		eligible = patch.object(budget_gateway, "eligible_line_ids", return_value={fx.BUDGET_LINE, fx.BUDGET_LINE_2})
		eligible.start()
		self.addCleanup(eligible.stop)

	def accepted_item(self, *, indicative_amount: float = 1000000, budget_line: str = "") -> tuple[dict, str]:
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(indicative_amount=indicative_amount, budget_line=budget_line or fx.BUDGET_LINE),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		return accepted, formed["created_items"][0]

	def ready_item(self, **kwargs) -> tuple[dict, str]:
		accepted, item_id = self.accepted_item(**kwargs)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(), expected_record_version=item["record_version"], idempotency_key=key(),
		)
		return accepted, item_id

	def request(self, plan_reference: str, *, user: str = fx.PLANNER):
		frappe.set_user(user)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		return plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)


class TestRequestPlanFundingConfirmation(PlanFinanceCase):
	def test_request_creates_one_task_per_version_and_flips_the_funding_state(self):
		accepted, item_id = self.ready_item()
		result = self.request(accepted["annual_plan"])
		self.assertEqual(result["action"], "requested")
		task = frappe.get_doc("Plan Finance Task", result["task"])
		self.assertEqual(task.status, "Open")
		self.assertEqual(task.plan_version, accepted["annual_plan_version"])
		self.assertTrue(task.task_reference.startswith("FNT-"))
		self.assertEqual(int(task.plan_value), 1000000)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", task.plan_version, "funding_state"), "Awaiting confirmation")
		# PLN-AC-080: one task per Version, none per item
		self.assertEqual(frappe.db.count("Plan Finance Task", {"plan_version": task.plan_version}), 1)
		self.assertFalse(frappe.get_meta("Plan Finance Task").has_field("plan_item"))

	def test_request_is_refused_by_the_exact_readiness_blocker(self):
		accepted, item_id = self.accepted_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		# no Objective, no reservation category: the first blocker names it
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.request(accepted["annual_plan"])
		self.assertIn(caught.exception.code, ("PLN_OBJECTIVE_INELIGIBLE", "PLN_RESERVATION_REQUIRED"))
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(reservation_category=""),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.request(accepted["annual_plan"])
		self.assertEqual(caught.exception.code, "PLN_RESERVATION_REQUIRED")

	def test_request_replays_idempotently_and_reuses_the_open_task(self):
		accepted, item_id = self.ready_item()
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		idem = key()
		first = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=idem,
		)
		replay = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=idem,
		)
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["task"], first["task"])
		self.assertEqual(frappe.db.count("Plan Finance Task", {"plan_version": plan["version_reference"]}), 1)

	def test_a_plan_over_the_approved_amount_cannot_request_confirmation(self):
		"""PLN-AC-082 — within approved amount is the blocking verdict."""
		accepted, item_id = self.ready_item(indicative_amount=150_000_000)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.request(accepted["annual_plan"])
		self.assertEqual(caught.exception.code, "PLN_PLAN_NOT_AFFORDABLE")
		self.assertTrue(caught.exception.detail["failing_lines"])
		self.assertEqual(int(caught.exception.detail["failing_lines"][0]["excess"]), 50_000_000)


class TestConfirmPlanFunding(PlanFinanceCase):
	def confirm(self, task_name: str, *, user: str = fx.FINANCE_OFFICER, idem: str | None = None):
		task = frappe.get_doc("Plan Finance Task", task_name)
		frappe.set_user(user)
		return plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=idem or key())

	def test_confirm_records_the_statement_and_creates_no_reservation(self):
		"""PLN-AC-022/023/081 — the whole plan cycle leaves Budget untouched."""
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"])
		reservations_before = frappe.db.count("Funding Reservation", {"budget_line": fx.BUDGET_LINE})
		frappe.set_user(fx.FINANCE_OFFICER)
		read = plan_read.get_finance_task(task=requested["task"])
		self.assertTrue(read["within_approved"])
		self.assertTrue(read["can_confirm"])
		self.assertIn("EAT", read["as_at_display"])
		line = next(r for r in read["lines"] if r["budget_line"] == fx.BUDGET_LINE)
		self.assertEqual(line["planned_display"], "KES 1,000,000")
		self.assertEqual(line["within_approved_display"], "Yes")
		self.assertIn("reserves no funds", read["quiet_line"])

		result = self.confirm(requested["task"])
		self.assertEqual(result["action"], "confirmed")
		decision = frappe.get_doc("Plan Finance Decision", {"decision_reference": result["decision"]})
		self.assertEqual(decision.decision, "Confirm plan funding")
		self.assertIn("within_approved", decision.affordability_statement)
		self.assertIn("assignment_id", decision.authority_snapshot)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "funding_state"), "Confirmed")
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": fx.BUDGET_LINE}), reservations_before)
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(next(c for c in plan["readiness"] if c["check"] == "Plan funding confirmed")["result"], "Confirmed")
		frappe.set_user(fx.HOPF)
		self.assertTrue(plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["can_sign_and_submit"])  # v1.18 §6.2

	def test_the_hybrid_planner_who_requested_cannot_also_confirm(self):
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"], user=fx.HYBRID_FINANCE)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(requested["task"], user=fx.HYBRID_FINANCE)
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")

	def test_a_non_finance_officer_is_refused(self):
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"])
		with self.assertRaises(frappe.DoesNotExistError):
			self.confirm(requested["task"], user=fx.PLANNER)

	def test_confirm_replays_idempotently(self):
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"])
		idem = key()
		first = self.confirm(requested["task"], idem=idem)
		replay = self.confirm(requested["task"], idem=idem)
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["decision"], first["decision"])

	def test_return_requires_a_reason_and_sends_the_version_back_to_the_planner(self):
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"])
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.FINANCE_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_finance.return_from_finance(task=task.name, reason="", task_token=task.task_token, idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")
		result = plan_finance.return_from_finance(
			task=task.name, reason="Reconcile the planned total against the approved line.", task_token=task.task_token, idempotency_key=key(),
		)
		self.assertEqual(result["action"], "returned")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "funding_state"), "Returned")
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertTrue(plan["can_request_funding"])

	def _line_version(self, budget_line: str) -> str:
		return frappe.db.get_value("Procurement Budget Line Version", {"budget_line": budget_line, "budget_version": ("in", frappe.get_all("Procurement Budget Version", filters={"status": "Active"}, pluck="name"))}, "name")

	def _change_approved_amount(self, budget_line: str, amount: float) -> None:
		name = self._line_version(budget_line)
		before = frappe.db.get_value("Procurement Budget Line Version", name, "approved_amount")
		frappe.db.set_value("Procurement Budget Line Version", name, "approved_amount", amount, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Procurement Budget Line Version", name, "approved_amount", before, update_modified=False)

	def test_a_request_captures_an_immutable_basis_and_the_review_reads_it(self):
		"""v1.18 §4.7 / §5.3.1 — the basis Finance decides on."""
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"])
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		self.assertEqual(task.financial_basis, requested["financial_basis"])
		basis = frappe.get_doc("Plan Financial Basis", task.financial_basis)
		self.assertEqual(basis.plan_version, accepted["annual_plan_version"])
		self.assertEqual(basis.currency, "KES")
		self.assertTrue(basis.basis_digest and basis.budget_basis_digest)
		lines = {r["budget_line"]: r for r in json.loads(basis.lines)}
		self.assertEqual(lines[fx.BUDGET_LINE]["planned"], "1000000.00")
		self.assertEqual(lines[fx.BUDGET_LINE]["line_version"], self._line_version(fx.BUDGET_LINE))
		frappe.set_user(fx.FINANCE_OFFICER)
		read = plan_read.get_finance_task(task=task.name)
		self.assertEqual(read["financial_basis"]["basis_digest"], basis.basis_digest)
		self.assertTrue(read["basis_current"])
		self.assertFalse(read["is_reassessment"])
		# a second request on the same basis reuses the one open review
		again = self.request(accepted["annual_plan"])
		self.assertEqual(again["action"], "reused")
		self.assertEqual(again["task"], task.name)

	def test_a_changed_budget_basis_replaces_the_open_review_and_fails_a_stale_decision(self):
		"""§5.3.2 at most one open review; §5.3.3 a stale basis fails the positive decision atomically."""
		accepted, item_id = self.ready_item()
		first = self.request(accepted["annual_plan"])
		self._change_approved_amount(fx.BUDGET_LINE, 90_000_000)
		frappe.set_user(fx.FINANCE_OFFICER)
		self.assertFalse(plan_read.get_finance_task(task=first["task"])["basis_current"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(first["task"])
		self.assertEqual(caught.exception.code, "PLN_FINANCE_STALE")
		self.assertEqual(frappe.db.get_value("Plan Finance Task", first["task"], "status"), "Open")  # a failed decision changes nothing
		replaced = self.request(accepted["annual_plan"])
		self.assertEqual(replaced["action"], "replaced")
		self.assertNotEqual(replaced["task"], first["task"])
		self.assertEqual(frappe.db.get_value("Plan Finance Task", first["task"], "status"), "Cancelled")
		self.assertEqual(frappe.db.count("Plan Finance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"}), 1)
		confirmed = self.confirm(replaced["task"])
		self.assertEqual(confirmed["action"], "confirmed")
		decision = frappe.get_doc("Plan Finance Decision", {"decision_reference": confirmed["decision"]})
		self.assertEqual(json.loads(decision.affordability_statement)["financial_basis"], replaced["financial_basis"])

	def test_an_identical_basis_after_a_source_change_reuses_the_earlier_confirmation(self):
		"""§5.3.2 — the reuse record links the current basis to the earlier decision."""
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"])
		confirmed = self.confirm(requested["task"])
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.dissolve_plan_item(plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key())
		self.assertEqual(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "funding_state"), "Stale")
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		new_item = plan_read.get_plan_item(plan_item_id=formed["created_items"][0])
		plan_workbench.save_plan_item(plan_item=formed["created_items"][0], values=fx.item_values(), expected_record_version=new_item["record_version"], idempotency_key=key())
		reused = self.request(accepted["annual_plan"])
		self.assertEqual(reused["action"], "confirmation_reused")
		self.assertEqual(reused["earlier_decision"], confirmed["decision"])
		self.assertTrue(frappe.db.exists("Plan Finance Basis Reuse", reused["reuse"]))
		self.assertEqual(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "funding_state"), "Confirmed")
		self.assertEqual(frappe.db.count("Plan Finance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"}), 0)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertTrue(plan["funding_evidence"]["current"])
		self.assertEqual(plan["funding_evidence"]["reuse"]["earlier_decision"], confirmed["decision"])
		frappe.set_user(fx.HOPF)
		self.assertTrue(plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["can_sign_and_submit"])  # v1.18 §6.2

	def test_a_line_total_change_makes_the_confirmation_stale(self):
		"""PLN-AC-024/087 — a changed per-line total, not a narrative edit,
		invalidates the confirmation."""
		accepted, item_id = self.ready_item()
		requested = self.request(accepted["annual_plan"])
		self.confirm(requested["task"])
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(title="Renamed package without a money change"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "funding_state"), "Confirmed")
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.dissolve_plan_item(plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key())
		self.assertEqual(frappe.db.get_value("Annual Plan Version", accepted["annual_plan_version"], "funding_state"), "Stale")
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		frappe.set_user(fx.HOPF)
		self.assertFalse(plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["can_sign_and_submit"])
