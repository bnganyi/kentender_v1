# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-004 / Pack v1.3 — add Demand formation without cosmetic Keep separate."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	approve_plan_via_gate05,
	create_plan_as_planner,
	ensure_approver_user,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestAddDemandToPlanGate04(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _assert_no_keep_separate(self, item_version: str) -> None:
		decision = (
			frappe.db.get_value(
				"Procurement Plan Item Version", item_version, "aggregation_decision"
			)
			or ""
		)
		self.assertNotEqual(decision, "Keep separate")

	def test_creates_proposed_item_and_draft_allocation_without_demand_mutation(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Add demand gate04")
		d = make_approved_demand(title="Add path demand")
		before = frappe.db.get_value(
			"Demand",
			d["demand"],
			["status", "planning_usage", "confirmed_estimate", "modified"],
			as_dict=True,
		)
		result = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		self.assertTrue(result["ok"])
		self.assertTrue(result["plan_item"])
		self.assertEqual(result["allocation_status"], "Draft")
		after = frappe.db.get_value(
			"Demand",
			d["demand"],
			["status", "planning_usage", "confirmed_estimate", "modified"],
			as_dict=True,
		)
		self.assertEqual(before.status, after.status)
		self.assertEqual(before.planning_usage, after.planning_usage)
		self.assertEqual(flt(before.confirmed_estimate), flt(after.confirmed_estimate))
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", result["plan_item"], "baseline_state"),
			"Proposed",
		)
		iv0 = frappe.db.get_value(
			"Procurement Plan Item", result["plan_item"], "draft_item_version"
		)
		# Ordinary one-Demand path: no aggregation metadata.
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv0, "aggregation_decision")
			or "",
			"",
		)
		self._assert_no_keep_separate(iv0)

	def test_rejects_over_allocation(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Over alloc plan")
		d = make_approved_demand(title="Cap demand")
		with self.assertRaises(Exception) as ctx:
			add_demand_to_plan(
				plan=plan["plan"],
				demand=d["demand"],
				allocated_amount=50_000_000,
				user=planner,
			)
		self.assertIn("exceeds approved available", str(ctx.exception).lower())

	def test_opens_draft_revision_when_plan_only_has_approved_version(self) -> None:
		"""PLN-FR-018 / REQ §add flow step 2 — do not require a pre-opened Draft UI."""
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		plan = create_plan_as_planner(title="Approved then add")
		first = make_approved_demand(title="Seed approved item")
		added = add_demand_to_plan(plan=plan["plan"], demand=first["demand"], user=planner)
		self.assertTrue(added["ok"])
		approve_plan_via_gate05(
			plan=plan["plan"], version=plan["version"], user=approver
		)
		self.assertFalse(
			frappe.db.get_value("Procurement Plan", plan["plan"], "open_draft_version")
		)
		builder = get_plan_builder(plan=plan["plan"], user=planner)
		self.assertTrue(
			builder["can_add_demand"],
			"Add Demand must stay available on Open plans with an Approved version",
		)
		second = make_approved_demand(title="Post-approval add")
		result = add_demand_to_plan(plan=plan["plan"], demand=second["demand"], user=planner)
		self.assertTrue(result["ok"])
		self.assertTrue(
			frappe.db.get_value("Procurement Plan", plan["plan"], "open_draft_version")
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", result["plan_item"], "baseline_state"),
			"Proposed",
		)
		iv = frappe.db.get_value(
			"Procurement Plan Item", result["plan_item"], "draft_item_version"
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "aggregation_decision")
			or "",
			"",
		)

	def test_default_one_plan_item_for_multi_need_no_aggregation_metadata(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Multi need default")
		d = make_approved_demand(title="Two need default", need_item_count=2)
		result = add_demand_to_plan(
			plan=plan["plan"],
			demand=d["demand"],
			formation_mode="one_plan_item",
			user=planner,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result.get("formation_mode"), "one_plan_item")
		self.assertEqual(len(result.get("plan_items") or [result["plan_item"]]), 1)
		allocs = frappe.get_all(
			"Plan Demand Allocation",
			filters={"plan_item": result["plan_item"], "status": "Draft"},
		)
		self.assertEqual(len(allocs), 2)
		iv = frappe.db.get_value(
			"Procurement Plan Item", result["plan_item"], "draft_item_version"
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "aggregation_decision")
			or "",
			"",
		)
		self._assert_no_keep_separate(iv)

	def test_separate_per_need_item_requires_reason_and_creates_n_items(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Multi need separate")
		d = make_approved_demand(title="Two need separate", need_item_count=2)
		with self.assertRaises(Exception) as ctx:
			add_demand_to_plan(
				plan=plan["plan"],
				demand=d["demand"],
				formation_mode="separate_per_need_item",
				user=planner,
			)
		self.assertIn("reason", str(ctx.exception).lower())
		result = add_demand_to_plan(
			plan=plan["plan"],
			demand=d["demand"],
			formation_mode="separate_per_need_item",
			separation_reason="Distinct delivery and tender packages for ICT vs works",
			user=planner,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result.get("formation_mode"), "separate_per_need_item")
		self.assertEqual(len(result["plan_items"]), 2)
		self.assertTrue(result.get("builder_route"))
		self.assertFalse(result.get("editor_route"))
		for pi in result["plan_items"]:
			allocs = frappe.get_all(
				"Plan Demand Allocation",
				filters={"plan_item": pi, "status": "Draft"},
				fields=["demand_item"],
			)
			self.assertEqual(len(allocs), 1)
			iv = frappe.db.get_value("Procurement Plan Item", pi, "draft_item_version")
			# Real separate items — division reason only; never cosmetic Keep separate.
			self.assertEqual(
				frappe.db.get_value("Procurement Plan Item Version", iv, "aggregation_decision")
				or "",
				"",
			)
			self._assert_no_keep_separate(iv)
			self.assertTrue(
				frappe.db.get_value("Procurement Plan Item Version", iv, "aggregation_reason")
			)

	def test_ungoverned_second_add_blocked_by_anti_split(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Anti split add")
		d = make_approved_demand(title="Anti split demand", need_item_count=2)
		first = add_demand_to_plan(
			plan=plan["plan"],
			demand=d["demand"],
			formation_mode="one_plan_item",
			user=planner,
		)
		self.assertTrue(first["ok"])
		with self.assertRaises(Exception) as ctx:
			add_demand_to_plan(
				plan=plan["plan"],
				demand=d["demand"],
				formation_mode="separate_per_need_item",
				separation_reason="Should be blocked — already packaged",
				user=planner,
			)
		self.assertIn("split", str(ctx.exception).lower())

	def test_schema_does_not_default_keep_separate(self) -> None:
		meta = frappe.get_meta("Procurement Plan Item Version")
		field = meta.get_field("aggregation_decision")
		self.assertIsNotNone(field)
		self.assertNotIn("Keep separate", field.options or "")
		self.assertIn((field.default or ""), ("", None))
