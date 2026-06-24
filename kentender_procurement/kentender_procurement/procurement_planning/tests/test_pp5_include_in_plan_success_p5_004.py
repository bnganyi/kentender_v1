# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-004 — Include in Plan success offers Create Package on Workbench."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	PLAN_CODE,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP5IncludeInPlanSuccessP5004Contract(UnitTestCase):
	def test_router_mounts_include_success_summary_helper(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function includePlanSuccessSummary", source)
		self.assertIn("function mountIncludePlanSuccessSummary", source)
		self.assertIn("create_package_next", source)
		self.assertIn("pp2-create-package-next-action", source)

	def test_router_workbench_success_uses_back_to_workbench(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function includePlanSuccessSummary", 1)[1].split(
			"function mountIncludePlanSuccessSummary", 1
		)[0]
		self.assertIn("back_to_workbench", fn_block)
		self.assertIn('__("Back to Workbench")', fn_block)

	def test_workbench_selected_summary_renders_include_success(self) -> None:
		path = _pkg_public("js", "pp3_planning_selected_work_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("includeSuccess", source)
		self.assertIn("pp2-include-plan-success", source)
		self.assertIn("pp2-create-package-next-action", source)


class TestPP5IncludeInPlanSuccessP5004Include(IntegrationTestCase):
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

	def test_include_demand_returns_success_payload(self) -> None:
		"""PP5-004-BE-001: live include succeeds for golden-path demand."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = include_pp_demand_in_procurement_plan(
			demand_code=DEMAND_CODE,
			procurement_plan_code=PLAN_CODE,
			demand_item_codes=f'["{DEMAND_ITEM_CODE}"]',
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("demand_code"), DEMAND_CODE)
		self.assertEqual(out.get("procurement_plan_code"), PLAN_CODE)
		self.assertTrue(str(out.get("inclusion_code") or "").strip())
