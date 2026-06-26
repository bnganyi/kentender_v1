# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-002 — Include/Create Package unavailable without active plan."""

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
from kentender_procurement.procurement_planning.pp2_constants import PLAN_DRAFT
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	get_active_plan_view_model,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	DemandInclusion,
)


def _router_path() -> Path:
	return Path(frappe.get_app_path("kentender_procurement")) / "public" / "js" / "pp2_planning_router.js"


class TestPP8NoActivePlanP8002Contract(UnitTestCase):
	def test_pp8_002_router_gates_workbench_on_has_active_plan(self) -> None:
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		self.assertIn("pp3-planning-work-unavailable", source)
		self.assertIn("has_active_plan", source)
		self.assertIn("mountPlanningWorkUnavailable", source)


class TestPP8NoActivePlanP8002API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self._skip = True
			return
		self._skip = False
		self._original_status = frappe.db.get_value("Procurement Plan", PLAN_CODE, "status")

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		if self._original_status and frappe.db.exists("Procurement Plan", PLAN_CODE):
			frappe.db.set_value(
				"Procurement Plan",
				PLAN_CODE,
				"status",
				self._original_status,
				update_modified=False,
			)
			frappe.db.commit()

	def test_pp8_002_include_blocked_when_plan_not_active(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.db.set_value("Procurement Plan", PLAN_CODE, "status", PLAN_DRAFT, update_modified=False)
		frappe.db.commit()
		out = include_pp_demand_in_procurement_plan(
			demand_code=DEMAND_CODE,
			procurement_plan_code=PLAN_CODE,
			demand_item_codes=f'["{DEMAND_ITEM_CODE}"]',
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), DemandInclusion.PLAN_INACTIVE)

	def test_pp8_002_active_plan_view_model_reports_no_active_when_draft_only(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.db.set_value("Procurement Plan", PLAN_CODE, "status", PLAN_DRAFT, update_modified=False)
		frappe.db.commit()
		out = get_active_plan_view_model(actor="planner@moh.test")
		self.assertTrue(out.get("ok"), out)
		self.assertFalse(out.get("has_active_plan"))

	def test_pp8_002_create_package_modal_blocked_without_inclusion(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		out = get_pp_create_package_modal_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
			inclusion_code="",
		)
		if out.get("ok"):
			self.assertFalse(out.get("create_allowed"), out)
			self.assertTrue(out.get("blocker_code") or out.get("blocker_message"), out)
		else:
			self.assertFalse(out.get("ok"))
			self.assertTrue(str(out.get("error_code") or out.get("message") or "").strip())
