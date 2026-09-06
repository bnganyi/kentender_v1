# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 6 — downstream consumer migration.

Covers the "Works Master" demo fixture rebuild (kentender_budget's and
kentender_procurement's shared seed dependency) and confirms the real
cross-app contract surface Phase 4 fixed is exercised end-to-end, not just
unit-tested in isolation.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	PE_MOH,
	resolve_site_entity_code,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_consumer import (
	apply_budget_primary_strategy_reference,
	get_strategy_lineage,
	target_snapshot_fields,
)
from kentender_strategy.services.strategy_consumer import list_active_targets


class TestWorksMasterFixtureRebuilt(FrappeTestCase):
	def test_resolve_site_entity_code_no_fallback(self):
		self.assertEqual(resolve_site_entity_code(), PE_MOH)

	def test_seed_idempotent_and_produces_real_active_data(self):
		first = upsert_works_master_strategy_hierarchy()
		second = upsert_works_master_strategy_hierarchy()

		self.assertTrue(first["ok"])
		self.assertEqual(first["plan"], second["plan"])
		self.assertEqual(first["target"], second["target"])
		self.assertTrue(second.get("already_seeded"))

		version = frappe.get_doc("Strategic Plan Version", first["plan"])
		self.assertEqual(version.status, "Active")

		objective = frappe.get_doc("Strategy Node", first["objective"])
		self.assertEqual(objective.node_type, "Strategic Objective")

	def test_budget_consumer_functions_work_against_the_fixture(self):
		"""The exact functions kentender_budget's budget_line_contracts.py
		calls — apply_budget_primary_strategy_reference and
		target_snapshot_fields — proven against a real Active target, not a
		throwaway one, closing the loop on the Phase 1-flagged regression."""
		out = upsert_works_master_strategy_hierarchy()

		snapshot = target_snapshot_fields(out["target"])
		self.assertIsNotNone(snapshot)
		self.assertEqual(snapshot["plan_version"], out["plan"])

		class _FakeBudgetLine:
			primary_target_id = None
			primary_target_code = None
			primary_target_name = None
			primary_plan_version_id = None
			primary_snapshot_label = None
			primary_strategy_linked = 0

		doc = _FakeBudgetLine()
		ref = apply_budget_primary_strategy_reference(doc, out["target"])
		self.assertEqual(doc.primary_target_id, out["target"])
		self.assertEqual(doc.primary_plan_version_id, out["plan"])
		self.assertEqual(doc.primary_strategy_linked, 1)
		self.assertIsNotNone(ref)

	def test_get_strategy_lineage_resolves_the_fixture_objective(self):
		"""The same contract kentender_procurement's rebuilt
		strategy_alignment_handoff.py now uses instead of a direct Strategy
		table read."""
		out = upsert_works_master_strategy_hierarchy()
		lineage = get_strategy_lineage(out["objective"])
		types = [p["type"] for p in lineage["path"]]
		self.assertEqual(types, ["Pillar", "Programme", "Strategic Objective"])
		self.assertEqual(lineage["path"][-1]["id"], out["objective"])

	def test_list_active_targets_matches_current_schema_str_908(self):
		"""Real gap found during Phase 9's static scan (STR-908): this
		function — the one `kentender_budget`'s own live
		`budget_live_bind.js::loadTargetOptions` calls via
		`kentender_strategy.api.strategy_api.list_active_targets` to
		populate the Budget Line "primary target" dropdown — still filtered
		on `Strategic Plan.status`/`plan_code` and
		`Performance Target.plan_version`/`target_code`/`title`/`status`,
		none of which exist post-Phase-1 (status moved to `Strategic Plan
		Version`; `Performance Target` links only via `indicator_id`).
		Every real call from Budget's UI has been silently returning an
		empty dropdown since Phase 1 (the JS `error:` callback swallows the
		failure and resolves `[]`). Fixed in this same phase to match the
		already-correct sibling functions in this module
		(`validate_strategy_reference`/`build_strategy_reference`)."""
		out = upsert_works_master_strategy_hierarchy()

		refs = list_active_targets()

		self.assertTrue(any(r["node_id"] == out["target"] for r in refs))
		matched = next(r for r in refs if r["node_id"] == out["target"])
		self.assertEqual(matched["plan_version_id"], out["plan"])
		self.assertTrue(matched["node_name"])
