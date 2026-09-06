# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable platform seed pack — load, clear, validate integration tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.stable_platform_seed.clear import clear_stable_platform_seed
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_DEMAND_CODE,
	IT_PKG_CODE,
	WORKS_DEMAND_CODE,
	WORKS_PKG_CODE,
	WORKS_PLAN_CODE,
)
from kentender_core.seeds.stable_platform_seed.load import load_stable_platform_seed
from kentender_core.seeds.stable_platform_seed.validate import validate_stable_platform_seed

# The STD Engine was retired on 2026-09-05. These tests used to skip unless the
# IT STD v1_1 package zip was on disk, and asserted the imported STD Version /
# clause counts. The seed's STD stage is now a no-op skip, so the guards are
# gone and the tests cover the rest of the pack unconditionally.


class TestStablePlatformSeed(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_load_clear_reload_cycle(self) -> None:
		clear_stable_platform_seed(purge_non_master=False, skip_guard=True)
		frappe.db.commit()

		loaded = load_stable_platform_seed(
			reset=False,
			planning_checkpoint="PACKAGE_DRAFT",
			import_it_std=True,
			include_it_supplement=True,
			purge_non_master=False,
		)
		self.assertTrue(loaded.get("ok"), loaded)

		validation = validate_stable_platform_seed(planning_checkpoint="PACKAGE_DRAFT")
		self.assertEqual(validation.get("failed_count"), 0, validation)

		self.assertTrue(frappe.db.exists("Procurement Plan", WORKS_PLAN_CODE))
		self.assertTrue(frappe.db.exists("Procurement Package", WORKS_PKG_CODE))
		self.assertTrue(frappe.db.exists("Procurement Package", IT_PKG_CODE))
		self.assertEqual(
			frappe.db.get_value("Demand", {"demand_id": WORKS_DEMAND_CODE}, "status"),
			"Approved",
		)
		self.assertEqual(
			frappe.db.get_value("Demand", {"demand_id": IT_DEMAND_CODE}, "status"),
			"Approved",
		)
		self.assertEqual(
			(loaded.get("stages") or {}).get("std_it", {}).get("reason"),
			"STD_ENGINE_RETIRED",
			loaded,
		)

	def test_reset_then_load_is_idempotent(self) -> None:
		first = load_stable_platform_seed(
			reset=True,
			planning_checkpoint="PACKAGE_DRAFT",
			purge_non_master=False,
		)
		self.assertTrue(first.get("ok"), first)

		second = load_stable_platform_seed(
			reset=False,
			planning_checkpoint="PACKAGE_DRAFT",
			purge_non_master=False,
		)
		self.assertTrue(second.get("ok"), second)

		validation = validate_stable_platform_seed(planning_checkpoint="PACKAGE_DRAFT")
		self.assertEqual(validation.get("failed_count"), 0, validation)

	def test_clear_removes_it_supplement_rows(self) -> None:
		load_stable_platform_seed(
			reset=True,
			planning_checkpoint="INCLUDED_IN_PLAN",
			purge_non_master=False,
		)
		self.assertTrue(frappe.db.exists("Procurement Package", IT_PKG_CODE))

		cleared = clear_stable_platform_seed(purge_non_master=False, skip_guard=True)
		self.assertTrue(cleared.get("ok"), cleared)
		frappe.db.commit()

		self.assertFalse(frappe.db.exists("Procurement Package", IT_PKG_CODE))
		self.assertFalse(frappe.db.exists("Demand", {"demand_id": IT_DEMAND_CODE}))
