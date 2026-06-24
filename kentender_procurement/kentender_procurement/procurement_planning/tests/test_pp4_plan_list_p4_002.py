# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-002 — Procurement Plans list source contract and API."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.procurement_planning.api.procurement_plans import (
	get_pp_procurement_plans_list,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.procurement_plans_view_model import (
	get_procurement_plans_list_view_model,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP4PlanListP4002Source(UnitTestCase):
	def test_plan_list_component_exposes_required_testids(self) -> None:
		path = _pkg_public("js", "pp3_planning_plan_list.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="pp3-plan-list"', source)
		self.assertIn('data-testid="pp3-plan-row"', source)
		self.assertIn("get_pp_procurement_plans_list", source)

	def test_router_mounts_plan_list_on_procurement_plans_surface(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountProcurementPlansSurface", 1)[1].split(
			"function mountPlanningQueueTabs", 1
		)[0]
		self.assertIn("PlanningPlanList", fn_block)
		self.assertNotIn("renderSurfaceEmptyState(bodyHost, slug)", fn_block)


class TestPP4PlanListP4002API(IntegrationTestCase):
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

	def _mk_plan(
		self,
		*,
		status: str = PLAN_ACTIVE,
		plan_name: str = "Ministry of Health Procurement Plan",
		fiscal_year: int = 2026,
	) -> str:
		code = f"PLAN-P4002-{frappe.generate_hash()[:6].upper()}"
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": plan_name,
				"plan_code": code,
				"fiscal_year": fiscal_year,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": status,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		self._cleanup.append(plan.name)
		return plan.name

	def test_guest_denied_api(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_procurement_plans_list()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_list_returns_title_fiscal_year_status_and_counts(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		plan_code = self._mk_plan(status=PLAN_ACTIVE)
		frappe.db.commit()

		out = get_procurement_plans_list_view_model(actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		rows = out.get("plans") or []
		match = next((row for row in rows if row.get("plan_code") == plan_code), None)
		self.assertIsNotNone(match, msg=f"expected plan {plan_code} in {rows!r}")
		assert match is not None
		self.assertEqual(match.get("title"), "Ministry of Health Procurement Plan")
		self.assertEqual(match.get("fiscal_year"), "2026/2027")
		self.assertEqual(match.get("status_label"), "Active")
		self.assertIn("demands_count", match)
		self.assertIn("packages_count", match)
		self.assertIn("released_count", match)
		self.assertIn("demand", (match.get("counts_label") or "").lower())
		self.assertIn("package", (match.get("counts_label") or "").lower())
		self.assertIn("released", (match.get("counts_label") or "").lower())

	def test_draft_plan_status_label(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		plan_code = self._mk_plan(status=PLAN_DRAFT, plan_name="Draft FY Plan")
		frappe.db.commit()
		out = get_procurement_plans_list_view_model(actor="Administrator")
		match = next((row for row in out.get("plans") or [] if row.get("plan_code") == plan_code), None)
		self.assertIsNotNone(match)
		assert match is not None
		self.assertEqual(match.get("status_label"), "Draft")
