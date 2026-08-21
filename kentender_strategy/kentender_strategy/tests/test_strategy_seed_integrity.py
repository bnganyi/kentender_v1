# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §13 / SCL-804..805 — seed determinism, no first-PE fallback,
idempotent double-run."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.kentender_mvp_v1_strategy import (
	upsert_kentender_mvp_v1_strategy,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	resolve_procuring_entity_moh,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles


class TestStrategySeedIntegrity(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_resolve_procuring_entity_moh_finds_seeded_entity(self):
		self.assertEqual(resolve_procuring_entity_moh(), self.seed["procuring_entity"])

	def test_resolve_procuring_entity_moh_no_first_pe_fallback(self):
		"""SCL-804 — with no code/name match, must return None, never an
		arbitrary Procuring Entity (there are several others seeded: Kisumu,
		test fixtures, etc.). Temporarily disables PE-MOH's identifying
		fields and restores them via addCleanup."""
		pe = self.seed["procuring_entity"]
		original = frappe.db.get_value(
			"Procuring Entity", pe, ["entity_code", "entity_name"], as_dict=True
		)
		self.addCleanup(
			lambda: frappe.db.set_value(
				"Procuring Entity",
				pe,
				{"entity_code": original.entity_code, "entity_name": original.entity_name},
				update_modified=False,
			)
		)
		frappe.db.set_value(
			"Procuring Entity",
			pe,
			{"entity_code": "PE-MOH-TEMP-DISABLED", "entity_name": "Temporarily Disabled Entity"},
			update_modified=False,
		)
		self.assertIsNone(resolve_procuring_entity_moh())

	def test_seed_double_run_is_idempotent(self):
		"""SCL-805 / STR-AC-014 — rerunning without reset creates nothing new
		and returns the same identities."""
		first = upsert_kentender_mvp_v1_strategy()
		second = upsert_kentender_mvp_v1_strategy()
		self.assertFalse(first.get("created"))
		self.assertFalse(second.get("created"))
		self.assertEqual(first["plan"], second["plan"])
		self.assertEqual(first["target_avail"], second["target_avail"])
		self.assertEqual(first["pvcs"], second["pvcs"])
		self.assertEqual(first["kisumu"]["plan"], second["kisumu"]["plan"])
		self.assertEqual(first["kisumu"]["target"], second["kisumu"]["target"])
		self.assertEqual(first["kisumu"]["pvcs"], second["kisumu"]["pvcs"])

	def test_seed_double_run_creates_no_duplicate_rows(self):
		plan = self.seed["plan"]
		counts_before = {
			dt: frappe.db.count(dt, {"plan_version": plan})
			for dt in (
				"Strategy Programme",
				"Strategy Sub Programme",
				"Strategic Objective",
				"Strategic Outcome",
				"Performance Indicator",
				"Performance Target",
				"Strategy Value Commitment",
			)
		}
		upsert_kentender_mvp_v1_strategy()
		counts_after = {
			dt: frappe.db.count(dt, {"plan_version": plan}) for dt in counts_before
		}
		self.assertEqual(counts_before, counts_after)
