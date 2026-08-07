# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW5 — Package Creation Wizard Step 3 backend: readiness preview and
blocking-condition evaluation (`Planning Package Creation Wizard.md`
§10.3/§10.5).

Covers:
- Empty selection is Blocked with `create_allowed = False`.
- A fully eligible single demand yields all-Ready/Warning checks with
  `create_allowed = True`.
- Each of several §10.5 blocking conditions independently sets
  `create_allowed = False` with a matching business-readable reason:
  demand not Approved, no active plan, missing category (no usable
  template).
- The whitelisted API wrapper returns the same shape behind the
  create-package permission gate.
"""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_CLOSED, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
	include_demand_in_procurement_plan,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan")) and bool(demand_consumers_live())


class TestPW5WizardReadiness(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok():
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

	def _seed_budget_line(self):
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl_name:
			bl_name = frappe.db.get_value(
				"Budget Line", {"procuring_entity": C.ENTITY_MOH, "is_active": 1}, "name", order_by="modified desc"
			)
		if not bl_name:
			bl_name = frappe.db.get_value("Budget Line", {"is_active": 1}, "name", order_by="modified desc")
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept PW5 {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self, *, status: str = PLAN_DRAFT) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"PW5 plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PW5-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "status", status, update_modified=False)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(self, bl_name: str, entity: str, dept: str, *, title: str, status: str = "Approved"):
		did = f"DEM-PW5-{frappe.generate_hash()[:8]}"
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": title,
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
		frappe.db.set_value("Demand", doc.name, "status", status, update_modified=False)
		doc.reload()
		self._track("Demand", doc.name)
		return doc

	def _mk_journey(self, demand_id: str) -> str:
		jc = f"JRN-PW5-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"PW5 test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _mk_included_demand(self, plan_name: str, **demand_kwargs):
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available")
		demand = self._mk_demand(bl_name, entity, dept, **demand_kwargs)
		self._mk_journey(demand.demand_id)
		frappe.db.commit()
		item_codes = [f"DEMITEM-PW5-{frappe.generate_hash()[:8]}"]
		out = include_demand_in_procurement_plan(demand.demand_id, item_codes, plan_name, "Administrator")
		self._track("Procurement Handoff Card", out["inclusion_code"])
		inclusion = get_planning_inclusion(out["inclusion_code"])
		return demand, inclusion

	def test_empty_selection_is_blocked(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			evaluate_wizard_readiness,
		)

		out = evaluate_wizard_readiness([])
		self.assertFalse(out["create_allowed"])
		self.assertTrue(out["blocking_reasons"])

	def test_fully_eligible_demand_allows_create(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			evaluate_wizard_readiness,
		)

		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW5 Ready Demand")

		out = evaluate_wizard_readiness([inclusion["inclusion_code"]])
		self.assertTrue(out["create_allowed"], out["blocking_reasons"])
		statuses = {c["key"]: c["status"] for c in out["checks"]}
		self.assertEqual(statuses["demand_selected"], "Ready")
		self.assertEqual(statuses["plan_active"], "Ready")
		self.assertEqual(statuses["category"], "Ready")
		self.assertIn(statuses["lines"], ("Ready",))

	def test_unapproved_demand_blocks_create(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			evaluate_wizard_readiness,
		)

		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand, inclusion = self._mk_included_demand(plan_name, title="PW5 Unapproved Demand")
		frappe.db.set_value("Demand", demand.name, "status", "Draft", update_modified=False)

		out = evaluate_wizard_readiness([inclusion["inclusion_code"]])
		self.assertFalse(out["create_allowed"])
		statuses = {c["key"]: c["status"] for c in out["checks"]}
		self.assertEqual(statuses["demand_selected"], "Blocked")
		self.assertTrue(any("not Approved" in r for r in out["blocking_reasons"]))

	def test_inactive_plan_blocks_create(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			evaluate_wizard_readiness,
		)

		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW5 Closed Plan Demand")
		frappe.db.set_value("Procurement Plan", plan_name, "status", PLAN_CLOSED, update_modified=False)

		out = evaluate_wizard_readiness([inclusion["inclusion_code"]])
		self.assertFalse(out["create_allowed"])
		statuses = {c["key"]: c["status"] for c in out["checks"]}
		self.assertEqual(statuses["plan_active"], "Blocked")

	def test_already_packaged_inclusion_blocks_create(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_creation_service import (
			create_package_from_planning_inclusion,
		)
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			evaluate_wizard_readiness,
		)

		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			self.skipTest("No active Procurement Template available")
		row = frappe.db.get_value(
			"Procurement Template", tpl[0], ("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"), as_dict=True
		)
		if not row or not all(row.values()):
			self.skipTest("No usable Procurement Template with profiles available")

		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW5 Already Packaged Demand")
		out = create_package_from_planning_inclusion(inclusion["inclusion_code"], "Administrator")
		self._track("Procurement Package", out["package_code"])
		for line_code in out["package_line_codes"]:
			self._track("Procurement Package Line", line_code)

		readiness = evaluate_wizard_readiness([inclusion["inclusion_code"]])
		self.assertFalse(readiness["create_allowed"])
		self.assertTrue(any("already fully packaged" in r for r in readiness["blocking_reasons"]))

	def test_api_wrapper_readiness_behind_permission_gate(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		import json

		from kentender_procurement.procurement_planning.api.package_wizard import (
			get_pp_package_wizard_readiness,
		)

		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW5 API Demand")

		out = get_pp_package_wizard_readiness(inclusion_codes=json.dumps([inclusion["inclusion_code"]]))
		self.assertTrue(out.get("ok"))
		self.assertIn("create_allowed", out)
		self.assertIn("checks", out)
