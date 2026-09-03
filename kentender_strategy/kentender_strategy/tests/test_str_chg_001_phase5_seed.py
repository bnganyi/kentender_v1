# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 Phase 5 seed contract, reworked for AUTH-ADR-001 v1.6
(CU-307): the two-Procuring-Entity `kentender_mvp_v1` strategy seed cannot
exist on a one-PE site and is superseded, archived not deleted. The live
seed surface is the works-master fixture (site-local, governed grants) plus
kentender_core's own site_setup world; both are covered where they live
(phase 6 here, kentender_core's suites there).
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.kentender_mvp_v1_strategy import upsert_kentender_mvp_v1_strategy


class TestLegacySeedSuperseded(FrappeTestCase):
	def test_legacy_two_pe_seed_reports_superseded_and_writes_nothing(self):
		plans_before = frappe.db.count("Strategic Plan")
		users_before = frappe.db.count("User")

		out = upsert_kentender_mvp_v1_strategy()

		self.assertFalse(out["ok"])
		self.assertIn("site_setup", out["superseded"])
		self.assertEqual(frappe.db.count("Strategic Plan"), plans_before)
		self.assertEqual(frappe.db.count("User"), users_before)

	def test_legacy_kisumu_world_is_absent(self):
		"""The superseded seed's second entity never appears on a v1.6 site."""
		self.assertEqual(
			frappe.db.count("Strategic Plan", {"title": ("like", "%Kisumu%")}), 0
		)
