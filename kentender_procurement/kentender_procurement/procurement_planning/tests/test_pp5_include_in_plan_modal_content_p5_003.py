# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-003 — Include in Plan modal shows demand, value, funding, active plan; no technical IDs."""

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
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.services.approved_demand_drawer import (
	get_approved_demand_planning_drawer,
)

_FORBIDDEN_MODAL_COPY = (
	"PLANINCL-",
	"source_object_code",
	"target_object_code",
	"technical_refs_json",
	"locked_summary_json",
	"passed_forward_summary_json",
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP5IncludeInPlanModalContentP5003Contract(UnitTestCase):
	def test_include_plan_modal_renders_active_plan_context(self) -> None:
		path = _pkg_public("js", "pp2_planning_include_plan_modal.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("pp2-include-plan-active-plan", source)
		self.assertIn("target_plan_name", source)
		self.assertIn("target_plan_locked", source)
		self.assertIn('__("Active plan")', source)
		context_block = source.split("function businessContextHtml", 1)[1].split("function ", 1)[0]
		for token in _FORBIDDEN_MODAL_COPY:
			self.assertNotIn(token, context_block)

	def test_include_plan_modal_active_plan_label_in_context_html(self) -> None:
		path = _pkg_public("js", "pp2_planning_include_plan_modal.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		context_block = source.split("function businessContextHtml", 1)[1].split("function ", 1)[0]
		self.assertIn("pp2-include-plan-demand", context_block)
		self.assertIn("pp2-include-plan-value", context_block)
		self.assertIn("pp2-include-plan-funding", context_block)
		self.assertIn("pp2-include-plan-active-plan", context_block)
		self.assertIn("o.demand_name", context_block)

	def test_router_passes_target_plan_name_and_locked_flag(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		summary_block = source.split("function approvedDemandSummaryFromDrawer", 1)[1].split(
			"function openIncludePlanModalForShell", 1
		)[0]
		self.assertIn("target_plan_name", summary_block)
		open_block = source.split("function openIncludePlanModalForShell", 1)[1].split(
			"function requestIncludePlanModalForShell", 1
		)[0]
		self.assertIn("target_plan_name", open_block)
		self.assertIn("target_plan_locked", open_block)
		workbench_block = source.split("function openWorkbenchIncludePlanModal", 1)[1].split(
			"function renderApprovedDemandSummary", 1
		)[0]
		self.assertIn("target_plan_locked: true", workbench_block)


class TestPP5IncludeInPlanModalContentP5003Drawer(IntegrationTestCase):
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

	def test_drawer_business_fields_for_include_modal(self) -> None:
		"""PP5-003-BE-001: golden-path drawer exposes modal business labels."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_approved_demand_planning_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"), out)

		demand = out.get("demand") or {}
		self.assertEqual(demand.get("code"), DEMAND_CODE)
		self.assertIn("District Hospital Renovation Works", demand.get("name") or "")
		self.assertGreater(float(demand.get("estimated_value") or 0), 0)
		self.assertEqual((demand.get("currency") or "").strip(), "KES")

		budget_line = ((out.get("budget_context") or {}).get("budget_line") or {})
		self.assertTrue(str(budget_line.get("code") or budget_line.get("id") or "").strip())

		target_plan = out.get("target_plan") or {}
		self.assertEqual(target_plan.get("code"), PLAN_CODE)
		self.assertEqual(target_plan.get("name"), PLAN_NAME)
