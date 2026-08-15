# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Approved PLN-UI-04/04A/04B one-step formation contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import add_demand_to_plan
from kentender_procurement.procurement_planning.services.list_eligible_demands import list_eligible_demands
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import PE_MOH, _ensure_ou


def _token(plan: str) -> str:
	version = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
	return frappe.db.get_value("Procurement Plan Version", version, "concurrency_token")


def _form(*, plan: str, demands: list[str], key: str, mode: str | None = None, reason: str | None = None):
	return add_demand_to_plan(
		plan=plan,
		demands=demands,
		expected_version_token=_token(plan),
		formation_mode=mode,
		formation_reason=reason,
		idempotency_key=key,
		user=ensure_planner_user(),
	)


class TestAddDemandToPlanGate04(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_single_demand_creates_one_item_and_holds_every_need_item(self) -> None:
		plan = create_plan_as_planner()["plan"]
		demand = make_approved_demand(title="Single source", need_item_count=2)
		result = _form(plan=plan, demands=[demand["demand"]], key="single")
		self.assertEqual(result["formation_mode"], "separate")
		self.assertEqual(len(result["plan_items"]), 1)
		allocations = frappe.get_all(
			"Plan Demand Allocation",
			filters={"plan_item": result["plan_item"]},
			fields=["demand_item", "source_org_unit", "active_hold_key", "status"],
		)
		self.assertEqual(len(allocations), 2)
		self.assertTrue(all(row.active_hold_key == row.demand_item for row in allocations))
		self.assertTrue(all(row.status == "Draft" for row in allocations))
		self.assertNotIn(
			demand["demand"],
			{row["demand"] for row in list_eligible_demands(plan=plan, user=ensure_planner_user())["demands"]},
		)

	def test_single_demand_rejects_formation_choice(self) -> None:
		plan = create_plan_as_planner()["plan"]
		demand = make_approved_demand(title="No choice")
		with self.assertRaises(frappe.ValidationError):
			_form(plan=plan, demands=[demand["demand"]], key="single-mode", mode="combined")

	def test_multiple_separate_creates_one_item_per_demand(self) -> None:
		plan = create_plan_as_planner()["plan"]
		a = make_approved_demand(title="Separate A", need_item_count=2)
		b = make_approved_demand(title="Separate B", need_item_count=2)
		result = _form(
			plan=plan, demands=[a["demand"], b["demand"]], key="separate", mode="separate"
		)
		self.assertEqual(len(result["plan_items"]), 2)
		self.assertIsNone(result["editor_route"])
		self.assertEqual(
			frappe.db.count("Plan Demand Allocation", {"plan_item": ["in", result["plan_items"]]}),
			4,
		)

	def test_combined_same_ou_retains_owner_and_requires_reason(self) -> None:
		plan = create_plan_as_planner()["plan"]
		a = make_approved_demand(title="Combined A")
		b = make_approved_demand(title="Combined B")
		with self.assertRaises(frappe.ValidationError):
			_form(plan=plan, demands=[a["demand"], b["demand"]], key="no-reason", mode="combined")
		result = _form(
			plan=plan,
			demands=[a["demand"], b["demand"]],
			key="combined",
			mode="combined",
			reason="Common supply and delivery basis",
		)
		self.assertEqual(len(result["plan_items"]), 1)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", result["plan_item"], "owner_org_unit"),
			"MOH-DIR-DHP",
		)

	def test_combined_mixed_ou_is_pe_owned_with_source_lineage(self) -> None:
		other_ou = "MOH-DIR-HRMD"
		_ensure_ou(other_ou, "Human Resources Management and Development", PE_MOH)
		plan = create_plan_as_planner()["plan"]
		a = make_approved_demand(title="Digital source")
		b = make_approved_demand(title="HR source", ou=other_ou)
		result = _form(
			plan=plan,
			demands=[a["demand"], b["demand"]],
			key="mixed",
			mode="combined",
			reason="Common market and coordinated delivery basis",
		)
		self.assertIsNone(
			frappe.db.get_value("Procurement Plan Item", result["plan_item"], "owner_org_unit")
		)
		self.assertEqual(
			set(frappe.get_all(
				"Plan Demand Allocation", filters={"plan_item": result["plan_item"]}, pluck="source_org_unit"
			)),
			{"MOH-DIR-DHP", other_ou},
		)

	def test_idempotent_replay_precedes_stale_token_rejection(self) -> None:
		plan = create_plan_as_planner()["plan"]
		demand = make_approved_demand(title="Replay")
		result = _form(plan=plan, demands=[demand["demand"]], key="replay")
		replayed = add_demand_to_plan(
			plan=plan,
			demands=[demand["demand"]],
			expected_version_token="stale",
			idempotency_key="replay",
			user=ensure_planner_user(),
		)
		self.assertTrue(replayed["replayed"])
		self.assertEqual(replayed["plan_item"], result["plan_item"])

	def test_duplicate_selection_and_missing_token_are_rejected(self) -> None:
		plan = create_plan_as_planner()["plan"]
		demand = make_approved_demand(title="Strict formation input")
		with self.assertRaises(frappe.ValidationError):
			add_demand_to_plan(
				plan=plan, demands=[demand["demand"], demand["demand"]],
				expected_version_token=_token(plan), formation_mode="separate",
				idempotency_key="duplicate-input", user=ensure_planner_user(),
			)
		with self.assertRaises(frappe.ValidationError):
			add_demand_to_plan(
				plan=plan, demands=[demand["demand"]], expected_version_token=None,
				idempotency_key="missing-token", user=ensure_planner_user(),
			)
