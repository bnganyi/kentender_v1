# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-002 — can_include_demand_in_plan guard and PP2 blocker codes."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_CLOSED, PLAN_DRAFT, PKG_DRAFT
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	can_include_demand_in_plan,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import DemandInclusion


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2DemandInclusionGuardP2002(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok() or not frappe.db.exists("DocType", "Demand"):
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(getattr(self, "_cleanup", [])):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _track(self, doctype: str, name: str) -> None:
		self._cleanup.append((doctype, name))

	def _seed_budget_line(self) -> tuple[str | None, str | None, str | None]:
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl_name:
			bl_name = frappe.db.get_value(
				"Budget Line",
				{"procuring_entity": C.ENTITY_MOH, "is_active": 1},
				"name",
				order_by="modified desc",
			)
		if not bl_name:
			bl_name = frappe.db.get_value(
				"Budget Line",
				{"is_active": 1},
				"name",
				order_by="modified desc",
			)
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept Guard {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Guard plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-GUARD-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		if status != PLAN_DRAFT:
			frappe.db.set_value("Procurement Plan", plan.name, "status", status, update_modified=False)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(
		self,
		bl_name: str,
		entity: str,
		dept: str,
		*,
		status: str = "Approved",
		budget_line: str | None = None,
		demand_id: str | None = None,
	) -> frappe.model.document.Document:
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Guard demand {frappe.generate_hash(length=4)}",
				"demand_id": demand_id or f"DEM-GUARD-{frappe.generate_hash()[:8]}",
				"procuring_entity": entity,
				"requesting_department": dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": "Goods",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"specification_summary": "Scope",
				"budget_line": budget_line if budget_line is not None else bl_name,
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 100,
					}
				],
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Demand", doc.name, "status", status, update_modified=False)
		doc.reload()
		self._track("Demand", doc.name)
		return doc

	def _mk_package(self, plan_name: str) -> str:
		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			raise RuntimeError("no template")
		dcp = frappe.get_all("Decision Criteria Profile", limit=1, pluck="name")
		pkg = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_name": f"Guard pkg {frappe.generate_hash(length=4)}",
				"plan_id": plan_name,
				"template_id": tpl[0],
				"procurement_method": "Direct Procurement",
				"contract_type": "Fixed Price",
				"currency": "KES",
				"risk_profile_id": frappe.get_all("Risk Profile", limit=1, pluck="name")[0],
				"kpi_profile_id": frappe.get_all("KPI Profile", limit=1, pluck="name")[0],
				"vendor_management_profile_id": frappe.get_all("Vendor Management Profile", limit=1, pluck="name")[
					0
				],
				"decision_criteria_profile_id": dcp[0] if dcp else None,
				"status": PKG_DRAFT,
				"is_active": 1,
			}
		)
		pkg.insert(ignore_permissions=True)
		self._track("Procurement Package", pkg.name)
		return pkg.name

	def _mk_package_line(
		self,
		pkg_name: str,
		demand_name: str,
		budget_line: str,
		*,
		demand_item_code: str | None = None,
	) -> str:
		line = frappe.get_doc(
			{
				"doctype": "Procurement Package Line",
				"package_id": pkg_name,
				"demand_id": demand_name,
				"budget_line_id": budget_line,
				"demand_item_code": demand_item_code,
				"amount": 100,
				"quantity": 1.0,
				"line_status": "Draft",
				"is_active": 1,
			}
		)
		line.insert(ignore_permissions=True)
		self._track("Procurement Package Line", line.name)
		return line.name

	def test_blocker_codes_are_stable(self) -> None:
		self.assertEqual(DemandInclusion.DEMAND_NOT_APPROVED, "PP2-BLOCK-DEMAND-NOT-APPROVED")
		self.assertEqual(DemandInclusion.BUDGET_MISSING, "PP2-BLOCK-BUDGET-MISSING")
		self.assertEqual(
			DemandInclusion.DEMAND_ITEM_ALREADY_PACKAGED,
			"PP2-BLOCK-DEMAND-ITEM-ALREADY-PACKAGED",
		)
		self.assertEqual(DemandInclusion.PLAN_INACTIVE, "PP2-BLOCK-PLAN-INACTIVE")

	def test_allowed_when_preconditions_met(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for guard tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		frappe.db.commit()
		out = can_include_demand_in_plan(
			demand.demand_id,
			["DEMITEM-TEST-001"],
			plan_name,
			"Administrator",
		)
		self.assertTrue(out["allowed"])
		self.assertEqual(out["blockers"], [])
		self.assertTrue(all(c["ok"] for c in out["checks"]))

	def test_blocks_unapproved_demand(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for guard tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept, status="Draft")
		frappe.db.commit()
		out = can_include_demand_in_plan(demand.demand_id, [], plan_name, "Administrator")
		self.assertFalse(out["allowed"])
		codes = [b["code"] for b in out["blockers"]]
		self.assertIn(DemandInclusion.DEMAND_NOT_APPROVED, codes)

	def test_blocks_missing_budget(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for guard tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept, budget_line="")
		frappe.db.commit()
		out = can_include_demand_in_plan(demand.demand_id, [], plan_name, "Administrator")
		self.assertFalse(out["allowed"])
		codes = [b["code"] for b in out["blockers"]]
		self.assertIn(DemandInclusion.BUDGET_MISSING, codes)

	def test_blocks_already_packaged_demand_item(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for guard tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		pkg_name = self._mk_package(plan_name)
		item_code = "DEMITEM-TEST-001"
		self._mk_package_line(pkg_name, demand.name, bl_name, demand_item_code=item_code)
		frappe.db.commit()
		out = can_include_demand_in_plan(demand.demand_id, [item_code], plan_name, "Administrator")
		self.assertFalse(out["allowed"])
		codes = [b["code"] for b in out["blockers"]]
		self.assertIn(DemandInclusion.DEMAND_ITEM_ALREADY_PACKAGED, codes)

	def test_blocks_inactive_plan(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for guard tests")
		for plan_status in (PLAN_DRAFT, PLAN_CLOSED):
			plan_name = self._mk_plan(status=plan_status)
			demand = self._mk_demand(bl_name, entity, dept)
			frappe.db.commit()
			out = can_include_demand_in_plan(demand.demand_id, [], plan_name, "Administrator")
			self.assertFalse(out["allowed"], msg=f"expected block for plan status {plan_status}")
			codes = [b["code"] for b in out["blockers"]]
			self.assertIn(DemandInclusion.PLAN_INACTIVE, codes)
