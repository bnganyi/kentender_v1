# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-001 — WORKS demand appears in Workbench Needs Planning (golden path)."""

from __future__ import annotations

from datetime import date

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_core.seeds import constants as C
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import DEMAND_TITLE
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.api.workbench_item import (
	get_pp_workbench_item_view_model,
)
from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.prep import (
	ensure_works_demand_queue_ready,
)
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	get_active_plan_view_model,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
)
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	get_workbench_item_view_model,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


def _find_works_item(items: list[dict]) -> dict | None:
	for item in items or []:
		if str(item.get("underlying_object_code") or "").strip() == DEMAND_CODE:
			return item
	return None


def _find_demand_row(rows: list[dict]) -> dict | None:
	for row in rows or []:
		demand = row.get("demand") or {}
		if str(demand.get("code") or "").strip() == DEMAND_CODE:
			return row
	return None


class TestPP5SelectWorksDemandP5001(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not _pp_ok() or not demand_consumers_live():
			cls._skip = True
			return
		cls._skip = False

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		self._cleanup: list[str] = []
		out = ensure_pp5_needs_planning_ready(force_reset=True)
		self.assertTrue(out.get("ok"), out)

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		for name in reversed(getattr(self, "_cleanup", [])):
			if frappe.db.exists("Procurement Plan", name):
				frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		self._cleanup = []
		frappe.db.commit()

	def test_001_works_demand_in_needs_planning_workbench_queue(self):
		"""PP5-001-BE-001: WORKS demand appears in Workbench Needs Planning queue."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_workbench_item_view_model(
			queue="needs_planning",
			actor="Administrator",
			limit=200,
			start=0,
		)
		self.assertTrue(out.get("ok"), out)
		item = _find_works_item(out.get("items") or [])
		self.assertIsNotNone(item, out)
		assert item is not None

		self.assertEqual(item.get("title"), DEMAND_TITLE)
		self.assertEqual(item.get("underlying_object_type"), "approved_demand")
		self.assertEqual(item.get("queue"), "needs_planning")
		self.assertEqual(item.get("next_action_label"), "Add to Active Plan")
		self.assertEqual((item.get("primary_action") or {}).get("action"), "include_in_plan")
		self.assertTrue(item.get("technical_hidden_by_default"))

	def test_002_api_matches_service_for_needs_planning(self):
		"""PP5-001-BE-002: Whitelisted API matches service output."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		service_out = get_workbench_item_view_model(
			queue="needs_planning",
			actor="Administrator",
			limit=200,
			start=0,
		)
		api_out = get_pp_workbench_item_view_model(queue="needs_planning", limit=200, start=0)
		self.assertEqual(service_out, api_out)

	def test_003_active_plan_present_for_workbench(self):
		"""PP5-001-BE-003: Active plan is available for Workbench context."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_active_plan_view_model(actor="Administrator")
		self.assertTrue(out.get("has_active_plan"), out)
		self.assertEqual(out.get("plan_code"), PLAN_CODE)

	def test_004_approved_demand_queue_regression_pp2_smoke_be_002(self):
		"""PP5-001-BE-004: PP2-SMOKE-BE-002 — WORKS demand in approved demand queue."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_approved_demands_awaiting_planning({"search_text": DEMAND_CODE}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		row = _find_demand_row(out.get("rows") or [])
		self.assertIsNotNone(row, out)
		assert row is not None
		demand = row.get("demand") or {}
		self.assertEqual(demand.get("code"), DEMAND_CODE)
		self.assertEqual(demand.get("name"), DEMAND_TITLE)

	def test_005_default_active_plan_uses_current_fy_not_newer_other_fy(self):
		"""PP5-001-BE-005: Workbench active plan defaults to current FY, not globally newest."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		other_fy = date.today().year + 5
		other = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"P5-001 other FY {frappe.generate_hash(length=4)}",
				"plan_code": f"PLAN-P5001-{frappe.generate_hash()[:6].upper()}",
				"fiscal_year": other_fy,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_ACTIVE,
				"is_active": 1,
				"is_master_seed": 0,
			}
		)
		other.insert(ignore_permissions=True)
		self._cleanup.append(other.name)
		frappe.db.set_value(
			"Procurement Plan",
			other.name,
			"modified",
			now_datetime(),
			update_modified=False,
		)
		frappe.db.commit()

		out = get_active_plan_view_model(actor="Administrator")
		self.assertTrue(out.get("has_active_plan"), out)
		self.assertEqual(out.get("plan_code"), PLAN_CODE)
		self.assertEqual(out.get("fiscal_year"), f"{date.today().year}/{date.today().year + 1}")

	def test_006_queue_prep_restores_active_master_plan(self):
		"""PP5-001-BE-006: Queue prep must not leave Workbench without PLAN-MOH-2026."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		ensure_works_demand_queue_ready()
		out = get_active_plan_view_model(actor="planner@moh.test")
		self.assertTrue(out.get("has_active_plan"), out)
		self.assertEqual(out.get("plan_code"), PLAN_CODE)
