# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-006 — Create Package validation blocks missing plan, funding, duplicate package."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
	get_pp_create_package_modal_drawer,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.services.planning_references import (
	resolve_demand_name,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageFromInclusion,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP5CreatePackageValidationP5006Contract(UnitTestCase):
	def test_drawer_service_evaluates_validation(self) -> None:
		path = Path(__file__).resolve().parents[2].joinpath(
			"procurement_planning",
			"services",
			"create_package_modal_drawer.py",
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("_evaluate_create_package_validation", source)
		self.assertIn("PackageFromInclusion.ACTIVE_PLAN_REQUIRED", source)
		self.assertIn("PackageFromInclusion.FUNDING_REQUIRED", source)
		self.assertIn("PackageFromInclusion.PACKAGE_ALREADY_EXISTS", source)

	def test_create_package_modal_handles_blockers_and_duplicate(self) -> None:
		path = _pkg_public("js", "pp2_planning_create_package_modal.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("showCreatePackageBlocker", source)
		self.assertIn("showDuplicatePackageDialog", source)
		self.assertIn("pp2-create-package-blocker-message", source)
		self.assertIn("pp2-create-package-duplicate-dialog", source)
		self.assertIn("pp2-open-existing-package", source)


class TestPP5CreatePackageValidationP5006Drawer(IntegrationTestCase):
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

	def test_blocks_when_demand_not_included(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		reset_out = ensure_pp5_needs_planning_ready(force_reset=True)
		self.assertTrue(reset_out.get("ok"), reset_out)

		out = get_pp_create_package_modal_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
		)
		self.assertFalse(out.get("create_allowed"), out)
		self.assertEqual(out.get("blocker_code"), PackageFromInclusion.INCLUSION_REQUIRED)

	def test_blocks_when_active_plan_missing(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.db.set_value(
			"Procurement Plan",
			PLAN_CODE,
			{"status": "Draft", "is_active": 0},
			update_modified=True,
		)
		frappe.db.commit()
		try:
			out = get_pp_create_package_modal_drawer(
				demand_code=DEMAND_CODE,
				plan_code=PLAN_CODE,
				inclusion_code=self.inclusion_code,
			)
			self.assertFalse(out.get("create_allowed"), out)
			self.assertEqual(out.get("blocker_code"), PackageFromInclusion.ACTIVE_PLAN_REQUIRED)
		finally:
			frappe.db.set_value(
				"Procurement Plan",
				PLAN_CODE,
				{"status": PLAN_ACTIVE, "is_active": 1},
				update_modified=True,
			)
			frappe.db.commit()

	def test_blocks_when_funding_missing(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_name = resolve_demand_name(DEMAND_CODE)
		original_budget = frappe.db.get_value("Demand", demand_name, "budget_line")
		frappe.db.set_value("Demand", demand_name, "budget_line", "", update_modified=False)
		frappe.db.commit()
		try:
			out = get_pp_create_package_modal_drawer(
				demand_code=DEMAND_CODE,
				plan_code=PLAN_CODE,
				inclusion_code=self.inclusion_code,
			)
			self.assertFalse(out.get("create_allowed"), out)
			self.assertEqual(out.get("blocker_code"), PackageFromInclusion.FUNDING_REQUIRED)
		finally:
			frappe.db.set_value(
				"Demand",
				demand_name,
				"budget_line",
				original_budget,
				update_modified=False,
			)
			frappe.db.commit()

	def test_duplicate_package_returns_existing_package_name(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		create_out = create_pp_package_from_planning_inclusion(inclusion_code=self.inclusion_code)
		self.assertTrue(create_out.get("ok"), create_out)
		package_name = str((create_out.get("package") or {}).get("package_name") or "").strip()
		self.assertTrue(package_name, create_out)

		out = get_pp_create_package_modal_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
			inclusion_code=self.inclusion_code,
		)
		self.assertFalse(out.get("create_allowed"), out)
		self.assertTrue(out.get("duplicate_package"), out)
		self.assertEqual(out.get("blocker_code"), PackageFromInclusion.PACKAGE_ALREADY_EXISTS)
		self.assertEqual(out.get("existing_package_name"), package_name)
