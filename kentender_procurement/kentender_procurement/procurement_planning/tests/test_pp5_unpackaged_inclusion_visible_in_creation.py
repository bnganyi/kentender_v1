# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Regression — demands "Added to Active Plan" but not yet packaged must be
findable on the Workbench (they disappear from Needs Planning by design, but
were previously unfindable anywhere else). They now surface as placeholder
rows in the "In Creation" (draft_packages) queue until a package is created
from them, closing the gap flagged by the user."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	get_workbench_item_view_model,
)


class TestPP5UnpackagedInclusionVisibleInCreation(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		out = ensure_pp5_needs_planning_ready(force_reset=True)
		self.assertTrue(out.get("ok"), out)

	def _include_demand(self) -> dict:
		out = include_pp_demand_in_procurement_plan(
			demand_code=DEMAND_CODE,
			procurement_plan_code=PLAN_CODE,
			demand_item_codes=f'["{DEMAND_ITEM_CODE}"]',
		)
		self.assertTrue(out.get("ok"), out)
		return out

	def test_001_included_demand_absent_before_inclusion(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_workbench_item_view_model(queue="draft_packages", actor="Administrator", limit=100)
		self.assertTrue(out.get("ok"), out)
		codes = [str(item.get("demand_code") or "") for item in out.get("items") or []]
		self.assertNotIn(DEMAND_CODE, codes)

	def test_002_included_demand_appears_as_placeholder_in_creation(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		include_out = self._include_demand()

		out = get_workbench_item_view_model(queue="draft_packages", actor="Administrator", limit=100)
		self.assertTrue(out.get("ok"), out)
		items = out.get("items") or []
		match = next((item for item in items if item.get("demand_code") == DEMAND_CODE), None)
		self.assertIsNotNone(match, items)
		self.assertTrue(match.get("is_placeholder"))
		self.assertEqual(match.get("inclusion_code"), include_out.get("inclusion_code"))
		self.assertEqual(match.get("underlying_object_id"), "")
		self.assertEqual(match.get("status_pill_label"), "Added to Active Plan")
		self.assertEqual(match.get("primary_action", {}).get("action"), "create_package_from_inclusion")
		self.assertGreater(flt_safe(match.get("estimated_value_number")), 0)

		# Regression-guard the never-expose-internal-hash-id rule for the
		# placeholder's department field too (same class of bug as the real
		# Needs Planning department-name fix).
		dept_label = str(match.get("department_label") or "")
		if dept_label:
			self.assertFalse(frappe.db.exists("Procuring Department", dept_label))

	def test_003_count_badge_includes_placeholder(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		before = get_workbench_item_view_model(queue="draft_packages", actor="Administrator", limit=1)
		self._include_demand()
		after = get_workbench_item_view_model(queue="draft_packages", actor="Administrator", limit=1)
		self.assertEqual(int(after.get("total") or 0), int(before.get("total") or 0) + 1)

	def test_004_placeholder_replaced_by_real_package_after_create(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		include_out = self._include_demand()
		create_out = create_pp_package_from_planning_inclusion(inclusion_code=include_out.get("inclusion_code"))
		self.assertTrue(create_out.get("ok"), create_out)

		# The freshly created package's business code doesn't match this demo
		# environment's WORKS-master code prefix, so it needs
		# `include_test_data=True` to survive `filter_demo_workbench_items`
		# (pre-existing demo-scope behavior, unrelated to this feature).
		out = get_workbench_item_view_model(
			queue="draft_packages", actor="Administrator", limit=100, include_test_data=True
		)
		self.assertTrue(out.get("ok"), out)
		items = out.get("items") or []
		placeholder_match = next(
			(item for item in items if item.get("demand_code") == DEMAND_CODE and item.get("is_placeholder")),
			None,
		)
		self.assertIsNone(placeholder_match, items)
		package_match = next(
			(item for item in items if item.get("underlying_object_id") == create_out.get("package_code")),
			None,
		)
		self.assertIsNotNone(package_match, items)
		self.assertFalse(package_match.get("is_placeholder"))


def flt_safe(value) -> float:
	try:
		return float(value or 0)
	except (TypeError, ValueError):
		return 0.0
