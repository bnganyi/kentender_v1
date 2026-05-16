# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS strategy purge + verify (companion to R2-004).

Run:
  bench --site kentender.midas.com run-tests --app kentender_strategy \\
    --module kentender_strategy.tests.test_r2_004_works_master_strategy_purge
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_procuring_entity
from kentender_strategy.seeds import works_master_strategy_hierarchy as wsh
from kentender_strategy.seeds.seed_works_master_strategy_purge import reset_to_works_master
from kentender_strategy.seeds.works_master_strategy_purge import (
	purge_non_works_strategy_hierarchy,
	verify_works_master_strategy_seed,
)
from kentender_strategy.tests.test_r2_004_works_master_strategy_seed import (
	_purge_plan_chain_for_tests,
)


class TestR2004WorksMasterStrategyPurge(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.pe = ensure_procuring_entity("PE-MOH", "Ministry of Health")
		_purge_plan_chain_for_tests(self.pe)

	def tearDown(self):
		_purge_plan_chain_for_tests(self.pe)

	def test_purge_removes_junk_plan_keeps_works(self):
		junk = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "KT purge junk plan",
				"procuring_entity": self.pe,
				"start_year": 2025,
				"end_year": 2028,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		)
		junk.insert(ignore_permissions=True)
		out_seed = wsh.upsert_works_master_strategy_hierarchy()
		self.assertTrue(out_seed.get("ok"))
		self.assertGreaterEqual(len(frappe.get_all("Strategic Plan", pluck="name")), 2)

		p = purge_non_works_strategy_hierarchy(
			dry_run=False,
			delete_blocking_demands_and_budget_lines=False,
			restrict_procuring_entity_names=[self.pe],
		)
		self.assertTrue(p.get("ok"), msg=str(p))
		self.assertIn(junk.name, p.get("removed_strategic_plans", []))

		v = verify_works_master_strategy_seed()
		self.assertTrue(v.get("ok"), msg=str(v.get("checks")))

	def test_purge_dry_run_does_not_delete(self):
		junk = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "KT dry run junk",
				"procuring_entity": self.pe,
				"start_year": 2024,
				"end_year": 2027,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		)
		junk.insert(ignore_permissions=True)
		before = len(frappe.get_all("Strategic Plan", pluck="name"))
		p = purge_non_works_strategy_hierarchy(dry_run=True, delete_blocking_demands_and_budget_lines=False, restrict_procuring_entity_names=[self.pe])
		self.assertIn(junk.name, p.get("removed_strategic_plans", []))
		after = len(frappe.get_all("Strategic Plan", pluck="name"))
		self.assertEqual(after, before)
		frappe.delete_doc("Strategic Plan", junk.name, force=1, ignore_permissions=True)

	def test_reset_to_works_master_end_to_end(self):
		junk = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "KT reset junk",
				"procuring_entity": self.pe,
				"start_year": 2024,
				"end_year": 2027,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		)
		junk.insert(ignore_permissions=True)
		out = reset_to_works_master(
			delete_blocking_demands_and_budget_lines=False,
			restrict_procuring_entity_names=[self.pe],
		)
		self.assertTrue(out.get("ok"), msg=str(out))
		self.assertTrue(out["verify"].get("ok"))
		self.assertEqual(out["verify"].get("desk_list_title"), wsh.PLAN_TITLE)
