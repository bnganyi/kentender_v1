# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Regression — include materializes missing procurement journey for approved demands."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_lifecycle.demand_journey_bootstrap import (
	ensure_procurement_journey_for_demand_code,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)


class TestDemandJourneyBootstrapInclude(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan") or not frappe.db.exists("DocType", "Demand"):
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

	def _seed_budget_line(self) -> tuple[str | None, str | None, str | None]:
		bl_name = frappe.db.get_value("Budget Line", {"is_active": 1}, "name", order_by="modified desc")
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept JRN {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"JRN plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-JRN-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": "MOH",
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "status", PLAN_ACTIVE, update_modified=False)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(self, bl_name: str, entity: str, dept: str) -> frappe.model.document.Document:
		did = f"DEM-JRN-{frappe.generate_hash()[:8]}"
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Journey bootstrap {frappe.generate_hash(length=4)}",
				"demand_id": did,
				"procuring_entity": entity,
				"requesting_department": dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": "Goods",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"specification_summary": "Scope",
				"budget_line": bl_name,
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
		frappe.db.set_value("Demand", doc.name, "status", "Approved", update_modified=False)
		doc.reload()
		self._track("Demand", doc.name)
		return doc

	def test_include_materializes_missing_journey(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available")
		plan_name = self._mk_plan()
		demand = self._mk_demand(bl_name, entity, dept)
		frappe.db.commit()

		self.assertFalse(
			frappe.db.get_value("Procurement Journey", {"demand_ref": demand.demand_id}, "name")
		)

		out = include_demand_in_procurement_plan(
			demand.demand_id,
			[],
			plan_name,
			"Administrator",
		)
		self.assertTrue(out.get("ok"), out)
		journey_code = frappe.db.get_value(
			"Procurement Journey",
			{"demand_ref": demand.demand_id},
			"journey_code",
		)
		self.assertTrue(journey_code)
		self._track("Procurement Journey", journey_code)
		if out.get("inclusion_code"):
			self._track("Procurement Handoff Card", out["inclusion_code"])

	def test_ensure_returns_existing_journey(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available")
		demand = self._mk_demand(bl_name, entity, dept)
		frappe.db.commit()

		first = ensure_procurement_journey_for_demand_code(demand.demand_id)
		second = ensure_procurement_journey_for_demand_code(demand.demand_id)
		self.assertTrue(first)
		self.assertEqual(first, second)
		self._track("Procurement Journey", first)
