# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-004 — create_package_from_planning_inclusion write service."""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	DemandInclusion,
	PackageFromInclusion,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2CreatePackageP2004(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok() or not demand_consumers_live():
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
		dept = ensure_department(f"Dept Pkg {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Pkg plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PKG-{frappe.generate_hash()[:6]}",
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
		demand_id: str | None = None,
	) -> frappe.model.document.Document:
		did = demand_id or f"DEM-PKG-{frappe.generate_hash()[:8]}"
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Pkg demand {frappe.generate_hash(length=4)}",
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

	def _mk_journey(self, demand_id: str) -> str:
		jc = f"JRN-PKG-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Package test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _include_demand(
		self,
		demand: frappe.model.document.Document,
		plan_name: str,
		item_codes: list[str],
	) -> dict:
		out = include_demand_in_procurement_plan(
			demand.demand_id,
			item_codes,
			plan_name,
			"Administrator",
		)
		inclusion_code = out.get("inclusion_code")
		if inclusion_code:
			self._track("Procurement Handoff Card", inclusion_code)
		return out

	def _mk_blocking_package_line(
		self,
		plan_name: str,
		demand_name: str,
		budget_line: str,
		*,
		demand_item_code: str,
	) -> None:
		tpl = self._require_template()
		if not tpl:
			raise RuntimeError("no template")
		dcp = frappe.get_all("Decision Criteria Profile", limit=1, pluck="name")
		pkg = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_name": f"Blocker pkg {frappe.generate_hash(length=4)}",
				"plan_id": plan_name,
				"template_id": tpl,
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
		line = frappe.get_doc(
			{
				"doctype": "Procurement Package Line",
				"package_id": pkg.name,
				"demand_id": demand_name,
				"budget_line_id": budget_line,
				"demand_item_code": demand_item_code,
				"amount": 100,
				"quantity": 1.0,
				"line_status": PKG_DRAFT,
				"is_active": 1,
			}
		)
		line.insert(ignore_permissions=True)
		self._track("Procurement Package Line", line.name)

	def _audit_count(self, package_code: str) -> int:
		return frappe.db.count(
			"Planning Audit Event",
			{
				"object_code": package_code,
				"event_type": "Package Created",
			},
		)

	def test_creates_package_from_inclusion_on_success(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		bl_name, entity, dept, bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for package tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		item_codes = [f"DEMITEM-PKG-{frappe.generate_hash()[:8]}"]
		frappe.db.commit()

		incl = self._include_demand(demand, plan_name, item_codes)
		inclusion_code = incl.get("inclusion_code")
		self.assertTrue(inclusion_code)

		out = create_package_from_planning_inclusion(inclusion_code, "Administrator")

		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("status"), PKG_DRAFT)
		self.assertEqual(out.get("demand_code"), demand.demand_id)
		self.assertEqual(out.get("budget_line_code"), bl_code)
		package_code = out.get("package_code")
		self.assertTrue(package_code)
		self._track("Procurement Package", package_code)
		line_codes = out.get("package_line_codes") or []
		self.assertEqual(len(line_codes), 1)
		self._track("Procurement Package Line", line_codes[0])

		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_DRAFT)
		self.assertEqual(pkg.planning_inclusion_code, inclusion_code)
		self.assertEqual(pkg.demand_id, demand.name)
		self.assertEqual(pkg.budget_line_id, bl_name)

		line = frappe.get_doc("Procurement Package Line", {"package_line_code": line_codes[0]})
		self.assertEqual(line.demand_id, demand.name)
		self.assertEqual(line.budget_line_id, bl_name)
		self.assertEqual(line.demand_item_code, item_codes[0])

		inclusion = out.get("inclusion") or {}
		self.assertEqual(inclusion.get("status"), "Packaged")
		self.assertEqual(inclusion.get("created_package_code"), package_code)

	def test_idempotent_second_call(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for package tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		frappe.db.commit()

		incl = self._include_demand(demand, plan_name, [f"DEMITEM-PKG-{frappe.generate_hash()[:8]}"])
		inclusion_code = incl.get("inclusion_code")
		self.assertTrue(inclusion_code)

		first = create_package_from_planning_inclusion(inclusion_code, "Administrator")
		package_code = first.get("package_code")
		self.assertTrue(package_code)
		self._track("Procurement Package", package_code)
		for lc in first.get("package_line_codes") or []:
			self._track("Procurement Package Line", lc)

		count_after_first = frappe.db.count(
			"Procurement Package",
			{"planning_inclusion_code": inclusion_code, "is_active": 1},
		)

		second = create_package_from_planning_inclusion(inclusion_code, "Administrator")

		self.assertEqual(second.get("action"), "existing")
		self.assertEqual(second.get("package_code"), package_code)
		count_after_second = frappe.db.count(
			"Procurement Package",
			{"planning_inclusion_code": inclusion_code, "is_active": 1},
		)
		self.assertEqual(count_after_first, count_after_second)

	def test_blocked_when_inclusion_missing(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		with self.assertRaises(frappe.ValidationError) as ctx:
			create_package_from_planning_inclusion("PLANINCL-DOES-NOT-EXIST", "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageFromInclusion.INCLUSION_NOT_FOUND in err_text
			or "not found" in err_text.lower()
		)

	def test_blocked_when_demand_already_packaged(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for package tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-PKG-BLOCK-{frappe.generate_hash()[:8]}"
		frappe.db.commit()

		incl = self._include_demand(demand, plan_name, [item_code])
		inclusion_code = incl.get("inclusion_code")
		self.assertTrue(inclusion_code)

		self._mk_blocking_package_line(
			plan_name,
			demand.name,
			bl_name,
			demand_item_code=item_code,
		)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			create_package_from_planning_inclusion(inclusion_code, "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			DemandInclusion.DEMAND_ITEM_ALREADY_PACKAGED in err_text
			or "already" in err_text.lower()
		)

	def test_audit_event_on_create_only(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available for package tests")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		frappe.db.commit()

		incl = self._include_demand(demand, plan_name, [f"DEMITEM-PKG-{frappe.generate_hash()[:8]}"])
		inclusion_code = incl.get("inclusion_code")
		self.assertTrue(inclusion_code)

		first = create_package_from_planning_inclusion(inclusion_code, "Administrator")
		package_code = first.get("package_code")
		self.assertTrue(package_code)
		self._track("Procurement Package", package_code)
		for lc in first.get("package_line_codes") or []:
			self._track("Procurement Package Line", lc)
		self.assertEqual(self._audit_count(package_code), 1)

		create_package_from_planning_inclusion(inclusion_code, "Administrator")
		self.assertEqual(self._audit_count(package_code), 1)
