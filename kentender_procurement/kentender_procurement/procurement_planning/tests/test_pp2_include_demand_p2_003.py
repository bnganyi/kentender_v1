# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-003 — include_demand_in_procurement_plan write service."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import DemandInclusion


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2IncludeDemandP2003(IntegrationTestCase):
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
			if doctype == "Procurement Journey":
				frappe.db.sql("DELETE FROM `tabProcurement Journey` WHERE name=%s", name)
				continue
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _track(self, doctype: str, name: str) -> None:
		self._cleanup.append((doctype, name))

	def _seed_budget_line(self) -> tuple[str | None, str | None, str | None, str | None]:
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
			return None, None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept Incl {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Incl plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-INCL-{frappe.generate_hash()[:6]}",
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
		did = demand_id or f"DEM-INCL-{frappe.generate_hash()[:8]}"
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Incl demand {frappe.generate_hash(length=4)}",
				"demand_id": did,
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

	def _mk_journey(self, demand_id: str) -> str:
		jc = f"JRN-INCL-{frappe.generate_hash()[:8]}"
		now = now_datetime()
		frappe.db.sql(
			"""
			INSERT INTO `tabProcurement Journey`
			(name, creation, modified, modified_by, owner, docstatus,
			 journey_code, journey_title, demand_ref, procuring_entity_code,
			 procurement_category, procurement_method, fiscal_year,
			 current_stage_key, current_stage_label, current_status_category,
			 current_owner_module, blocker_count, critical_blocker_count, is_master_seed)
			VALUES (%s, %s, %s, 'Administrator', 'Administrator', 0,
			 %s, %s, %s, 'MOH', 'Goods', 'Open Tender', '2029',
			 'planning_inclusion', 'Planning Inclusion', 'In Progress',
			 'Procurement Planning', 0, 0, 0)
			""",
			(jc, now, now, jc, f"Inclusion test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _audit_count(self, handoff_code: str) -> int:
		return frappe.db.count(
			"Planning Audit Event",
			{
				"object_code": handoff_code,
				"event_type": "Demand Included in Plan",
			},
		)

	def test_creates_inclusion_on_success(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept, bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for include tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		item_codes = ["DEMITEM-INCL-001"]
		frappe.db.commit()

		out = include_demand_in_procurement_plan(
			demand.demand_id,
			item_codes,
			plan_name,
			"Administrator",
		)

		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("status"), "Included")
		self.assertEqual(out.get("demand_code"), demand.demand_id)
		self.assertEqual(out.get("procurement_plan_code"), plan_name)
		self.assertEqual(out.get("budget_line_code"), bl_code)
		self.assertEqual(out.get("demand_item_codes"), item_codes)
		inclusion_code = out.get("inclusion_code")
		self.assertTrue(inclusion_code)
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", inclusion_code))
		self._track("Procurement Handoff Card", inclusion_code)
		handoff = frappe.get_doc("Procurement Handoff Card", inclusion_code)
		self.assertEqual(handoff.status, "Handed Off")
		self.assertEqual(handoff.source_object_code, demand.demand_id)
		self.assertEqual(handoff.target_object_code, plan_name)

	def test_idempotent_second_call(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for include tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		item_codes = ["DEMITEM-INCL-002"]
		frappe.db.commit()

		first = include_demand_in_procurement_plan(
			demand.demand_id,
			item_codes,
			plan_name,
			"Administrator",
		)
		inclusion_code = first.get("inclusion_code")
		self.assertTrue(inclusion_code)
		self._track("Procurement Handoff Card", inclusion_code)

		count_after_first = frappe.db.count(
			"Procurement Handoff Card",
			{
				"handoff_title": "Planning Inclusion Record",
				"source_object_code": demand.demand_id,
				"target_object_code": plan_name,
			},
		)

		second = include_demand_in_procurement_plan(
			demand.demand_id,
			item_codes,
			plan_name,
			"Administrator",
		)

		self.assertEqual(second.get("action"), "existing")
		self.assertEqual(second.get("inclusion_code"), inclusion_code)
		count_after_second = frappe.db.count(
			"Procurement Handoff Card",
			{
				"handoff_title": "Planning Inclusion Record",
				"source_object_code": demand.demand_id,
				"target_object_code": plan_name,
			},
		)
		self.assertEqual(count_after_first, count_after_second)

	def test_blocked_when_guard_fails(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for include tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept, status="Draft")
		self._mk_journey(demand.demand_id)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			include_demand_in_procurement_plan(
				demand.demand_id,
				[],
				plan_name,
				"Administrator",
			)
		self.assertIn("not approved", str(ctx.exception).lower())

	def test_audit_event_on_create_only(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for include tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		frappe.db.commit()

		first = include_demand_in_procurement_plan(
			demand.demand_id,
			["DEMITEM-INCL-003"],
			plan_name,
			"Administrator",
		)
		inclusion_code = first.get("inclusion_code")
		self.assertTrue(inclusion_code)
		self._track("Procurement Handoff Card", inclusion_code)
		self.assertEqual(self._audit_count(inclusion_code), 1)

		include_demand_in_procurement_plan(
			demand.demand_id,
			["DEMITEM-INCL-003"],
			plan_name,
			"Administrator",
		)
		self.assertEqual(self._audit_count(inclusion_code), 1)
