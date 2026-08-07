# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW6 — Package Creation Wizard final commit: multi-demand/multi-line
create orchestration (`Planning Package Creation Wizard.md` §10.4/§12).

Covers:
- A blocked (not-ready) selection is rejected without creating anything.
- A single fully eligible demand creates a Draft package + line, applies
  Step 2 configuration overrides, and records the "Package Wizard
  Completed" evidence event on top of the primitive's own events.
- Two compatible demands create one package with two lines (multi-demand
  packaging).
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
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
	include_demand_in_procurement_plan,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan")) and bool(demand_consumers_live())


class TestPW6WizardCreateOrchestration(IntegrationTestCase):
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

	def _track_package_lines(self, package_line_codes: list[str]) -> None:
		for code in package_line_codes:
			name = frappe.db.get_value("Procurement Package Line", {"package_line_code": code}, "name")
			if name:
				self._track("Procurement Package Line", name)

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
		dept = ensure_department(f"Dept PW6 {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"PW6 plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PW6-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_ACTIVE,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "status", PLAN_ACTIVE, update_modified=False)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(self, bl_name: str, entity: str, dept: str, *, title: str, status: str = "Approved"):
		did = f"DEM-PW6-{frappe.generate_hash()[:8]}"
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
		jc = f"JRN-PW6-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"PW6 test journey {jc}", demand_id),
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
		item_codes = [f"DEMITEM-PW6-{frappe.generate_hash()[:8]}"]
		out = include_demand_in_procurement_plan(demand.demand_id, item_codes, plan_name, "Administrator")
		self._track("Procurement Handoff Card", out["inclusion_code"])
		inclusion = get_planning_inclusion(out["inclusion_code"])
		return demand, inclusion

	def _has_usable_template(self) -> bool:
		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			return False
		row = frappe.db.get_value(
			"Procurement Template", tpl[0], ("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"), as_dict=True
		)
		return bool(row and all(row.values()))

	def test_blocked_selection_creates_nothing(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			create_package_from_wizard,
		)

		out = create_package_from_wizard([])
		self.assertFalse(out["ok"])
		self.assertEqual(out["error_code"], "WIZARD_NOT_READY")
		self.assertTrue(out["blocking_reasons"])

	def test_single_demand_creates_package_with_overrides_and_evidence(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._has_usable_template():
			self.skipTest("No usable Procurement Template with profiles available")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			create_package_from_wizard,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW6 Single Demand")

		config = {
			"package_title": "PW6 Custom Package Title",
			"package_owner": "Administrator",
			"package_priority": "High",
			"line_overrides": {
				inclusion["inclusion_code"]: {"lot_group": "Lot A", "delivery_location": "Nairobi"},
			},
		}
		out = create_package_from_wizard([inclusion["inclusion_code"]], config, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self._track("Procurement Package", out["package_code"])
		self._track_package_lines(out["package_line_codes"])

		self.assertEqual(out["package"]["package_name"], "PW6 Custom Package Title")
		self.assertEqual(out["package"]["status"], "Draft")
		self.assertEqual(out["plan"].get("plan_code"), frappe.db.get_value("Procurement Plan", plan_name, "plan_code"))
		self.assertEqual(len(out["package_line_codes"]), 1)

		line_row = frappe.db.get_value(
			"Procurement Package Line",
			{"package_line_code": out["package_line_codes"][0]},
			("lot_group", "delivery_location"),
			as_dict=True,
		)
		self.assertEqual(line_row.lot_group, "Lot A")
		self.assertEqual(line_row.delivery_location, "Nairobi")

		if frappe.db.exists("DocType", "Planning Audit Event"):
			evidence = frappe.get_all(
				"Planning Audit Event",
				filters={"object_code": out["package_code"], "event_type": "Package Wizard Completed"},
				pluck="name",
			)
			self.assertTrue(evidence, "Expected a Package Wizard Completed audit event")

	def test_two_compatible_demands_create_one_package_two_lines(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._has_usable_template():
			self.skipTest("No usable Procurement Template with profiles available")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			create_package_from_wizard,
		)

		plan_name = self._mk_plan()
		_d1, inclusion1 = self._mk_included_demand(plan_name, title="PW6 Multi Demand A")
		_d2, inclusion2 = self._mk_included_demand(plan_name, title="PW6 Multi Demand B")

		out = create_package_from_wizard(
			[inclusion1["inclusion_code"], inclusion2["inclusion_code"]], {}, "Administrator"
		)
		self.assertTrue(out.get("ok"), out)
		self._track("Procurement Package", out["package_code"])
		self._track_package_lines(out["package_line_codes"])

		self.assertEqual(len(out["package_line_codes"]), 2)
		self.assertEqual(len(out["demand_codes"]), 2)
		self.assertEqual(len(out["inclusion_codes"]), 2)

	def test_api_wrapper_create_behind_permission_gate(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._has_usable_template():
			self.skipTest("No usable Procurement Template with profiles available")
		import json

		from kentender_procurement.procurement_planning.api.package_wizard import (
			create_pp_package_from_wizard,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW6 API Demand")

		out = create_pp_package_from_wizard(
			inclusion_codes=json.dumps([inclusion["inclusion_code"]]),
			config=json.dumps({"package_title": "PW6 API Package"}),
		)
		self.assertTrue(out.get("ok"), out)
		self._track("Procurement Package", out["package_code"])
		self._track_package_lines(out["package_line_codes"])
		self.assertEqual(out["package"]["package_name"], "PW6 API Package")
