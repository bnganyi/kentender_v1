# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-012 — post-release baseline locking."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.api.package_line_edit import add_pp_package_line
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_RELEASED,
	PLAN_ACTIVE,
	PLAN_DRAFT,
	POST_RELEASE_LOCK_MESSAGE,
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
from kentender_procurement.procurement_planning.services.planning_release_consumption_service import (
	mark_planning_release_consumed,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackagePostReleaseLock,
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


class TestPP2PostReleaseLockP2012(IntegrationTestCase):
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
			if doctype == "TM2 Tender":
				for row in frappe.get_all(
					"TM2 Tender Access Rule",
					filters={"tm2_tender": name},
					pluck="name",
				):
					if frappe.db.exists("TM2 Tender Access Rule", row):
						frappe.delete_doc(
							"TM2 Tender Access Rule", row, force=True, ignore_permissions=True
						)
				for row in frappe.get_all(
					"TM2 Tender Timeline",
					filters={"tm2_tender": name},
					pluck="name",
				):
					if frappe.db.exists("TM2 Tender Timeline", row):
						frappe.delete_doc(
							"TM2 Tender Timeline", row, force=True, ignore_permissions=True
						)
				if frappe.db.exists("TM2 Tender", name):
					frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)
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
		dept = ensure_department(f"Dept Lock {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Lock plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-LOCK-{frappe.generate_hash()[:6]}",
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
				"title": f"Lock demand {frappe.generate_hash(length=4)}",
				"demand_id": f"DEM-LOCK-{frappe.generate_hash()[:8]}",
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
		jc = f"JRN-LOCK-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Lock test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

	def _create_draft_package(self) -> tuple[str, str, str, str, str]:
		bl_name, entity, dept, bl_code = self._seed_budget_line()
		if not bl_name:
			raise RuntimeError("no budget line")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		journey_code = self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-LOCK-{frappe.generate_hash()[:8]}"
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
		return package_code, journey_code, demand.demand_id, bl_code, plan_name

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

	def _approved_with_passing_readiness(self) -> tuple[str, str, str]:
		package_code, journey_code, demand_code, bl_code, _plan_name = self._create_draft_package()
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
		return package_code, journey_code, readiness_code

	def _ready_for_release_package(self) -> tuple[str, str]:
		package_code, journey_code, _readiness_code = self._approved_with_passing_readiness()
		mark_package_ready_for_release(package_code, "Administrator")
		return package_code, journey_code

	def _xmv_ok(self):
		result = MagicMock()
		result.has_critical.return_value = False
		return result

	def _release_patches(self, *, has_tender: bool = True):
		return patch.multiple(
			"kentender_procurement.procurement_planning.services.package_release_service",
			deliver_procurement_package_release=MagicMock(),
			package_has_release_tender=MagicMock(return_value=has_tender),
			validate_package_for_release_xmv=MagicMock(return_value=self._xmv_ok()),
		)

	def _released_package(self) -> tuple[str, str, str]:
		package_code, journey_code = self._ready_for_release_package()
		release_code = pkgrel_handoff_code_from_journey_code(journey_code)
		frappe.db.commit()
		with self._release_patches(has_tender=True):
			release_package_to_tender_management(package_code, "Administrator")
		self._track("Procurement Handoff Card", release_code)
		return package_code, journey_code, release_code

	def _seed_tm2_tender(self, package_code: str, plan_name: str) -> str:
		tc = f"TND-LOCK-{frappe.generate_hash()[:8]}"
		tender = frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_code": tc,
				"tender_title": f"Lock test tender {tc}",
				"status": "Draft",
				"procurement_package": package_code,
				"procurement_plan": plan_name,
			}
		)
		tender.insert(ignore_permissions=True)
		self._track("TM2 Tender", tender.name)
		return tc

	def _consumed_package(self) -> tuple[str, str, str]:
		package_code, journey_code, release_code = self._released_package()
		plan_name = frappe.db.get_value("Procurement Package", package_code, "plan_id")
		tender_code = self._seed_tm2_tender(package_code, plan_name)
		frappe.db.commit()
		mark_planning_release_consumed(release_code, tender_code, "Administrator")
		return package_code, journey_code, release_code

	def _err_text(self, exc: BaseException) -> str:
		title = getattr(exc, "title", None)
		if title:
			return f"{title} {exc}".strip()
		return str(exc)

	def _assert_post_release_blocker(self, exc: BaseException) -> None:
		blob = self._err_text(exc)
		title = getattr(exc, "title", None) or ""
		combined = f"{title} {blob}".strip()
		self.assertTrue(
			PackagePostReleaseLock.LOCKED_AFTER_RELEASE in combined
			or POST_RELEASE_LOCK_MESSAGE in str(exc),
			msg=f"expected blocker in {combined!r}",
		)
		self.assertIn(POST_RELEASE_LOCK_MESSAGE, str(exc))

	def _first_package_line_context(self, package_code: str) -> tuple[str, str]:
		line = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": package_code, "is_active": 1},
			fields=["demand_id", "budget_line_id"],
			limit=1,
		)
		if not line:
			raise RuntimeError("no package line")
		return line[0]["demand_id"], line[0]["budget_line_id"]

	def test_blocked_edit_procurement_method(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _, _ = self._released_package()
		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_RELEASED)
		pkg.procurement_method = "Restricted Tender"
		with self.assertRaises(frappe.ValidationError) as ctx:
			pkg.save(ignore_permissions=True)
		self._assert_post_release_blocker(ctx.exception)
		pkg.reload()
		self.assertEqual(pkg.status, PKG_RELEASED)
		self.assertEqual(pkg.procurement_method, "Open Tender")

	def test_blocked_edit_estimated_value(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _, _ = self._released_package()
		pkg = frappe.get_doc("Procurement Package", package_code)
		before = flt(pkg.estimated_value)
		pkg.estimated_value = before + 5000
		with self.assertRaises(frappe.ValidationError) as ctx:
			pkg.save(ignore_permissions=True)
		self._assert_post_release_blocker(ctx.exception)

	def test_blocked_edit_procurement_category(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _, _ = self._released_package()
		pkg = frappe.get_doc("Procurement Package", package_code)
		pkg.procurement_category = "Goods"
		with self.assertRaises(frappe.ValidationError) as ctx:
			pkg.save(ignore_permissions=True)
		self._assert_post_release_blocker(ctx.exception)

	def test_blocked_package_line_add(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _, _ = self._released_package()
		demand_id, budget_line_id = self._first_package_line_context(package_code)
		out = add_pp_package_line(
			package=package_code,
			demand_id=demand_id,
			budget_line_id=budget_line_id,
			amount=250,
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackagePostReleaseLock.LOCKED_AFTER_RELEASE)
		self.assertIn(POST_RELEASE_LOCK_MESSAGE, out.get("message") or "")

	def test_blocked_record_method_decision(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		package_code, _, _ = self._released_package()
		with self.assertRaises(frappe.ValidationError) as ctx:
			record_package_method_decision(
				package_code,
				_works_payload(procurement_method="Restricted Tender"),
				"Administrator",
			)
		self._assert_post_release_blocker(ctx.exception)

	def test_locked_after_consumed(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")
		if not frappe.db.exists("DocType", "TM2 Tender"):
			self.skipTest("TM2 Tender not installed")
		package_code, _, _ = self._consumed_package()
		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_CONSUMED)
		pkg.procurement_method = "Restricted Tender"
		with self.assertRaises(frappe.ValidationError) as ctx:
			pkg.save(ignore_permissions=True)
		self._assert_post_release_blocker(ctx.exception)
