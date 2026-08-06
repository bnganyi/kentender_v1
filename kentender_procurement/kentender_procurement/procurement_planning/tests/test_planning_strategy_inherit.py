# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""XMOD-STR-004 — Planning package inherits Demand Strategy Reference."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.api.strategy_reference import (
	list_active_strategy_targets,
	validate_planning_strategy_reference,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_with_lines,
)
from kentender_procurement.procurement_planning.services.package_wizard_service import (
	_strategy_label_for_demand,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
	include_demand_in_procurement_plan,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy


class TestPlanningStrategyInherit(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = upsert_works_master_strategy_hierarchy()

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package") or not frappe.db.exists(
			"DocType", "Demand"
		):
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

	def _track(self, doctype: str, name: str) -> None:
		self._cleanup.append((doctype, name))

	def _require_template(self) -> str | None:
		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			return None
		row = frappe.db.get_value(
			"Procurement Template",
			tpl[0],
			("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"),
			as_dict=True,
		)
		if not row or not all(row.values()):
			return None
		return tpl[0]

	def _budget_line(self) -> str | None:
		return frappe.db.get_value(
			"Budget Line", {"generated_reference": "MOH-BL-DHI-2027"}, "name"
		) or (self.seed.get("downstream") or {}).get("linked", {}).get("budget_line")

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"STR inherit {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-STR-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2030,
				"procuring_entity": self.seed["procuring_entity"],
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "status", PLAN_ACTIVE, update_modified=False)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(self, *, with_strategy: bool = True):
		bl = self._budget_line()
		if not bl:
			self.skipTest("MOH-BL-DHI-2027 Budget Line not present")
		dept = ensure_department(
			f"Dept STRI {frappe.generate_hash(length=4)}", self.seed["procuring_entity"]
		)
		self._track("Procuring Department", dept)
		did = f"DEM-STRI-{frappe.generate_hash()[:8]}"
		payload = {
			"doctype": "Demand",
			"title": f"Strategy inherit {did}",
			"demand_id": did,
			"procuring_entity": self.seed["procuring_entity"],
			"requesting_department": dept,
			"request_date": today(),
			"required_by_date": today(),
			"requisition_type": "Works",
			"priority_level": "Normal",
			"demand_type": "Planned",
			"specification_summary": "Scope",
			"beneficiary_summary": "Benefit",
			"budget_line": bl,
			"items": [
				{
					"item_description": "Line",
					"category": "Works",
					"uom": "Lot",
					"quantity": 1,
					"estimated_unit_cost": 1000,
				}
			],
		}
		if with_strategy:
			payload["strategy_target"] = self.seed["target"]
		doc = frappe.get_doc(payload)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Demand", doc.name, "status", "Approved", update_modified=False)
		doc.reload()
		self._track("Demand", doc.name)
		return doc

	def _mk_journey(self, demand_id: str) -> str:
		jc = f"JRN-STRI-{frappe.generate_hash()[:8]}"
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
			 %s, %s, %s, 'MOH', 'Works', 'Open Tender', '2030',
			 'planning_inclusion', 'Planning Inclusion', 'In Progress',
			 'Procurement Planning', 0, 0, 0)
			""",
			(jc, now, now, jc, f"STR inherit journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def test_package_inherits_demand_strategy_reference(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles")
		plan = self._mk_plan()
		demand = self._mk_demand(with_strategy=True)
		self.assertEqual(demand.strategy_target, self.seed["target"])
		self._mk_journey(demand.demand_id)
		incl = include_demand_in_procurement_plan(
			demand.demand_id, [f"DEMITEM-STRI-{frappe.generate_hash()[:6]}"], plan, "Administrator"
		)
		self.assertTrue(incl.get("ok") or incl.get("inclusion_code"), incl)
		inclusion_code = incl["inclusion_code"]
		self._track("Procurement Handoff Card", inclusion_code)
		inclusion = get_planning_inclusion(inclusion_code)
		result = create_package_with_lines(inclusions=[inclusion], actor="Administrator")
		pkg_name = result.get("package_code")
		self.assertTrue(pkg_name, result)
		self._track("Procurement Package", pkg_name)
		for line_code in result.get("package_line_codes") or []:
			self._track("Procurement Package Line", line_code)
		pkg = frappe.get_doc("Procurement Package", pkg_name)
		self.assertEqual(pkg.strategy_target, self.seed["target"])
		self.assertEqual(pkg.strategy_plan_version, self.seed["plan"])
		self.assertTrue((pkg.strategy_snapshot_label or "").strip())

	def test_wizard_strategy_label_from_demand(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		demand = self._mk_demand(with_strategy=True)
		label = _strategy_label_for_demand(demand.name)
		self.assertIn("(", label)
		code = frappe.db.get_value("Performance Target", self.seed["target"], "target_code")
		self.assertIn(code, label)

	def test_planning_strategy_adapter_smoke(self):
		if self._skip:
			self.skipTest("PP or Demand not installed")
		rows = list_active_strategy_targets(procuring_entity=self.seed["procuring_entity"])
		self.assertIsInstance(rows, list)
		self.assertGreaterEqual(len(rows), 1)
		ref = {
			"plan_version_id": self.seed["plan"],
			"node_id": self.seed["target"],
			"node_type": "PerformanceTarget",
		}
		out = validate_planning_strategy_reference(ref)
		self.assertTrue(out.get("valid") or out.get("selectable_for_new") is not None or "reference" in out)
