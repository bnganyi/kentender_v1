# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-007 — Create Package success offers Open Package on Workbench."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

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


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP5CreatePackageSuccessP5007Contract(UnitTestCase):
	def test_router_mounts_create_package_success_helpers(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function createPackageSuccessSummary", source)
		self.assertIn("function mountCreatePackageSuccessSummary", source)
		self.assertIn("open_package_next", source)
		self.assertIn("pp2-open-package-next-action", source)

	def test_workbench_selected_summary_renders_create_package_success(self) -> None:
		path = _pkg_public("js", "pp3_planning_selected_work_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("createPackageSuccess", source)
		self.assertIn("pp2-create-package-success", source)
		self.assertIn("pp2-open-package-next-action", source)

	def test_router_open_package_navigates_to_draft_packages_queue(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function buildWorkbenchOpenPackageUrl", source)
		open_pkg_block = source.split("function buildWorkbenchOpenPackageUrl", 1)[1].split(
			"function createPackageSuccessSummary", 1
		)[0]
		self.assertIn("draft-packages", open_pkg_block)
		fn_block = source.split("function mountCreatePackageSuccessSummary", 1)[1].split(
			"function includePlanSuccessSummary", 1
		)[0]
		self.assertIn("buildWorkbenchOpenPackageUrl", fn_block)
		self.assertIn("open_package_next", fn_block)


class TestPP5CreatePackageSuccessP5007Create(IntegrationTestCase):
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

	def test_create_package_returns_package_code_for_open_package(self) -> None:
		"""PP5-007-BE-001: live create succeeds and returns package identity."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = create_pp_package_from_planning_inclusion(inclusion_code=self.inclusion_code)
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(str(out.get("package_code") or "").strip())
		package = out.get("package") or {}
		self.assertTrue(
			str(package.get("package_name") or "").strip()
			or str(out.get("package_code") or "").strip()
		)
