# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW2 — Package Creation Wizard Step 1 backend: eligible-demands list and
multi-select compatibility check (`Planning Package Creation Wizard.md`
§5/§8.2-§8.4).

Covers:
- `list_wizard_eligible_demands` returns demand-card fields (ref,
  department, category, funding label, strategy label, needed-by,
  documents count, status label) for demands "Added to Active Plan" with
  no package yet, and supports search filtering.
- `check_package_compatibility` passes for a single selection, passes for
  two compatible demands (same entity/fiscal year/category/method,
  confirmed funding), and flags a reason when categories differ.
- The whitelisted API wrappers in `package_wizard.py` return the same
  shape behind the create-package permission gate.
"""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
	include_demand_in_procurement_plan,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan")) and bool(demand_consumers_live())


class TestPW2WizardEligibilityCompatibility(IntegrationTestCase):
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
		dept = ensure_department(f"Dept PW2 {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"PW2 plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PW2-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "status", PLAN_ACTIVE, update_modified=False)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(self, bl_name: str, entity: str, dept: str, *, title: str, requisition_type: str = "Goods"):
		did = f"DEM-PW2-{frappe.generate_hash()[:8]}"
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": title,
				"demand_id": did,
				"procuring_entity": entity,
				"requesting_department": dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": requisition_type,
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

	def _mk_journey(self, demand_id: str) -> str:
		jc = f"JRN-PW2-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"PW2 test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _include_demand(self, demand, plan_name: str) -> dict:
		item_codes = [f"DEMITEM-PW2-{frappe.generate_hash()[:8]}"]
		out = include_demand_in_procurement_plan(demand.demand_id, item_codes, plan_name, "Administrator")
		inclusion_code = out.get("inclusion_code")
		if inclusion_code:
			self._track("Procurement Handoff Card", inclusion_code)
		return out

	def _mk_included_demand(self, plan_name: str, *, title: str, requisition_type: str = "Goods"):
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available")
		demand = self._mk_demand(bl_name, entity, dept, title=title, requisition_type=requisition_type)
		self._mk_journey(demand.demand_id)
		frappe.db.commit()
		out = self._include_demand(demand, plan_name)
		inclusion = get_planning_inclusion(out["inclusion_code"])
		return demand, inclusion

	def test_eligible_demands_list_has_demand_card_fields(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			list_wizard_eligible_demands,
		)

		plan_name = self._mk_plan()
		demand, inclusion = self._mk_included_demand(plan_name, title="PW2 Eligible Demand")

		rows = list_wizard_eligible_demands(plan_name)
		match = next((r for r in rows if r["inclusion_code"] == inclusion["inclusion_code"]), None)
		self.assertIsNotNone(match)
		self.assertEqual(match["ref"], demand.demand_id)
		self.assertTrue(match["department"])
		self.assertEqual(match["category"], "Goods")
		self.assertEqual(match["funding_label"], "Reserved")
		self.assertEqual(match["needed_by"], str(demand.required_by_date))
		self.assertEqual(match["documents_count"], 0)
		self.assertEqual(match["status_label"], "Added to Active Plan")
		self.assertNotIn("demand_id", match)
		self.assertNotIn("name", match)

	def test_eligible_demands_list_search_filters_by_department_and_category(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			list_wizard_eligible_demands,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW2 Searchable Demand")

		hit = list_wizard_eligible_demands(plan_name, search="goods")
		self.assertTrue(any(r["inclusion_code"] == inclusion["inclusion_code"] for r in hit))

		miss = list_wizard_eligible_demands(plan_name, search="no-such-needle-zzz")
		self.assertFalse(any(r["inclusion_code"] == inclusion["inclusion_code"] for r in miss))

	def test_compatibility_single_selection_always_compatible(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			check_package_compatibility,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW2 Solo Demand")

		out = check_package_compatibility([inclusion["inclusion_code"]])
		self.assertTrue(out["compatible"])
		self.assertEqual(out["reasons"], [])

	def test_compatibility_two_matching_demands_are_compatible(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			check_package_compatibility,
		)

		plan_name = self._mk_plan()
		_demand_a, inclusion_a = self._mk_included_demand(plan_name, title="PW2 Match A", requisition_type="Goods")
		_demand_b, inclusion_b = self._mk_included_demand(plan_name, title="PW2 Match B", requisition_type="Goods")

		out = check_package_compatibility([inclusion_a["inclusion_code"], inclusion_b["inclusion_code"]])
		self.assertTrue(out["compatible"], out["reasons"])
		self.assertEqual(out["reasons"], [])
		self.assertEqual(len(out["demands"]), 2)

	def test_compatibility_flags_category_mismatch(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			check_package_compatibility,
		)

		plan_name = self._mk_plan()
		_demand_a, inclusion_a = self._mk_included_demand(plan_name, title="PW2 Goods Demand", requisition_type="Goods")
		_demand_b, inclusion_b = self._mk_included_demand(plan_name, title="PW2 Works Demand", requisition_type="Works")

		out = check_package_compatibility([inclusion_a["inclusion_code"], inclusion_b["inclusion_code"]])
		self.assertFalse(out["compatible"])
		self.assertTrue(out["reasons"])

	def test_api_wrapper_returns_eligible_demands_behind_permission_gate(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.api.package_wizard import (
			list_pp_wizard_eligible_demands,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW2 API Demand")

		out = list_pp_wizard_eligible_demands(plan_code=plan_name)
		self.assertTrue(out.get("ok"))
		self.assertTrue(any(r["inclusion_code"] == inclusion["inclusion_code"] for r in out["demands"]))

	def test_api_wrapper_compatibility_accepts_json_list_string(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		import json

		from kentender_procurement.procurement_planning.api.package_wizard import (
			check_pp_package_compatibility,
		)

		plan_name = self._mk_plan()
		_demand_a, inclusion_a = self._mk_included_demand(plan_name, title="PW2 API Match A")
		_demand_b, inclusion_b = self._mk_included_demand(plan_name, title="PW2 API Match B")

		codes = json.dumps([inclusion_a["inclusion_code"], inclusion_b["inclusion_code"]])
		out = check_pp_package_compatibility(inclusion_codes=codes)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("compatible"), out.get("reasons"))
