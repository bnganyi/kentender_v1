# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-002 — Workbench Include in Plan action opens active-plan modal."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.services.approved_demand_drawer import (
	get_approved_demand_planning_drawer,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP5IncludeInPlanActionP5002Contract(UnitTestCase):
	def test_router_wires_workbench_include_in_plan_primary_action(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountPlanningWorkList", 1)[1].split(
			"function bindWorkbenchQueueRefresh", 1
		)[0]
		self.assertIn("openWorkbenchIncludePlanModal", fn_block)
		self.assertIn('"include_in_plan"', fn_block)
		self.assertIn("onPrimaryAction", fn_block)
		self.assertIn("function openWorkbenchIncludePlanModal", source)
		self.assertIn("useActivePlanContext", source)

	def test_router_shares_include_plan_modal_launcher(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function openIncludePlanModalForShell", source)
		self.assertIn("function requestIncludePlanModalForShell", source)
		self.assertIn("ACTIVE_PLAN_API", source)
		self.assertIn("PlanningIncludePlanModal.open", source)

	def test_include_plan_modal_asset_registered(self) -> None:
		hooks_path = Path(__file__).resolve().parents[2].joinpath("hooks.py")
		hooks = hooks_path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("pp2_planning_include_plan_modal.js", hooks)


class TestPP5IncludeInPlanActionP5002Drawer(IntegrationTestCase):
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

	def test_drawer_ready_for_workbench_include_modal(self) -> None:
		"""PP5-002-BE-001: WORKS demand drawer supports Include in Plan modal launch."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_approved_demand_planning_drawer(demand_code=DEMAND_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual((out.get("demand") or {}).get("code"), DEMAND_CODE)
		eligibility = out.get("eligibility") or {}
		self.assertTrue(eligibility.get("allowed"), out)
		self.assertTrue((out.get("actions") or {}).get("include_in_plan"))

		with_plan = get_approved_demand_planning_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
			actor="Administrator",
		)
		self.assertTrue(with_plan.get("ok"), with_plan)
		target_plan = with_plan.get("target_plan") or {}
		self.assertEqual(target_plan.get("code"), PLAN_CODE)
