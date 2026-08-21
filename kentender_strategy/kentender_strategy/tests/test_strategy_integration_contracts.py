# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §12 — the 5 named integration contracts in strategy_consumer.py."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_consumer import (
	create_strategy_snapshot,
	get_strategy_lineage,
	list_strategy_commitments,
	record_verified_result,
	resolve_commitment_id,
	resolve_strategy_context,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles


def _force_status(plan_name: str, status: str) -> None:
	frappe.db.set_value("Strategic Plan", plan_name, "status", status, update_modified=False)


class TestStrategyIntegrationContracts(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan = cls.seed["plan"]
		cls.target = cls.seed["target"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	# -- resolve_strategy_context -------------------------------------------------

	def test_resolve_strategy_context_returns_primary_plan(self):
		context = resolve_strategy_context(self.pe)
		self.assertEqual(context["primary_plan"]["id"], self.plan)
		self.assertEqual(context["primary_plan"]["code"], STRATEGY_PLAN_CODE)
		self.assertIn("supporting_plans", context)

	def test_resolve_strategy_context_errors_on_no_coverage(self):
		with self.assertRaises(frappe.DoesNotExistError):
			resolve_strategy_context(self.pe, effective_date="1999-01-01")

	def test_resolve_strategy_context_errors_on_ambiguous_lineage(self):
		"""Defensive path: if two primary Active plans ever coexist for the same
		entity+date (Phase 6 blocks this at activation time, but this contract
		must still fail loudly rather than silently pick one)."""
		dupe = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": f"CTX-DUPE-{frappe.generate_hash(length=6).upper()}",
				"version_number": 1,
				"title": "Context ambiguity fixture",
				"procuring_entity": self.pe,
				"plan_type": "Entity Strategic Plan",
				"scope_type": "Procuring Entity",
				"scope_id": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.addCleanup(
			lambda: frappe.delete_doc("Strategic Plan", dupe.name, force=True, ignore_permissions=True)
		)
		_force_status(dupe.name, "Active")
		with self.assertRaises(frappe.ValidationError):
			resolve_strategy_context(self.pe)

	# -- list_strategy_commitments -------------------------------------------------

	def test_list_strategy_commitments_only_locked(self):
		rows = list_strategy_commitments(procuring_entity=self.pe)
		self.assertTrue(rows)
		for r in rows:
			self.assertEqual(r["status"], "Locked")

	def test_list_strategy_commitments_filters_by_target(self):
		all_rows = list_strategy_commitments(plan_version=self.plan)
		linked = [
			r
			for r in all_rows
			if any((ln.get("target") or {}).get("id") == self.target for ln in r.get("links") or [])
		]
		filtered = list_strategy_commitments(plan_version=self.plan, target_id=self.target)
		self.assertEqual({r["id"] for r in filtered}, {r["id"] for r in linked})

	# -- get_strategy_lineage -------------------------------------------------

	def test_get_strategy_lineage_matches_build_strategy_reference(self):
		lineage = get_strategy_lineage(plan_version=self.plan, node_id=self.target)
		self.assertEqual(lineage["node_id"], self.target)
		self.assertEqual(lineage["plan_code"], STRATEGY_PLAN_CODE)
		types = {p["type"] for p in lineage["path"]}
		self.assertIn("PerformanceTarget", types)
		self.assertIn("PerformanceIndicator", types)

	def test_get_strategy_lineage_rejects_unsupported_node_type(self):
		with self.assertRaises(frappe.ValidationError):
			get_strategy_lineage(plan_version=self.plan, node_id=self.target, node_type="Bogus")

	# -- create_strategy_snapshot -------------------------------------------------

	def test_create_strategy_snapshot_idempotent_by_correlation_key(self):
		first = create_strategy_snapshot(
			plan_version=self.plan, node_id=self.target, correlation_key="BL-TEST-0001"
		)
		second = create_strategy_snapshot(
			plan_version=self.plan, node_id=self.target, correlation_key="BL-TEST-0001"
		)
		self.assertEqual(first["node_code"], TARGET_CODE)
		self.assertEqual(first["snapshot_label"], second["snapshot_label"])
		self.assertEqual(first["path"], second["path"])

	def test_create_strategy_snapshot_requires_correlation_key(self):
		with self.assertRaises(frappe.ValidationError):
			create_strategy_snapshot(plan_version=self.plan, node_id=self.target, correlation_key="")

	def test_create_strategy_snapshot_rejects_invalid_reference(self):
		with self.assertRaises(frappe.ValidationError):
			create_strategy_snapshot(
				plan_version=self.plan, node_id="not-a-real-target", correlation_key="BL-TEST-0002"
			)

	def test_create_strategy_snapshot_is_audited(self):
		"""STR-FR-022 — downstream-resolution actions are audited."""
		key = f"BL-AUDIT-{frappe.generate_hash(length=6).upper()}"
		create_strategy_snapshot(plan_version=self.plan, node_id=self.target, correlation_key=key)
		self.assertTrue(
			frappe.db.exists(
				"Strategy Audit Event",
				{
					"entity_type": "PerformanceTarget",
					"entity_name": self.target,
					"event_type": "Strategy Snapshot Created",
					"reason": key,
				},
			)
		)

	# -- record_verified_result -------------------------------------------------

	def test_record_verified_result_is_deferred_stub(self):
		with self.assertRaises(NotImplementedError):
			record_verified_result()

	# -- resolve_commitment_id -------------------------------------------------

	def test_resolve_commitment_id_round_trips(self):
		commitments = list_strategy_commitments(plan_version=self.plan)
		self.assertTrue(commitments)
		row = commitments[0]
		commitment_code = row["objective"]["code"]
		self.assertEqual(resolve_commitment_id(commitment_code), row["id"])

	def test_resolve_commitment_id_unknown_code(self):
		self.assertIsNone(resolve_commitment_id("NOT-A-REAL-CODE"))
