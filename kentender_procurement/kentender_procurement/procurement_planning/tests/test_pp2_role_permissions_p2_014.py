# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-014 — role permission guards (PP2-PERM-NEG fixtures)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)
from kentender_procurement.procurement_planning.api.workflow import release_package_to_tender
from kentender_procurement.procurement_planning.permissions import pp_policy
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PLAN_ACTIVE,
	READINESS_PASSED,
)
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	record_package_method_decision,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	run_package_readiness_checks,
)
from kentender_procurement.procurement_planning.services.package_release_service import (
	mark_package_ready_for_release,
	release_package_to_tender_management,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	record_package_review_decision,
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


def _journey_suffix(journey_code: str) -> str:
	jc = (journey_code or "").strip()
	if jc.upper().startswith("JRN-"):
		return jc[4:]
	return jc


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


class TestPP2RolePermissionsP2014(IntegrationTestCase):
	PLANNER = "planner@moh.test"
	REVIEWER = "planning.reviewer@moh.test"
	AUDITOR = "auditor@moh.test"
	FINANCE = "finance.reviewer@moh.test"

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok() or not demand_consumers_live():
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()
		ensure_roles()
		moh = ensure_procuring_entity(C.ENTITY_MOH, "Ministry of Health")
		dept = ensure_department(C.DEPT_PROC, moh)
		for email, full_name, role in (
			(self.PLANNER, "Procurement Planner MOH", "Procurement Planner"),
			(self.REVIEWER, "Planning Reviewer MOH", "Planning Reviewer"),
			(self.AUDITOR, "Auditor MOH", "Auditor"),
			(self.FINANCE, "Finance Reviewer MOH", "Finance Reviewer"),
		):
			upsert_seed_user(
				email,
				full_name,
				role,
				entity_name=moh,
				department_docname=dept,
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
			if doctype == "User":
				if frappe.db.exists("User", name):
					frappe.delete_doc("User", name, force=True, ignore_permissions=True)
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
			return None, None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept Perm {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Perm plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-PERM-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_ACTIVE,
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
				"title": f"Perm demand {frappe.generate_hash(length=4)}",
				"demand_id": f"DEM-PERM-{frappe.generate_hash()[:8]}",
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
		jc = f"JRN-PERM-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Perm journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _draft_package(self) -> tuple[str, str, str, str]:
		bl_name, entity, dept, bl_code = self._seed_budget_line()
		if not bl_name:
			raise RuntimeError("no budget line")
		plan_name = self._mk_plan()
		demand = self._mk_demand(bl_name, entity, dept)
		journey_code = self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-PERM-{frappe.generate_hash()[:8]}"
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
		return package_code, journey_code, demand.demand_id, bl_code

	def _seed_upstream_handoffs(
		self, journey_code: str, demand_code: str, budget_line_code: str
	) -> None:
		suffix = _journey_suffix(journey_code)
		cards = (
			(
				f"DEMAPP-{suffix}",
				"Demand Approval Certificate",
				"Demands",
				"Procurement Planning",
				"Demand",
				demand_code,
			),
			(
				f"BUDCONF-{suffix}",
				"Budget Funding Confirmation",
				"Budget",
				"Demands",
				"Budget Line",
				budget_line_code,
			),
		)
		for handoff_code, title, source_mod, target_mod, src_type, src_code in cards:
			create_or_update_handoff_card(
				{
					"handoff_code": handoff_code,
					"handoff_title": title,
					"journey_code": journey_code,
					"source_module": source_mod,
					"target_module": target_mod,
					"status": "Consumed",
					"next_action": "Proceed to procurement planning.",
					"source_object_type": src_type,
					"source_object_code": src_code,
				}
			)
			self._track("Procurement Handoff Card", handoff_code)

	def _approved_with_passing_readiness(self) -> str:
		package_code, journey_code, demand_code, bl_code = self._draft_package()
		self._approve_package(package_code)
		self._seed_upstream_handoffs(journey_code, demand_code, bl_code)
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			{
				"schedule_start": today(),
				"schedule_end": add_days(today(), 30),
			},
			update_modified=False,
		)
		readiness_out = run_package_readiness_checks(package_code, "Administrator")
		readiness_code = readiness_out.get("readiness_code")
		if not readiness_code:
			raise RuntimeError("readiness failed")
		self._track("Package Readiness Result", readiness_code)
		self.assertEqual(readiness_out.get("result_status"), READINESS_PASSED)
		return package_code

	def _approve_package(self, package_code: str) -> None:
		submit_out = submit_package_for_review(package_code, "Administrator")
		submit_code = submit_out.get("review_decision_code")
		if submit_code:
			self._track("Package Review Decision", submit_code)
		approve_out = record_package_review_decision(
			package_code, {"decision": "Approved"}, "Administrator"
		)
		approve_code = approve_out.get("review_decision_code")
		if approve_code:
			self._track("Package Review Decision", approve_code)

	def _in_review_package(self) -> str:
		package_code, *_rest = self._draft_package()
		submit_out = submit_package_for_review(package_code, "Administrator")
		code = submit_out.get("review_decision_code")
		if code:
			self._track("Package Review Decision", code)
		return package_code

	def _ready_for_release_package(self) -> str:
		package_code = self._approved_with_passing_readiness()
		mark_package_ready_for_release(package_code, "Administrator")
		return package_code

	def _ensure_system_manager_only(self) -> str:
		email = f"sm-only-{frappe.generate_hash(length=6)}@pp2.test"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "SM",
					"last_name": "Only",
					"send_welcome_email": 0,
					"enabled": 1,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("System Manager")
		self._track("User", email)
		return email

	def _assert_permission_denied(self, exc: BaseException) -> None:
		self.assertIsInstance(exc, frappe.PermissionError)
		self.assertIn(PlanningPermission.NOT_PERMITTED, str(exc))

	def test_planner_cannot_approve_package(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._in_review_package()
		frappe.db.commit()
		frappe.set_user(self.PLANNER)
		with self.assertRaises(frappe.PermissionError) as ctx:
			record_package_review_decision(
				package_code, {"decision": "Approved"}, self.PLANNER
			)
		self._assert_permission_denied(ctx.exception)

	def _release_patches(self):
		xmv = MagicMock()
		xmv.has_critical.return_value = False
		return patch.multiple(
			"kentender_procurement.procurement_planning.services.package_release_service",
			deliver_procurement_package_release=MagicMock(),
			package_has_release_tender=MagicMock(return_value=True),
			validate_package_for_release_xmv=MagicMock(return_value=xmv),
		)

	def test_planner_cannot_release_package(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._ready_for_release_package()
		frappe.db.commit()
		frappe.set_user(self.PLANNER)
		with self._release_patches():
			with self.assertRaises(frappe.PermissionError) as ctx:
				release_package_to_tender_management(package_code, self.PLANNER)
		self._assert_permission_denied(ctx.exception)

	def test_reviewer_can_approve_package(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._in_review_package()
		frappe.db.commit()
		frappe.set_user(self.REVIEWER)
		out = record_package_review_decision(
			package_code, {"decision": "Approved"}, self.REVIEWER
		)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("to_state"), PKG_APPROVED)
		code = out.get("review_decision_code")
		if code:
			self._track("Package Review Decision", code)

	def test_reviewer_cannot_edit_lines_in_review(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._in_review_package()
		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_IN_REVIEW)
		frappe.db.commit()
		frappe.set_user(self.REVIEWER)
		with self.assertRaises(frappe.PermissionError) as ctx:
			pp_policy.assert_may_edit_package_lines(pkg)
		self._assert_permission_denied(ctx.exception)

	def test_auditor_cannot_submit_package(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, *_rest = self._draft_package()
		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_DRAFT)
		frappe.db.commit()
		frappe.set_user(self.AUDITOR)
		with self.assertRaises(frappe.PermissionError) as ctx:
			submit_package_for_review(package_code, self.AUDITOR)
		self._assert_permission_denied(ctx.exception)

	def test_system_manager_only_cannot_release(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._ready_for_release_package()
		sm_user = self._ensure_system_manager_only()
		frappe.db.commit()
		frappe.set_user(sm_user)
		with self.assertRaises(frappe.PermissionError) as ctx:
			release_package_to_tender(package_code)
		self._assert_permission_denied(ctx.exception)

	def test_budget_officer_cannot_mark_ready(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._approved_with_passing_readiness()
		frappe.db.commit()
		frappe.set_user(self.FINANCE)
		with self.assertRaises(frappe.PermissionError) as ctx:
			mark_package_ready_for_release(package_code, self.FINANCE)
		self._assert_permission_denied(ctx.exception)

	def test_guest_cannot_include_demand(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No budget line")
		plan_name = self._mk_plan()
		demand = self._mk_demand(bl_name, entity, dept)
		item_code = f"DEMITEM-GUEST-{frappe.generate_hash()[:8]}"
		frappe.db.commit()
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError) as ctx:
			include_demand_in_procurement_plan(
				demand.demand_id,
				[item_code],
				plan_name,
				"Guest",
			)
		self._assert_permission_denied(ctx.exception)
