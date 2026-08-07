# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-005 — record_package_method_decision write service."""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PKG_IN_REVIEW, PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	record_package_method_decision,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import PackageMethodDecision


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


class TestPP2RecordMethodDecisionP2005(IntegrationTestCase):
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
		dept = ensure_department(f"Dept Meth {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Meth plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-METH-{frappe.generate_hash()[:6]}",
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

	def _mk_demand(self, bl_name: str, entity: str, dept: str) -> frappe.model.document.Document:
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Meth demand {frappe.generate_hash(length=4)}",
				"demand_id": f"DEM-METH-{frappe.generate_hash()[:8]}",
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
		jc = f"JRN-METH-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Method test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _create_draft_package(self) -> tuple[str, str]:
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			raise RuntimeError("no budget line")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-METH-{frappe.generate_hash()[:8]}"
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
		for lc in pkg_out.get("package_line_codes") or []:
			self._track("Procurement Package Line", lc)
		return package_code, f"METHDEC-{package_code}"

	def _audit_count(self, method_decision_code: str) -> int:
		return frappe.db.count(
			"Planning Audit Event",
			{
				"object_code": method_decision_code,
				"event_type": "Method Decision Recorded",
			},
		)

	def test_records_works_open_tender_decision(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, decision_code = self._create_draft_package()
		frappe.db.commit()

		out = record_package_method_decision(package_code, _works_payload(), "Administrator")

		self.assertTrue(out.get("ok"))
		self.assertIn(out.get("action"), ("created", "superseded"))
		self.assertEqual(out.get("method_decision_code"), decision_code)
		self.assertEqual(out.get("status"), "Current")
		self._track("Package Method Decision", decision_code)

		row = frappe.get_doc("Package Method Decision", decision_code)
		self.assertEqual(row.procurement_category, "Works")
		self.assertEqual(row.procurement_method, "Open Tender")
		self.assertEqual(row.required_std_category, "Works")
		self.assertEqual(row.required_std_type, "Building and Associated Civil Engineering Works")
		self.assertFalse(bool(row.override_flag))
		self.assertTrue(bool(row.is_current))

		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.procurement_category, "Works")
		self.assertEqual(pkg.procurement_method, "Open Tender")
		self.assertEqual(pkg.required_std_category, "Works")
		self.assertEqual(pkg.required_std_type, "Building and Associated Civil Engineering Works")

	def test_idempotent_same_payload(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, decision_code = self._create_draft_package()
		payload = _works_payload()
		frappe.db.commit()

		first = record_package_method_decision(package_code, payload, "Administrator")
		self._track("Package Method Decision", decision_code)

		second = record_package_method_decision(package_code, payload, "Administrator")

		self.assertEqual(second.get("action"), "existing")
		self.assertEqual(second.get("method_decision_code"), first.get("method_decision_code"))
		self.assertEqual(
			frappe.db.count(
				"Package Method Decision",
				{"package_code": package_code, "is_current": 1},
			),
			1,
		)

	def test_blocked_when_package_not_found(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		with self.assertRaises(frappe.ValidationError) as ctx:
			record_package_method_decision("PKG-DOES-NOT-EXIST", _works_payload(), "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageMethodDecision.PACKAGE_NOT_FOUND in err_text
			or "not found" in err_text.lower()
		)

	def test_blocked_when_package_not_editable(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _decision_code = self._create_draft_package()
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"status",
			PKG_IN_REVIEW,
			update_modified=False,
		)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			record_package_method_decision(package_code, _works_payload(), "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageMethodDecision.LOCKED_AFTER_RELEASE in err_text
			or "draft" in err_text.lower()
		)

	def test_blocked_when_override_without_reason(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _decision_code = self._create_draft_package()
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			record_package_method_decision(
				package_code,
				_works_payload(override_flag=True),
				"Administrator",
			)
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageMethodDecision.METHOD_OVERRIDE_REASON in err_text
			or "override" in err_text.lower()
		)

	def test_blocked_when_std_category_missing(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _decision_code = self._create_draft_package()
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			record_package_method_decision(
				package_code,
				_works_payload(required_std_category=""),
				"Administrator",
			)
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageMethodDecision.STD_CATEGORY_MISSING in err_text
			or "std" in err_text.lower()
		)

	def test_audit_event_on_create_only(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, decision_code = self._create_draft_package()
		payload = _works_payload()
		frappe.db.commit()

		record_package_method_decision(package_code, payload, "Administrator")
		self._track("Package Method Decision", decision_code)
		self.assertEqual(self._audit_count(decision_code), 1)

		record_package_method_decision(package_code, payload, "Administrator")
		self.assertEqual(self._audit_count(decision_code), 1)
