# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-003 — Selected plan summary source contract and API."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.procurement_planning.api.procurement_plans import (
	get_pp_procurement_plan_summary,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.services.procurement_plans_view_model import (
	get_procurement_plan_summary_view_model,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP4PlanSummaryP4003Source(UnitTestCase):
	def test_plan_summary_component_exposes_required_testids(self) -> None:
		path = _pkg_public("js", "pp3_planning_plan_summary.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="pp3-plan-summary"', source)
		self.assertIn('data-testid="pp3-plan-summary-status"', source)
		self.assertIn('data-testid="pp3-plan-summary-blockers"', source)
		self.assertIn("get_pp_procurement_plan_summary", source)

	def test_router_wires_plan_summary_on_procurement_plans_surface(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountProcurementPlansSurface", 1)[1].split(
			"function mountPlanningQueueTabs", 1
		)[0]
		self.assertIn("PlanningPlanSummary", fn_block)


class TestPP4PlanSummaryP4003API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[str] = []
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for name in reversed(self._cleanup):
			if frappe.db.exists("Procurement Plan", name):
				frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _mk_plan(self) -> str:
		code = f"PLAN-P4003-{frappe.generate_hash()[:6].upper()}"
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "Ministry of Health Procurement Plan",
				"plan_code": code,
				"fiscal_year": 2026,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_ACTIVE,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		self._cleanup.append(plan.name)
		return plan.name

	def test_summary_returns_active_state_demands_packages_released_blockers(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		plan_code = self._mk_plan()
		frappe.db.commit()
		out = get_procurement_plan_summary_view_model(plan_id=plan_code, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		self.assertEqual(out.get("status_label"), "Active")
		self.assertEqual(out.get("fiscal_year"), "2026/2027")
		self.assertIn("demands_count", out)
		self.assertIn("packages_count", out)
		self.assertIn("released_count", out)
		self.assertEqual(out.get("blockers_label"), "None")

	def test_missing_plan_returns_error(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp_procurement_plan_summary(plan_id="PLAN-DOES-NOT-EXIST")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PLAN_NOT_FOUND")
