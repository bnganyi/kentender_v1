# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§7.3/§8 Finance confirmation tests (Phase 7, Slice E).

Exercises the REAL `check_funding`/`reserve_funding`/`release_reservation`
Budget contracts (never mocked, unlike `eligible_line_ids` elsewhere) against
a real Active Budget Version + Budget Line Version graph."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_read,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx

def ready_values() -> dict:
	# fx.STRATEGY_OBJECTIVE is populated by ensure_world() in setUpClass, so
	# this must be read lazily at call time, never captured as a module-level
	# constant (which would freeze the pre-ensure_world "" default).
	return {
		"title": "Direct requirement", "description": "Assess and remediate the direct requirement.",
		"strategic_objective": fx.STRATEGY_OBJECTIVE, "aggregation_reason": "",
		"invitation_date": "2098-08-01", "bid_opening_date": "2098-08-15",
		"evaluation_completion_date": "2098-09-01", "award_approval_date": "2098-09-10",
		"award_notification_date": "2098-09-15", "contract_signing_date": "2098-10-01",
		"delivery_completion_date": "2098-10-15",
	}


def key() -> str:
	return uuid4().hex


class PlanFinanceCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		patched = patch.object(needs_intake, "current_accepted_sources", return_value=[])
		patched.start()
		self.addCleanup(patched.stop)

	def ready_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		"""One accepted entry, formed and fully completed (objective + full
		chronological schedule) — ready for RequestFinanceConfirmation."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(indicative_amount=indicative_amount),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications={added["entry_id"]: "Goods"},
			task_token=task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		dpp_entry = plan["unallocated_sources"][0]["dpp_entry"]
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=ready_values(),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		return accepted, item_id

	def request_confirmation(self, item_id: str):
		item = plan_read.get_plan_item(plan_item_id=item_id)
		frappe.set_user(fx.PLANNER)
		return plan_finance.request_finance_confirmation(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)


class TestRequestFinanceConfirmation(PlanFinanceCase):
	def test_request_creates_one_open_task_and_flips_finance_state(self):
		_, item_id = self.ready_item()
		result = self.request_confirmation(item_id)
		self.assertEqual(result["action"], "requested")
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(item["header"]["finance_state_badge"], "Awaiting Finance")
		task = frappe.get_doc("Plan Finance Task", result["task"])
		self.assertEqual(task.status, "Open")
		self.assertEqual(task.required_amount, 1000000)

	def test_request_is_refused_without_a_strategic_objective(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications={added["entry_id"]: "Goods"},
			task_token=task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"],
			dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		# no objective, no schedule — Save draft tolerates it, Request Finance doesn't
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.request_confirmation(item_id)
		self.assertEqual(caught.exception.code, "PLN_OBJECTIVE_INELIGIBLE")

	def test_request_replays_idempotently_and_reuses_the_open_task(self):
		_, item_id = self.ready_item()
		idem = key()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		frappe.set_user(fx.PLANNER)
		first = plan_finance.request_finance_confirmation(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=idem,
		)
		second = plan_finance.request_finance_confirmation(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=idem,
		)
		self.assertTrue(second["idempotent"])
		self.assertEqual(second["task"], first["task"])
		self.assertEqual(frappe.db.count("Plan Finance Task", {"fixture_namespace": fx.NS}), 1)


class TestConfirmFunding(PlanFinanceCase):
	def _open_task(self, indicative_amount: float = 1000000):
		accepted, item_id = self.ready_item(indicative_amount=indicative_amount)
		result = self.request_confirmation(item_id)
		task = frappe.get_doc("Plan Finance Task", result["task"])
		return accepted, item_id, task

	def _read_as_budget_officer(self, task_name: str) -> dict:
		frappe.set_user(fx.BUDGET_OFFICER)
		return plan_read.get_finance_task(task=task_name)

	def test_confirm_creates_one_reservation_and_completes_the_task(self):
		accepted, item_id, task = self._open_task()
		read = self._read_as_budget_officer(task.name)
		self.assertEqual(read["header"]["badge"], "Awaiting Finance")
		self.assertTrue(read["all_sufficient"])
		self.assertTrue(read["budget_check_token"])
		self.assertEqual(len(read["lines"]), 1)
		self.assertIn("KES 1,000,000", read["lines"][0]["required_display"])

		frappe.set_user(fx.BUDGET_OFFICER)
		result = plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
			idempotency_key=key(),
		)
		self.assertEqual(result["action"], "confirmed")
		refreshed = frappe.get_doc("Plan Finance Task", task.name)
		self.assertEqual(refreshed.status, "Completed")
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(item["header"]["finance_state_badge"], "Confirmed")
		refs = frappe.get_all(
			"Plan Reservation Reference", filters={"plan_item_id": item_id}, fields=["amount"]
		)
		self.assertEqual(len(refs), 1)
		self.assertEqual(refs[0].amount, 1000000)

	def test_shortfall_is_refused_and_creates_no_reservation(self):
		accepted, item_id, task = self._open_task(indicative_amount=999999999)
		read = self._read_as_budget_officer(task.name)
		self.assertFalse(read["all_sufficient"])
		self.assertFalse(read["lines"][0]["sufficient"])

		frappe.set_user(fx.BUDGET_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_finance.confirm_funding(
				task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_FINANCE_SHORTFALL")
		self.assertEqual(frappe.db.count("Plan Reservation Reference", {"fixture_namespace": fx.NS}), 0)
		self.assertEqual(frappe.get_doc("Plan Finance Task", task.name).status, "Open")

	def test_the_hybrid_planner_who_requested_cannot_also_confirm(self):
		"""§6.1: role combinations are permitted — the conflict is on THIS
		evidence chain, not the role label. HYBRID_FINANCE holds both
		Procurement Planner and Budget Officer from fixture setup (never
		added mid-test: `User.add_roles` doesn't reliably invalidate
		`frappe.get_roles`'s cache within one test process — the same lesson
		test_dpp_validation.py's HYBRID persona already encodes)."""
		accepted, item_id = self.ready_item()
		frappe.set_user(fx.HYBRID_FINANCE)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		result = plan_finance.request_finance_confirmation(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Plan Finance Task", result["task"])
		frappe.set_user(fx.HYBRID_FINANCE)
		read = plan_read.get_finance_task(task=task.name)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_finance.confirm_funding(
				task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")

	def test_non_budget_officer_is_refused(self):
		accepted, item_id, task = self._open_task()
		read = self._read_as_budget_officer(task.name)
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_finance.confirm_funding(
				task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
				idempotency_key=key(),
			)

	def test_confirm_replays_idempotently(self):
		accepted, item_id, task = self._open_task()
		read = self._read_as_budget_officer(task.name)
		frappe.set_user(fx.BUDGET_OFFICER)
		idem = key()
		first = plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
			idempotency_key=idem,
		)
		second = plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
			idempotency_key=idem,
		)
		self.assertTrue(second["idempotent"])
		self.assertEqual(frappe.db.count("Plan Reservation Reference", {"fixture_namespace": fx.NS}), 1)


class TestReturnFromFinance(PlanFinanceCase):
	def test_return_requires_a_reason_and_creates_no_reservation(self):
		accepted, item_id = self.ready_item()
		result = self.request_confirmation(item_id)
		task = frappe.get_doc("Plan Finance Task", result["task"])
		frappe.set_user(fx.BUDGET_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			plan_finance.return_from_finance(
				task=task.name, reason="", task_token=task.task_token, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

		result = plan_finance.return_from_finance(
			task=task.name, reason="The indicative amount exceeds the approved Budget Line ceiling.",
			task_token=task.task_token, idempotency_key=key(),
		)
		self.assertEqual(result["action"], "returned")
		self.assertEqual(frappe.db.count("Plan Reservation Reference", {"fixture_namespace": fx.NS}), 0)
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(item["header"]["finance_state_badge"], "Returned")
		self.assertEqual(frappe.get_doc("Plan Finance Task", task.name).status, "Completed")


class TestDissolveReleasesConfirmedReservations(PlanFinanceCase):
	def test_dissolving_a_confirmed_item_releases_its_reservation(self):
		accepted, item_id = self.ready_item()
		result = self.request_confirmation(item_id)
		task = frappe.get_doc("Plan Finance Task", result["task"])
		frappe.set_user(fx.BUDGET_OFFICER)
		read = plan_read.get_finance_task(task=task.name)
		plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
			idempotency_key=key(),
		)
		ref = frappe.get_all(
			"Plan Reservation Reference", filters={"plan_item_id": item_id},
			fields=["name", "reservation"],
		)[0]
		self.assertEqual(frappe.db.get_value("Funding Reservation", ref.reservation, "status"), "Active")

		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.dissolve_plan_item(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)
		self.assertEqual(frappe.db.get_value("Funding Reservation", ref.reservation, "status"), "Released")
		refreshed_ref = frappe.get_doc("Plan Reservation Reference", ref.name)
		self.assertTrue(refreshed_ref.release_reference)
		self.assertTrue(refreshed_ref.release_correlation)

	def test_a_release_failure_changes_nothing(self):
		"""§7.3: "A release failure rolls back the Planning transition and
		leaves the item blocked." `dissolve_plan_item` releases every
		reservation BEFORE touching allocation or item state — proven here by
		showing that when release itself fails, none of those later writes
		ever happen, not merely that they get rolled back afterwards."""
		accepted, item_id = self.ready_item()
		result = self.request_confirmation(item_id)
		task = frappe.get_doc("Plan Finance Task", result["task"])
		frappe.set_user(fx.BUDGET_OFFICER)
		read = plan_read.get_finance_task(task=task.name)
		plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
			idempotency_key=key(),
		)
		ref = frappe.get_all(
			"Plan Reservation Reference", filters={"plan_item_id": item_id}, fields=["reservation"],
		)[0]

		from kentender_procurement.procurement_planning.services import budget_gateway

		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		with patch.object(
			budget_gateway, "release_planning_reservations",
			side_effect=ProcurementPlanningError(
				"PLN_RESERVATION_RELEASE_FAILED", "Funding could not be released."
			),
		):
			with self.assertRaises(ProcurementPlanningError) as caught:
				plan_workbench.dissolve_plan_item(
					plan_item=item_id, expected_record_version=item["record_version"],
					idempotency_key=key(),
				)
		self.assertEqual(caught.exception.code, "PLN_RESERVATION_RELEASE_FAILED")

		# nothing moved: the reservation, the allocation and the item are
		# exactly where they were before the failed dissolution attempt
		self.assertEqual(frappe.db.get_value("Funding Reservation", ref.reservation, "status"), "Active")
		refreshed = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(refreshed["record_version"], item["record_version"])
		task_doc = frappe.get_doc("Plan Finance Task", task.name)
		self.assertEqual(task_doc.status, "Completed")
		allocation_states = frappe.get_all(
			"Plan Source Allocation", filters={"plan_item_id": item_id}, pluck="allocation_state"
		)
		self.assertEqual(set(allocation_states), {"Draft"})
