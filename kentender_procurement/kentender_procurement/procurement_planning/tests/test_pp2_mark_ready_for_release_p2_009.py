# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-009 — mark_package_ready_for_release transition service."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_DRAFT,
	PKG_READY_FOR_RELEASE,
	PLAN_ACTIVE,
	PLAN_DRAFT,
	READINESS_PASSED,
)
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	record_package_method_decision,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	reconcile_package_readiness_staleness,
	run_package_readiness_checks,
)
from kentender_procurement.procurement_planning.services.package_release_service import (
	mark_package_ready_for_release,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	record_package_review_decision,
	submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageMarkReady,
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


def _journey_suffix(journey_code: str) -> str:
	jc = (journey_code or "").strip()
	if jc.upper().startswith("JRN-"):
		return jc[4:]
	return jc


class TestPP2MarkReadyForReleaseP2009(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok() or not frappe.db.exists("DocType", "Demand"):
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
		dept = ensure_department(f"Dept Mrdy {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Mrdy plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-MRDY-{frappe.generate_hash()[:6]}",
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
				"title": f"Mrdy demand {frappe.generate_hash(length=4)}",
				"demand_id": f"DEM-MRDY-{frappe.generate_hash()[:8]}",
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
		jc = f"JRN-MRDY-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Mark ready journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _create_draft_package(self) -> tuple[str, str, str, str]:
		bl_name, entity, dept, bl_code = self._seed_budget_line()
		if not bl_name:
			raise RuntimeError("no budget line")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		journey_code = self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-MRDY-{frappe.generate_hash()[:8]}"
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
		return package_code, journey_code, demand.demand_id, bl_code

	def _seed_upstream_handoffs(
		self, journey_code: str, demand_code: str, budget_line_code: str
	) -> None:
		suffix = _journey_suffix(journey_code)
		cards = (
			(
				f"DEMAPP-{suffix}",
				"Demand Approval Certificate",
				"Demand Intake and Approval",
				"Procurement Planning",
				"Demand",
				demand_code,
			),
			(
				f"BUDCONF-{suffix}",
				"Budget Funding Confirmation",
				"Budget",
				"Demand Intake and Approval",
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

	def _approved_with_passing_readiness(self) -> tuple[str, str]:
		package_code, journey_code, demand_code, bl_code = self._create_draft_package()
		record_package_method_decision(package_code, _works_payload(), "Administrator")
		self._track("Package Method Decision", f"METHDEC-{package_code}")
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
		return package_code, readiness_code

	def _audit_count(self, package_code: str) -> int:
		return frappe.db.count(
			"Planning Audit Event",
			{
				"object_code": package_code,
				"event_type": "Package Marked Ready for Release",
			},
		)

	def test_mark_ready_success(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, readiness_code = self._approved_with_passing_readiness()
		frappe.db.commit()

		out = mark_package_ready_for_release(package_code, "Administrator")

		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("from_state"), PKG_APPROVED)
		self.assertEqual(out.get("to_state"), PKG_READY_FOR_RELEASE)
		self.assertEqual(out.get("readiness_code"), readiness_code)

		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_READY_FOR_RELEASE)
		self.assertIsNone(pkg.workflow_reason)
		self.assertEqual(self._audit_count(package_code), 1)

		audit = frappe.get_all(
			"Planning Audit Event",
			filters={
				"object_code": package_code,
				"event_type": "Package Marked Ready for Release",
			},
			fields=["evidence_ref"],
			limit=1,
		)
		self.assertEqual((audit[0] if audit else {}).get("evidence_ref"), readiness_code)

	def test_blocked_invalid_state(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _, _, _ = self._create_draft_package()
		record_package_method_decision(package_code, _works_payload(), "Administrator")
		self._track("Package Method Decision", f"METHDEC-{package_code}")
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			mark_package_ready_for_release(package_code, "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageMarkReady.INVALID_STATE in err_text
			or "approved" in err_text.lower()
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_DRAFT,
		)

	def test_blocked_readiness_failed(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _, _, _ = self._create_draft_package()
		record_package_method_decision(package_code, _works_payload(), "Administrator")
		self._track("Package Method Decision", f"METHDEC-{package_code}")
		self._approve_package(package_code)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			mark_package_ready_for_release(package_code, "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageMarkReady.READINESS_FAILED in err_text
			or "readiness" in err_text.lower()
		)

	def test_blocked_readiness_stale(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, readiness_code = self._approved_with_passing_readiness()
		frappe.db.commit()

		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"estimated_value",
			frappe.db.get_value("Procurement Package", package_code, "estimated_value") + 5000,
			update_modified=False,
		)
		reconcile = reconcile_package_readiness_staleness(package_code)
		self.assertTrue(reconcile.get("stale"))

		with self.assertRaises(frappe.ValidationError) as ctx:
			mark_package_ready_for_release(package_code, "Administrator")
		err_text = str(ctx.exception)
		self.assertTrue(
			PackageMarkReady.READINESS_STALE in err_text
			or "stale" in err_text.lower()
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_APPROVED,
		)
		self.assertEqual(self._audit_count(package_code), 0)

	def test_idempotent_recall(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, readiness_code = self._approved_with_passing_readiness()
		frappe.db.commit()

		first = mark_package_ready_for_release(package_code, "Administrator")
		self.assertEqual(first.get("action"), "created")

		second = mark_package_ready_for_release(package_code, "Administrator")

		self.assertEqual(second.get("action"), "recalled")
		self.assertEqual(second.get("readiness_code"), readiness_code)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_READY_FOR_RELEASE,
		)
		self.assertEqual(self._audit_count(package_code), 1)
