# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-014 / PLN-AC-019 — immutable Planning Handoff Snapshot."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import TAKEUP_ACTIVE
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.create_planning_handoff_snapshot import (
	create_planning_handoff_snapshot,
)
from kentender_procurement.procurement_planning.services.get_plan_implementation import (
	get_plan_implementation,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	approve_plan_via_gate05,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)


class TestCreatePlanningHandoffSnapshot(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_rejects_draft_item(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3300, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Handoff draft deny", financial_year=fy)
		d = make_approved_demand(title="Handoff draft demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		result = create_planning_handoff_snapshot(
			plan_item=added["plan_item"], user=planner
		)
		self.assertFalse(result["ok"])
		self.assertIn("form", result["errors"])

	def test_creates_immutable_snapshot_and_blocks_propose_removal(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3300, bucket=1)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Handoff active", financial_year=fy)
		d = make_approved_demand(title="Handoff active demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		first = create_planning_handoff_snapshot(
			plan_item=added["plan_item"],
			tender_reference="TND-MOH-TEST-008",
			user=planner,
		)
		self.assertTrue(first["ok"], first)
		self.assertEqual(first["tender_reference"], "TND-MOH-TEST-008")
		self.assertTrue(first["handoff_code"])
		snap = json.loads(
			frappe.db.get_value(
				"Planning Handoff Snapshot", first["handoff"], "snapshot_json"
			)
			or "{}"
		)
		self.assertEqual(snap.get("plan_item"), added["plan_item"])
		self.assertTrue(snap.get("demand_allocations"))

		second = create_planning_handoff_snapshot(
			plan_item=added["plan_item"],
			tender_reference="TND-SHOULD-NOT-CHANGE",
			user=planner,
		)
		self.assertTrue(second["ok"], second)
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(second["handoff"], first["handoff"])
		self.assertEqual(second["tender_reference"], "TND-MOH-TEST-008")

		dto = get_plan_implementation(plan=plan["plan"], user=planner)
		row = next(r for r in dto["items"] if r["plan_item"] == added["plan_item"])
		self.assertEqual(row["takeup_label"], TAKEUP_ACTIVE)
		self.assertEqual(row["tender_reference"], "TND-MOH-TEST-008")
		self.assertFalse(row["can_propose_removal"])
		self.assertEqual(dto["takeup_label"], "1 of 1")
