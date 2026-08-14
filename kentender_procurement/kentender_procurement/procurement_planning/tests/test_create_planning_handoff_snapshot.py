# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-014 / PLN-AC-019 / PLN-GAP-PERM-001 — immutable Planning Handoff Snapshot."""

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
	ensure_tender_initiator,
	ensure_viewer_user,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)


class TestCreatePlanningHandoffSnapshot(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _approved_item(self, *, title: str, fy_bucket: int) -> dict[str, str]:
		planner = ensure_planner_user()
		initiator = ensure_tender_initiator()
		fy = unique_test_fy(base_year=3300, bucket=fy_bucket)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title=title, financial_year=fy)
		d = make_approved_demand(title=f"{title} demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		return {
			"planner": planner,
			"initiator": initiator,
			"plan": plan["plan"],
			"plan_item": added["plan_item"],
		}

	def test_rejects_draft_item(self) -> None:
		planner = ensure_planner_user()
		initiator = ensure_tender_initiator()
		fy = unique_test_fy(base_year=3300, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Handoff draft deny", financial_year=fy)
		d = make_approved_demand(title="Handoff draft demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		result = create_planning_handoff_snapshot(
			plan_item=added["plan_item"], user=initiator
		)
		self.assertFalse(result["ok"])
		self.assertIn("form", result["errors"])

	def test_creates_immutable_snapshot_and_blocks_propose_removal(self) -> None:
		ctx = self._approved_item(title="Handoff active", fy_bucket=1)
		iv_name = frappe.db.get_value(
			"Procurement Plan Item", ctx["plan_item"], "current_approved_item_version"
		)
		frappe.db.set_value(
			"Procurement Plan Item Version",
			iv_name,
			{
				"strategy_snapshot": "MOH-TGT-AVAIL-2028 — handoff lineage",
				"pvc_snapshot": "MOH-PVC-EFT-01 — handoff lineage",
			},
			update_modified=False,
		)
		first = create_planning_handoff_snapshot(
			plan_item=ctx["plan_item"],
			tender_reference="TND-MOH-TEST-008",
			user=ctx["initiator"],
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
		self.assertEqual(snap.get("plan_item"), ctx["plan_item"])
		self.assertTrue(snap.get("plan_version_code") or snap.get("plan_version"))
		self.assertTrue(snap.get("demand_allocations"))
		self.assertTrue(snap["demand_allocations"][0].get("demand_code"))
		finance = snap.get("finance") or {}
		self.assertTrue(finance.get("reservation_id") or finance.get("reservation_code"))
		self.assertEqual(finance.get("status"), "Confirmed")
		self.assertEqual(snap.get("strategy_snapshot"), "MOH-TGT-AVAIL-2028 — handoff lineage")
		self.assertEqual(snap.get("pvc_snapshot"), "MOH-PVC-EFT-01 — handoff lineage")

		second = create_planning_handoff_snapshot(
			plan_item=ctx["plan_item"],
			tender_reference="TND-SHOULD-NOT-CHANGE",
			user=ctx["initiator"],
		)
		self.assertTrue(second["ok"], second)
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(second["handoff"], first["handoff"])
		self.assertEqual(second["tender_reference"], "TND-MOH-TEST-008")

		dto = get_plan_implementation(plan=ctx["plan"], user=ctx["planner"])
		row = next(r for r in dto["items"] if r["plan_item"] == ctx["plan_item"])
		self.assertEqual(row["takeup_label"], TAKEUP_ACTIVE)
		self.assertEqual(row["tender_reference"], "TND-MOH-TEST-008")
		self.assertFalse(row["can_propose_removal"])
		self.assertEqual(dto["takeup_label"], "1 of 1")

	def test_planner_cannot_create_handoff(self) -> None:
		"""PLN-GAP-PERM-001 — Planner is not Tender Initiator."""
		ctx = self._approved_item(title="Handoff planner deny", fy_bucket=2)
		result = create_planning_handoff_snapshot(
			plan_item=ctx["plan_item"],
			tender_reference="TND-MOH-TEST-PLANNER",
			user=ctx["planner"],
		)
		self.assertFalse(result["ok"], result)
		self.assertIn("form", result.get("errors") or {})
		self.assertFalse(
			frappe.db.exists("Planning Handoff Snapshot", {"plan_item": ctx["plan_item"]})
		)

	def test_viewer_cannot_create_handoff(self) -> None:
		"""PLN-GAP-PERM-001 — Viewer cannot take up a Tender."""
		ctx = self._approved_item(title="Handoff viewer deny", fy_bucket=3)
		viewer = ensure_viewer_user()
		result = create_planning_handoff_snapshot(
			plan_item=ctx["plan_item"],
			tender_reference="TND-MOH-TEST-VIEWER",
			user=viewer,
		)
		self.assertFalse(result["ok"], result)
		self.assertIn("form", result.get("errors") or {})
		self.assertFalse(
			frappe.db.exists("Planning Handoff Snapshot", {"plan_item": ctx["plan_item"]})
		)
