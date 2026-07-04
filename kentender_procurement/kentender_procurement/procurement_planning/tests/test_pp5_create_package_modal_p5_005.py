# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-005 — Create Package modal shows business context on Workbench."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	get_pp_create_package_modal_drawer,
)
from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	PLAN_CODE,
	PLAN_NAME,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP5CreatePackageModalP5005Contract(UnitTestCase):
	def test_create_package_modal_asset_registered(self) -> None:
		hooks_path = Path(__file__).resolve().parents[2].joinpath("hooks.py")
		hooks = hooks_path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("pp2_planning_create_package_modal.js", hooks)

	def test_create_package_modal_renders_business_context(self) -> None:
		path = _pkg_public("js", "pp2_planning_create_package_modal.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"pp2-create-package-modal",
			"pp2-create-package-demand",
			"pp2-create-package-active-plan",
			"pp2-create-package-category",
			"pp2-create-package-method",
			"pp2-create-package-value",
			"pp2-create-package-funding",
			"pp2-create-package-title-input",
			"pp2-confirm-create-package",
		):
			self.assertIn(tid, source)

	def test_router_wires_create_package_wizard_launcher(self) -> None:
		"""PW11 — `openCreatePackageModalForShell` still runs the P5-005
		drawer pre-flight (blocker/duplicate-package detection), but now
		launches the Package Creation Wizard instead of the retired
		single-field `PlanningCreatePackageModal` dialog."""
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function openCreatePackageModalForShell", source)
		self.assertIn("CREATE_PACKAGE_DRAWER_API", source)
		self.assertIn("PlanningPackageWizard.open", source)
		self.assertNotIn("PlanningCreatePackageModal.open", source)
		success_block = source.split("function mountIncludePlanSuccessSummary", 1)[1].split(
			"function openIncludePlanModalForShell", 1
		)[0]
		self.assertIn("openCreatePackageModalForShell", success_block)


class TestPP5CreatePackageModalP5005Drawer(IntegrationTestCase):
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
		include_out = include_pp_demand_in_procurement_plan(
			demand_code=DEMAND_CODE,
			procurement_plan_code=PLAN_CODE,
			demand_item_codes=f'["{DEMAND_ITEM_CODE}"]',
		)
		self.assertTrue(include_out.get("ok"), include_out)
		self.inclusion_code = str(include_out.get("inclusion_code") or "").strip()

	def test_drawer_returns_modal_business_fields(self) -> None:
		"""PP5-005-BE-001: included demand exposes Create Package modal labels."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_pp_create_package_modal_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
			inclusion_code=self.inclusion_code,
		)
		self.assertTrue(out.get("ok"), out)
		self.assertIn("District Hospital Renovation Works", out.get("demand_name") or "")
		self.assertEqual(out.get("active_plan_name"), PLAN_NAME)
		self.assertEqual(out.get("category_label"), "Works")
		self.assertEqual(out.get("method_label"), "Open Tender")
		self.assertIn("KES", out.get("value_label") or "")
		self.assertEqual(out.get("funding_label"), "Budget linked")
		self.assertEqual(
			out.get("package_title_default"),
			out.get("demand_name"),
		)
		self.assertTrue(out.get("create_allowed"), out)
