# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW3 — Package Creation Wizard Step 2 backend: pre-create configuration
preview (`Planning Package Creation Wizard.md` §9). Pure computation over
N selected inclusions + in-progress form input; asserts nothing persists
until Step 3's final create call (Save Draft explicitly deferred).

Covers:
- Package identity defaults (title from demand, owner from session user,
  priority normalized to Normal/High/Emergency).
- Category/method: template-derived recommendation, override flagging,
  "method override requires justification" warning.
- Funding rollup: package value = sum of demand totals, reserved amount
  from the linked Budget Line(s), funding status Reserved/Insufficient.
- Lines: one line per selected demand (existing v1 granularity — no
  demand-item splitting), lot_group/delivery_location pass-through from
  per-line overrides.
- Missing-specification warning.
- No DB writes: no new `Procurement Package` row after calling preview.
"""

from __future__ import annotations

import frappe
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
	return bool(frappe.db.exists("DocType", "Procurement Plan")) and bool(frappe.db.exists("DocType", "Demand"))


class TestPW3WizardConfigurationPreview(IntegrationTestCase):
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
		dept = ensure_department(f"Dept PW3 {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"PW3 plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PW3-{frappe.generate_hash()[:6]}",
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

	def _mk_demand(
		self,
		bl_name: str,
		entity: str,
		dept: str,
		*,
		title: str,
		unit_cost: float = 100,
		specification_summary: str = "Scope",
	):
		did = f"DEM-PW3-{frappe.generate_hash()[:8]}"
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
				"specification_summary": specification_summary,
				"budget_line": bl_name,
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": unit_cost,
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
		jc = f"JRN-PW3-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"PW3 test journey {jc}", demand_id),
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
		item_codes = [f"DEMITEM-PW3-{frappe.generate_hash()[:8]}"]
		out = include_demand_in_procurement_plan(demand.demand_id, item_codes, plan_name, "Administrator")
		self._track("Procurement Handoff Card", out["inclusion_code"])
		inclusion = get_planning_inclusion(out["inclusion_code"])
		return demand, inclusion

	def test_preview_defaults_identity_from_demand_and_session_user(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		plan_name = self._mk_plan()
		demand, inclusion = self._mk_included_demand(plan_name, title="PW3 Identity Demand")

		out = preview_package_configuration([inclusion["inclusion_code"]])
		self.assertTrue(out.get("ok"), out)
		identity = out["package_identity"]
		self.assertEqual(identity["package_title"], "PW3 Identity Demand")
		self.assertEqual(identity["package_owner"], "Administrator")
		self.assertEqual(identity["package_priority"], "Normal")

	def test_preview_respects_user_supplied_config_overrides(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW3 Override Demand")

		out = preview_package_configuration(
			[inclusion["inclusion_code"]],
			{
				"package_title": "Custom Title",
				"package_priority": "Emergency",
				"package_description": "Custom desc",
			},
		)
		identity = out["package_identity"]
		self.assertEqual(identity["package_title"], "Custom Title")
		self.assertEqual(identity["package_priority"], "Emergency")
		self.assertEqual(identity["package_description"], "Custom desc")

	def test_preview_method_override_without_reason_warns(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW3 Method Demand")

		out = preview_package_configuration(
			[inclusion["inclusion_code"]],
			{"procurement_method": "Direct Procurement — Emergency"},
		)
		self.assertTrue(out["category_method"]["method_override_flag"])
		self.assertTrue(out["category_method"]["method_justification_required"])
		self.assertIn("Procurement method override requires justification.", out["warnings"])

		out_with_reason = preview_package_configuration(
			[inclusion["inclusion_code"]],
			{
				"procurement_method": "Direct Procurement — Emergency",
				"method_override_reason": "Urgent life-safety works",
			},
		)
		self.assertNotIn("Procurement method override requires justification.", out_with_reason["warnings"])

	def test_preview_funding_rollup_reserved_for_two_demands(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		plan_name = self._mk_plan()
		_demand_a, inclusion_a = self._mk_included_demand(plan_name, title="PW3 Fund A", unit_cost=100)
		_demand_b, inclusion_b = self._mk_included_demand(plan_name, title="PW3 Fund B", unit_cost=200)

		out = preview_package_configuration([inclusion_a["inclusion_code"], inclusion_b["inclusion_code"]])
		funding = out["funding"]
		self.assertEqual(funding["package_estimated_value"], 300)
		self.assertEqual(len(out["lines"]), 2)
		self.assertIn(funding["funding_status"], ("Reserved", "Insufficient"))

	def test_preview_missing_specification_warns(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(
			plan_name, title="PW3 No Spec Demand", specification_summary=""
		)

		out = preview_package_configuration([inclusion["inclusion_code"]])
		self.assertIn("One selected demand has missing specifications.", out["warnings"])

	def test_preview_line_overrides_apply_lot_group_and_delivery_location(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW3 Lot Demand")
		code = inclusion["inclusion_code"]

		out = preview_package_configuration(
			[code],
			{"line_overrides": {code: {"lot_group": "Lot 1", "delivery_location": "Nairobi"}}},
		)
		line = out["lines"][0]
		self.assertEqual(line["lot_group"], "Lot 1")
		self.assertEqual(line["delivery_location"], "Nairobi")

	def test_preview_never_persists_a_package(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW3 No Persist Demand")
		before = frappe.db.count("Procurement Package")

		preview_package_configuration([inclusion["inclusion_code"]], {"package_title": "Should Not Save"})

		after = frappe.db.count("Procurement Package")
		self.assertEqual(before, after)
		self.assertFalse(frappe.db.exists("Procurement Package", {"package_name": "Should Not Save"}))

	def test_preview_rejects_empty_selection(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		from kentender_procurement.procurement_planning.services.package_wizard_service import (
			preview_package_configuration,
		)

		out = preview_package_configuration([])
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NO_DEMANDS_SELECTED")

	def test_api_wrapper_preview_behind_permission_gate(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		import json

		from kentender_procurement.procurement_planning.api.package_wizard import (
			get_pp_package_wizard_configuration_preview,
		)

		plan_name = self._mk_plan()
		_demand, inclusion = self._mk_included_demand(plan_name, title="PW3 API Demand")

		out = get_pp_package_wizard_configuration_preview(
			inclusion_codes=json.dumps([inclusion["inclusion_code"]]),
			config=json.dumps({"package_priority": "High"}),
		)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out["package_identity"]["package_priority"], "High")
