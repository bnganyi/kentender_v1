# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-007 — submit_package_for_review transition service."""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_RETURNED,
	PLAN_ACTIVE,
	PLAN_DRAFT,
)
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
	PackageSubmitReview,
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


class TestPP2SubmitForReviewP2007(IntegrationTestCase):
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
		dept = ensure_department(f"Dept Sub {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Sub plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-SUB-{frappe.generate_hash()[:6]}",
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
				"title": f"Sub demand {frappe.generate_hash(length=4)}",
				"demand_id": f"DEM-SUB-{frappe.generate_hash()[:8]}",
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
		jc = f"JRN-SUB-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Submit test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _create_draft_package(self) -> str:
		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			raise RuntimeError("no budget line")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		journey_code = self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-SUB-{frappe.generate_hash()[:8]}"
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
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"journey_code",
			journey_code,
			update_modified=False,
		)
		return package_code

	def _ready_package(self) -> str:
		package_code = self._create_draft_package()
		record_package_method_decision(package_code, _works_payload(), "Administrator")
		self._track("Package Method Decision", f"METHDEC-{package_code}")
		return package_code

	def _audit_count(self, package_code: str) -> int:
		return frappe.db.count(
			"Planning Audit Event",
			{
				"object_code": package_code,
				"event_type": "Package Submitted for Review",
			},
		)

	def test_submit_from_draft_success(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._ready_package()
		frappe.db.commit()

		out = submit_package_for_review(package_code, "Administrator")
		review_code = out.get("review_decision_code")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("from_state"), PKG_DRAFT)
		self.assertEqual(out.get("to_state"), PKG_IN_REVIEW)
		self.assertTrue(review_code)
		self._track("Package Review Decision", review_code)

		row = frappe.get_doc("Package Review Decision", review_code)
		self.assertEqual(row.decision_type, "Submitted for Review")
		self.assertEqual(row.from_state, PKG_DRAFT)
		self.assertEqual(row.to_state, PKG_IN_REVIEW)

		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_IN_REVIEW)
		self.assertEqual(pkg.latest_review_code, review_code)
		self.assertEqual(self._audit_count(package_code), 1)

	def test_submit_from_returned_success(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._ready_package()
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"status",
			PKG_RETURNED,
			update_modified=False,
		)
		frappe.db.commit()

		out = submit_package_for_review(package_code, "Administrator")
		review_code = out.get("review_decision_code")
		self._track("Package Review Decision", review_code)

		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("from_state"), PKG_RETURNED)
		self.assertEqual(frappe.db.get_value("Procurement Package", package_code, "status"), PKG_IN_REVIEW)

	def test_blocked_invalid_state(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._ready_package()
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"status",
			PKG_APPROVED,
			update_modified=False,
		)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			submit_package_for_review(package_code, "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageSubmitReview.INVALID_STATE in err_text
			or "draft or returned" in err_text.lower()
		)

	def test_blocked_no_package_line(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._ready_package()
		frappe.db.sql(
			"""update `tabProcurement Package Line`
			set is_active = 0 where package_id = %s""",
			package_code,
		)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			submit_package_for_review(package_code, "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageSubmitReview.NO_PACKAGE_LINE in err_text
			or "package line" in err_text.lower()
		)

	def test_blocked_incomplete_without_method_decision(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._create_draft_package()
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			submit_package_for_review(package_code, "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageSubmitReview.PACKAGE_NOT_COMPLETE in err_text
			or "not complete" in err_text.lower()
		)

	def test_idempotent_recall_when_already_in_review(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code = self._ready_package()
		frappe.db.commit()

		first = submit_package_for_review(package_code, "Administrator")
		review_code = first.get("review_decision_code")
		self._track("Package Review Decision", review_code)

		second = submit_package_for_review(package_code, "Administrator")

		self.assertEqual(second.get("action"), "recalled")
		self.assertEqual(second.get("review_decision_code"), review_code)
		self.assertEqual(
			frappe.db.count(
				"Package Review Decision",
				{"package_code": package_code, "decision_type": "Submitted for Review"},
			),
			1,
		)
		self.assertEqual(self._audit_count(package_code), 1)
