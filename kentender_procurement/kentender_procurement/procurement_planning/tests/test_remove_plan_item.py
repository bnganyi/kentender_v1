# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-017 / PLN-FR-066…069A — remove Plan Item from Draft (no hard-delete)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	ALLOC_REVERSED,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	ITEM_REMOVED,
)
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	FORMATION_COMBINED,
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder,
)
from kentender_procurement.procurement_planning.services.list_eligible_demands import (
	list_eligible_demands,
)
from kentender_procurement.procurement_planning.services.open_or_create_plan_revision import (
	open_or_create_plan_revision,
)
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	cancel_plan_update,
	release_draft_finance_effects,
	remove_plan_item_from_plan,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	approve_plan_via_gate05,
	complete_plan_item_for_signoff,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestRemovePlanItem(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _eligible_ids(self, plan: str, planner: str) -> set[str]:
		payload = list_eligible_demands(plan=plan, user=planner, remaining_only=True)
		return {r["demand"] for r in payload.get("demands") or []}

	def _token(self, version: str) -> str:
		return frappe.db.get_value("Procurement Plan Version", version, "concurrency_token") or ""

	def _insert_handoff(self, *, plan: str, version: str, plan_item: str) -> str:
		code = f"HO-{frappe.generate_hash(length=8).upper()}"
		doc = frappe.get_doc(
			{
				"doctype": "Planning Handoff Snapshot",
				"plan": plan,
				"plan_version": version,
				"plan_item": plan_item,
				"handoff_code": code,
				"snapshot_json": "{}",
				"snapshot_hash": "test",
				"tender_reference": "TND-TEST-008",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def test_schema_tombstone_fields_exist(self) -> None:
		meta = frappe.get_meta("Procurement Plan Item Version")
		self.assertIsNotNone(meta.get_field("removal_reason"))
		self.assertIsNotNone(meta.get_field("draft_change_label"))
		self.assertIsNotNone(meta.get_field("removed_in_version"))
		self.assertIsNotNone(meta.get_field("proposed_removal"))

	def test_draft_only_excludes_item_restores_eligibility_preserves_lineage(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Remove draft-only")
		d = make_approved_demand(title="Draft remove demand", item_amount=12_000_000)
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		self.assertTrue(added["ok"])
		item = added["plan_item"]
		iv = frappe.db.get_value("Procurement Plan Item", item, "draft_item_version")
		allocs = frappe.get_all(
			"Plan Demand Allocation", filters={"plan_item": item}, pluck="name"
		)
		self.assertTrue(allocs)
		self.assertNotIn(d["demand"], self._eligible_ids(plan["plan"], planner))

		before_total = flt(
			get_plan_builder(plan=plan["plan"], user=planner)["planned_total"]
		)
		result = remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=item,
			reason="Added in error for this draft",
			concurrency_token=self._token(plan["version"]),
			user=planner,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["mode"], "draft_exclude")
		self.assertFalse(result.get("idempotent"))
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", item, "baseline_state"),
			ITEM_REMOVED,
		)
		self.assertTrue(frappe.db.exists("Procurement Plan Item", item))
		self.assertTrue(frappe.db.exists("Procurement Plan Item Version", iv))
		for alloc in allocs:
			self.assertTrue(frappe.db.exists("Plan Demand Allocation", alloc))
			self.assertEqual(
				frappe.db.get_value("Plan Demand Allocation", alloc, "status"),
				ALLOC_REVERSED,
			)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "removal_reason"),
			"Added in error for this draft",
		)
		builder = get_plan_builder(plan=plan["plan"], user=planner)
		ids = {row["plan_item"] for row in builder["items"]}
		self.assertNotIn(item, ids)
		self.assertAlmostEqual(
			flt(builder["planned_total"]),
			max(before_total - 12_000_000, 0.0),
			places=2,
		)
		self.assertIn(d["demand"], self._eligible_ids(plan["plan"], planner))
		# Demand facts unchanged
		self.assertEqual(frappe.db.get_value("Demand", d["demand"], "status"), "Approved")

	def test_missing_reason_returns_field_error(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Remove missing reason")
		d = make_approved_demand(title="Missing reason demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		result = remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=added["plan_item"],
			reason="   ",
			concurrency_token=self._token(plan["version"]),
			user=planner,
		)
		self.assertFalse(result["ok"])
		self.assertIn("reason", result.get("errors") or {})
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", added["plan_item"], "baseline_state"),
			ITEM_PROPOSED,
		)

	def test_active_with_handoff_rejected(self) -> None:
		"""PLN-AC-027 — executed / handoff item: no removal action + service reject."""
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Remove handoff deny")
		d = make_approved_demand(title="Handoff demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		self._insert_handoff(
			plan=plan["plan"], version=plan["version"], plan_item=added["plan_item"]
		)
		open_or_create_plan_revision(plan=plan["plan"], user=planner)
		draft = frappe.db.get_value("Procurement Plan", plan["plan"], "open_draft_version")
		with self.assertRaises(frappe.ValidationError) as ctx:
			remove_plan_item_from_plan(
				plan=plan["plan"],
				plan_item=added["plan_item"],
				reason="Try remove tendered item",
				concurrency_token=self._token(draft),
				user=planner,
			)
		msg = (
			(getattr(ctx.exception, "title", None) or "") + " " + str(ctx.exception)
		).upper()
		self.assertTrue(
			"PLN_ITEM_NOT_REMOVABLE" in msg or "HANDOFF" in msg,
			msg,
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", added["plan_item"], "baseline_state"),
			ITEM_ACTIVE,
		)
		builder = get_plan_builder(plan=plan["plan"], user=planner)
		row = next(r for r in builder["items"] if r["plan_item"] == added["plan_item"])
		self.assertFalse(row.get("can_remove_from_draft"))
		self.assertFalse(row.get("can_propose_removal"))

	def test_combined_item_removed_as_whole(self) -> None:
		"""PLN-AC-027 — combined item is removed only as a whole."""
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Remove combined whole")
		d1 = make_approved_demand(title="Combine A")
		d2 = make_approved_demand(title="Combine B")
		added = add_demand_to_plan(
			plan=plan["plan"],
			demands=[d1["demand"], d2["demand"]],
			formation_mode=FORMATION_COMBINED,
			formation_reason="Same programme, one package",
			user=planner,
		)
		self.assertTrue(added["ok"])
		item = added["plan_item"]
		alloc_count = frappe.db.count("Plan Demand Allocation", {"plan_item": item})
		self.assertGreaterEqual(alloc_count, 2)
		result = remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=item,
			reason="Combined in error",
			concurrency_token=self._token(plan["version"]),
			user=planner,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", item, "baseline_state"),
			ITEM_REMOVED,
		)
		self.assertEqual(
			frappe.db.count(
				"Plan Demand Allocation", {"plan_item": item, "status": ALLOC_REVERSED}
			),
			alloc_count,
		)
		eligible = self._eligible_ids(plan["plan"], planner)
		self.assertIn(d1["demand"], eligible)
		self.assertIn(d2["demand"], eligible)

	def test_idempotent_retry_no_second_audit(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Remove idempotent")
		d = make_approved_demand(title="Idempotent demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		item = added["plan_item"]
		first = remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=item,
			reason="First removal",
			concurrency_token=self._token(plan["version"]),
			user=planner,
		)
		self.assertTrue(first["ok"])
		token = self._token(plan["version"])
		audit = frappe.db.count(
			"Plan Decision",
			{"plan_version": plan["version"], "decision_type": "Removal"},
		)
		second = remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=item,
			reason="First removal",
			concurrency_token=token,
			user=planner,
		)
		self.assertTrue(second["ok"])
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(
			frappe.db.count(
				"Plan Decision",
				{"plan_version": plan["version"], "decision_type": "Removal"},
			),
			audit,
		)

	def test_stale_concurrency_token_rejected(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Remove stale token")
		d = make_approved_demand(title="Stale token demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		with self.assertRaises(frappe.ValidationError) as ctx:
			remove_plan_item_from_plan(
				plan=plan["plan"],
				plan_item=added["plan_item"],
				reason="Stale attempt",
				concurrency_token="not-the-token",
				user=planner,
			)
		msg = (
			(getattr(ctx.exception, "title", None) or "") + " " + str(ctx.exception)
		).upper()
		self.assertTrue(
			"PLN_STALE_VERSION" in msg or "RELOAD" in msg or "ANOTHER USER" in msg,
			msg,
		)

	def test_active_propose_does_not_restore_eligibility_until_approve(self) -> None:
		"""PLN-AC-026 — successor approve applies proposed removal atomically."""
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Propose active removal")
		d = make_approved_demand(title="Active propose demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", added["plan_item"], "baseline_state"),
			ITEM_ACTIVE,
		)
		rev = open_or_create_plan_revision(plan=plan["plan"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		draft = rev["version"]
		result = remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=added["plan_item"],
			reason="No longer required next year",
			concurrency_token=self._token(draft),
			user=planner,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["mode"], "propose_active")
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", added["plan_item"], "baseline_state"),
			ITEM_ACTIVE,
		)
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": added["plan_item"], "plan_version": draft},
			"name",
		)
		self.assertTrue(
			frappe.db.get_value("Procurement Plan Item Version", iv, "proposed_removal")
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "draft_change_label"),
			"Proposed removal",
		)
		self.assertNotIn(d["demand"], self._eligible_ids(plan["plan"], planner))
		alloc_status = frappe.db.get_value(
			"Plan Demand Allocation",
			{"plan_item": added["plan_item"]},
			"status",
		)
		self.assertEqual(alloc_status, ALLOC_EFFECTIVE)

		approved = approve_plan_via_gate05(plan=plan["plan"], version=draft)
		self.assertTrue(approved["ok"])
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", added["plan_item"], "baseline_state"),
			ITEM_REMOVED,
		)
		self.assertEqual(
			frappe.db.get_value(
				"Plan Demand Allocation",
				{"plan_item": added["plan_item"]},
				"status",
			),
			ALLOC_REVERSED,
		)
		self.assertIn(d["demand"], self._eligible_ids(plan["plan"], planner))

	def test_concurrent_handoff_blocks_successor_approval(self) -> None:
		"""PLN-AC-026 — new handoff after propose blocks successor approval."""
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Handoff during propose")
		d = make_approved_demand(title="Handoff race demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		rev = open_or_create_plan_revision(plan=plan["plan"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		draft = rev["version"]
		remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=added["plan_item"],
			reason="Propose then tender appears",
			concurrency_token=self._token(draft),
			user=planner,
		)
		approved_v = frappe.db.get_value(
			"Procurement Plan", plan["plan"], "current_approved_version"
		)
		self._insert_handoff(
			plan=plan["plan"], version=approved_v, plan_item=added["plan_item"]
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			approve_plan_via_gate05(plan=plan["plan"], version=draft)
		blob = (
			(getattr(ctx.exception, "title", None) or "") + " " + str(ctx.exception)
		).upper()
		self.assertTrue(
			"PLN_ITEM_NOT_REMOVABLE" in blob or "HANDOFF" in blob or "TENDER" in blob,
			blob,
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item", added["plan_item"], "baseline_state"),
			ITEM_ACTIVE,
		)

	def test_no_changes_remain_and_cancel_update(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Empty successor cancel")
		d1 = make_approved_demand(title="Keep active")
		added1 = add_demand_to_plan(plan=plan["plan"], demand=d1["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added1["plan_item"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		d2 = make_approved_demand(title="Add then remove")
		added2 = add_demand_to_plan(plan=plan["plan"], demand=d2["demand"], user=planner)
		draft = frappe.db.get_value("Procurement Plan", plan["plan"], "open_draft_version")
		self.assertTrue(draft)
		remove_plan_item_from_plan(
			plan=plan["plan"],
			plan_item=added2["plan_item"],
			reason="Undo the addition",
			concurrency_token=self._token(draft),
			user=planner,
		)
		builder = get_plan_builder(plan=plan["plan"], user=planner)
		self.assertTrue(builder.get("no_changes_remain"))
		self.assertFalse(builder.get("can_submit_for_review"))
		self.assertTrue(builder.get("can_cancel_update"))
		cancelled = cancel_plan_update(
			plan=plan["plan"],
			concurrency_token=builder["concurrency_token"],
			user=planner,
		)
		self.assertTrue(cancelled["ok"])
		self.assertFalse(
			frappe.db.get_value("Procurement Plan", plan["plan"], "open_draft_version")
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Version", draft, "status"),
			"Cancelled",
		)

	def test_finance_release_hook_noop_and_idempotent(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Finance hook noop")
		d = make_approved_demand(title="No finance demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		first = release_draft_finance_effects(
			plan_item=added["plan_item"], version=plan["version"]
		)
		self.assertTrue(first["ok"])
		self.assertFalse(first.get("released"))
		self.assertFalse(first.get("cancelled_task"))
		second = release_draft_finance_effects(
			plan_item=added["plan_item"], version=plan["version"]
		)
		self.assertTrue(second["ok"])
		self.assertTrue(second.get("idempotent") or not second.get("released"))

	def test_builder_flags_draft_only_row(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Builder remove flags")
		d = make_approved_demand(title="Flag demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		builder = get_plan_builder(plan=plan["plan"], user=planner)
		row = next(r for r in builder["items"] if r["plan_item"] == added["plan_item"])
		self.assertTrue(row.get("can_remove_from_draft"))
		self.assertFalse(row.get("can_propose_removal"))
		self.assertEqual(row.get("removal_variant"), "draft")
