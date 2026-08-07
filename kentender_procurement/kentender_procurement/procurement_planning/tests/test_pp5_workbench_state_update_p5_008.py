# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-008 — Workbench state update after package creation."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import DEMAND_TITLE
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


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


def _find_demand_item(items: list[dict]) -> dict | None:
	for item in items or []:
		if str(item.get("underlying_object_code") or "").strip() == DEMAND_CODE:
			return item
	return None


def _find_package_item(items: list[dict], *, title: str | None = None) -> dict | None:
	for item in items or []:
		if str(item.get("underlying_object_type") or "").strip() != "procurement_package":
			continue
		if title and str(item.get("title") or "").strip() != title:
			continue
		return item
	return None


class TestPP5WorkbenchStateUpdateP5008Contract(UnitTestCase):
	def test_router_navigates_back_to_workbench_draft_packages(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function buildWorkbenchOpenPackageUrl", source)
		fn_block = source.split("function mountCreatePackageSuccessSummary", 1)[1].split(
			"function includePlanSuccessSummary", 1
		)[0]
		self.assertIn("buildWorkbenchOpenPackageUrl", fn_block)

	def test_back_to_workbench_switches_to_draft_packages(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountCreatePackageSuccessSummary", 1)[1].split(
			"function includePlanSuccessSummary", 1
		)[0]
		self.assertIn('actionKey === "back_to_workbench"', fn_block)
		self.assertIn("buildWorkbenchOpenPackageUrl", fn_block)

	def test_work_list_selects_package_from_url(self) -> None:
		path = _pkg_public("js", "pp3_planning_work_list.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("package_code", source)
		self.assertIn("selectedIdForItems", source)


class TestPP5WorkbenchStateUpdateP5008Queues(IntegrationTestCase):
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
		create_out = create_pp_package_from_planning_inclusion(
			inclusion_code=str(include_out.get("inclusion_code") or "").strip(),
		)
		self.assertTrue(create_out.get("ok"), create_out)
		self.package_code = str(create_out.get("package_code") or "").strip()

	def test_works_demand_leaves_needs_planning_after_package_create(self) -> None:
		"""PP5-008-BE-001: packaged demand no longer appears in Needs Planning."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_workbench_item_view_model(
			queue="needs_planning",
			actor="Administrator",
			limit=200,
			start=0,
		)
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(_find_demand_item(out.get("items") or []), out)

	def test_works_package_appears_in_draft_packages_queue(self) -> None:
		"""PP5-008-BE-002: created package appears in Draft Packages with Open Package."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_workbench_item_view_model(
			queue="draft_packages",
			actor="Administrator",
			limit=200,
			start=0,
		)
		self.assertTrue(out.get("ok"), out)
		item = _find_package_item(out.get("items") or [], title=DEMAND_TITLE)
		if item is None:
			item = _find_package_item(out.get("items") or [])
		self.assertIsNotNone(item, out)
		assert item is not None
		self.assertEqual(item.get("queue"), "draft_packages")
		self.assertIn(str(item.get("state_label") or "").strip(), ("Draft package", "Draft"))
		self.assertIn(
			str(item.get("next_action_label") or "").strip(),
			("Open Package", "Complete Package"),
		)
		self.assertIn(
			str((item.get("primary_action") or {}).get("action") or "").strip(),
			("open_package", "complete_package"),
		)
		if self.package_code:
			self.assertEqual(str(item.get("underlying_object_code") or "").strip(), self.package_code)

	def test_works_package_visible_to_planner_in_draft_packages(self) -> None:
		"""PP5-008-BE-003: scoped planner sees created package in Draft Packages."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		if not frappe.db.exists("User", "planner@moh.test"):
			self.skipTest("planner@moh.test not configured")

		frappe.set_user("planner@moh.test")
		out = get_workbench_item_view_model(
			queue="draft_packages",
			actor="planner@moh.test",
			limit=200,
			start=0,
		)
		self.assertTrue(out.get("ok"), out)
		item = _find_package_item(out.get("items") or [], title=DEMAND_TITLE)
		self.assertIsNotNone(item, out)
