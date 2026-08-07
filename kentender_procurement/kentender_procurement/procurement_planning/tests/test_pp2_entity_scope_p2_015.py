# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-015 — entity/department scope guards."""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)
from kentender_procurement.procurement_planning.api.workflow import cancel_package, cancel_plan
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PKG_IN_REVIEW, PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	record_package_method_decision,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PlanningPermission,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


def _works_payload(**overrides) -> dict:
	base = {
		"procurement_category": "Works",
		"procurement_method": "Open Tender",
		"required_std_category": "Works",
		"required_std_type": "Building and Associated Civil Engineering Works",
		"method_basis": "Template",
		"override_flag": False,
	}
	base.update(overrides)
	return base


class TestPP2EntityScopeP2015(IntegrationTestCase):
	PLANNER = "planner@moh.test"
	DEPT_APPROVER = "hod.approver@moh.test"
	AUTHORITY = "planning.authority@moh.test"
	REVIEWER = "planning.reviewer@moh.test"

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok() or not demand_consumers_live():
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()
		ensure_roles()
		self._moh = ensure_procuring_entity(C.ENTITY_MOH, "Ministry of Health")
		self._moe = ensure_procuring_entity(C.ENTITY_MOE, "Ministry of Education")
		self._dept_proc = ensure_department(C.DEPT_PROC, self._moh)
		self._dept_clin = ensure_department(C.DEPT_CLIN, self._moh)
		upsert_seed_user(
			self.PLANNER,
			"Procurement Planner MOH",
			"Procurement Planner",
			entity_name=self._moh,
			department_docname=self._dept_proc,
		)
		upsert_seed_user(
			self.DEPT_APPROVER,
			"HoD Approver MOH",
			"Department Approver",
			entity_name=self._moh,
			department_docname=self._dept_clin,
		)
		upsert_seed_user(
			self.AUTHORITY,
			"Planning Authority MOH",
			"Planning Authority",
			entity_name=self._moh,
			department_docname=self._dept_proc,
		)
		upsert_seed_user(
			self.REVIEWER,
			"Planning Reviewer MOH",
			"Planning Reviewer",
			entity_name=self._moh,
			department_docname=self._dept_proc,
		)
		frappe.db.commit()
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

	def _require_template(self) -> bool:
		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			return False
		row = frappe.db.get_value(
			"Procurement Template",
			tpl[0],
			("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"),
			as_dict=True,
		)
		return bool(row and all(row.values()))

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
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		return bl_name, ent, self._dept_proc

	def _mk_plan(self, *, entity: str, status: str = PLAN_ACTIVE) -> str:
		suffix = frappe.generate_hash()[:6]
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Scope plan {suffix}",
				"plan_code": f"PP-SCOPE-{suffix}",
				"fiscal_year": 2029,
				"procuring_entity": entity,
				"currency": "KES",
				"status": status,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		self._track("Procurement Plan", plan.name)
		return plan.name

	def _mk_demand(self, bl_name: str, entity: str, dept: str) -> frappe.model.document.Document:
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Scope demand {frappe.generate_hash(length=4)}",
				"demand_id": f"DEM-SCOPE-{frappe.generate_hash()[:8]}",
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
		jc = f"JRN-SCOPE-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Scope journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _draft_package(
		self,
		*,
		plan_entity: str,
		department: str,
	) -> str:
		bl_name, entity, _ = self._seed_budget_line()
		if not bl_name:
			raise RuntimeError("no budget line")
		plan_name = self._mk_plan(entity=plan_entity)
		demand = self._mk_demand(bl_name, entity or C.ENTITY_MOH, department)
		journey_code = self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-SCOPE-{frappe.generate_hash()[:8]}"
		frappe.db.commit()
		incl = include_demand_in_procurement_plan(
			demand.demand_id,
			[item_code],
			plan_name,
			"Administrator",
		)
		inclusion_code = incl.get("inclusion_code")
		if not inclusion_code:
			raise RuntimeError("inclusion failed")
		self._track("Procurement Handoff Card", inclusion_code)
		pkg_out = create_package_from_planning_inclusion(inclusion_code, "Administrator")
		package_code = pkg_out.get("package_code")
		if not package_code:
			raise RuntimeError("package failed")
		self._track("Procurement Package", package_code)
		record_package_method_decision(package_code, _works_payload(), "Administrator")
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"journey_code",
			journey_code,
			update_modified=False,
		)
		return package_code

	def _review_decision_for_package(self, package_code: str) -> str:
		out = submit_package_for_review(package_code, "Administrator")
		code = out.get("review_decision_code")
		if not code:
			raise RuntimeError("review decision missing")
		self._track("Package Review Decision", code)
		return code

	def _assert_out_of_scope(self, exc: BaseException) -> None:
		self.assertIsInstance(exc, frappe.PermissionError)
		self.assertIn(PlanningPermission.OUT_OF_SCOPE, str(exc))

	def test_planner_cannot_include_demand_outside_entity(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No budget line")
		moe_plan = self._mk_plan(entity=C.ENTITY_MOE)
		demand = self._mk_demand(bl_name, entity or C.ENTITY_MOH, dept)
		item_code = f"DEMITEM-XENT-{frappe.generate_hash()[:8]}"
		frappe.db.commit()
		frappe.set_user(self.PLANNER)
		with self.assertRaises(frappe.PermissionError) as ctx:
			include_demand_in_procurement_plan(
				demand.demand_id,
				[item_code],
				moe_plan,
				self.PLANNER,
			)
		self._assert_out_of_scope(ctx.exception)

	def test_planner_cannot_submit_package_outside_entity(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._draft_package(plan_entity=C.ENTITY_MOE, department=self._dept_proc)
		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_DRAFT)
		frappe.db.commit()
		frappe.set_user(self.PLANNER)
		with self.assertRaises(frappe.PermissionError) as ctx:
			submit_package_for_review(package_code, self.PLANNER)
		self._assert_out_of_scope(ctx.exception)

	def test_planner_can_submit_package_within_entity(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._draft_package(plan_entity=C.ENTITY_MOH, department=self._dept_proc)
		frappe.db.commit()
		frappe.set_user(self.PLANNER)
		out = submit_package_for_review(package_code, self.PLANNER)
		self.assertTrue(out.get("ok"))
		code = out.get("review_decision_code")
		if code:
			self._track("Package Review Decision", code)

	def test_department_approver_cannot_read_review_decision_outside_dept(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._draft_package(plan_entity=C.ENTITY_MOH, department=self._dept_proc)
		review_code = self._review_decision_for_package(package_code)
		frappe.db.commit()
		frappe.set_user(self.DEPT_APPROVER)
		with self.assertRaises(frappe.PermissionError) as ctx:
			pp_scope.assert_may_read_package_review_decision(review_code)
		self._assert_out_of_scope(ctx.exception)
		self.assertFalse(
			frappe.has_permission("Package Review Decision", "read", review_code, user=self.DEPT_APPROVER)
		)

	def test_department_approver_can_read_review_decision_within_dept(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._draft_package(plan_entity=C.ENTITY_MOH, department=self._dept_clin)
		review_code = self._review_decision_for_package(package_code)
		frappe.db.commit()
		frappe.set_user(self.DEPT_APPROVER)
		pp_scope.assert_may_read_package_review_decision(review_code)
		self.assertTrue(
			frappe.has_permission("Package Review Decision", "read", review_code, user=self.DEPT_APPROVER)
		)

	def test_authority_cannot_cancel_plan_outside_entity(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		moe_plan = self._mk_plan(entity=C.ENTITY_MOE, status=PLAN_DRAFT)
		frappe.db.commit()
		frappe.set_user(self.AUTHORITY)
		with self.assertRaises(frappe.PermissionError) as ctx:
			cancel_plan(plan_id=moe_plan, reason="Cross-entity cancel should fail")
		self._assert_out_of_scope(ctx.exception)

	def test_reviewer_cannot_cancel_package_outside_entity(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._draft_package(plan_entity=C.ENTITY_MOE, department=self._dept_proc)
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"status",
			PKG_IN_REVIEW,
			update_modified=False,
		)
		frappe.db.commit()
		frappe.set_user(self.REVIEWER)
		with self.assertRaises(frappe.PermissionError) as ctx:
			cancel_package(package_id=package_code, reason="Cross-entity cancel should fail")
		self._assert_out_of_scope(ctx.exception)
