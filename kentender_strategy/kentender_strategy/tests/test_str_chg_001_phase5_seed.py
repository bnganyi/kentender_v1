# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 §14 seed contract, rebuilt for AUTH-ADR-001 v1.6 /
SEED-001 §3.4 (2026-09-05, FU-10 closed): `upsert_kentender_mvp_v1_strategy`
was a permanent stub reporting "superseded" for the old two-Procuring-Entity
(MOH + Kisumu) world, which cannot exist on a one-PE site. It is now a real,
idempotent seed that drives the single Ministry of Health plan through the
governed commands (`save_strategy_plan_draft`, `save_strategy_structure_draft`,
`transition_plan_version`) as the named §14.1 actors granted by
`kentender_core.seeds.site_setup` — this seed creates no user of its own.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.kentender_mvp_v1_strategy import (
	PLAN_TITLE,
	upsert_kentender_mvp_v1_strategy,
)

OBJECTIVE_TITLE = "Strengthen interoperable national digital health services"


class TestMohPlanSeed(FrappeTestCase):
	def test_the_seed_builds_the_real_moh_plan_and_is_idempotent(self):
		out = upsert_kentender_mvp_v1_strategy()
		self.assertTrue(out["ok"])
		self.assertTrue(out["moh"]["ok"])
		plan = out["moh"]["plan"]
		self.assertEqual(frappe.db.get_value("Strategic Plan", plan, "title"), PLAN_TITLE)
		self.assertTrue(
			frappe.db.exists("Strategy Node", {"title": OBJECTIVE_TITLE, "node_type": "Strategic Objective"})
		)

		plans_before = frappe.db.count("Strategic Plan")
		again = upsert_kentender_mvp_v1_strategy()
		self.assertTrue(again["moh"]["already_seeded"])
		self.assertEqual(again["moh"]["plan"], plan)
		self.assertEqual(frappe.db.count("Strategic Plan"), plans_before)

	def test_legacy_kisumu_world_is_absent(self):
		"""The retired seed's second entity never appears on a v1.6 site."""
		self.assertEqual(
			frappe.db.count("Strategic Plan", {"title": ("like", "%Kisumu%")}), 0
		)
