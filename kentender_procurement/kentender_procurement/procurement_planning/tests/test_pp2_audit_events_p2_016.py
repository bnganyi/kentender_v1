# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-016 — consolidated Planning Audit Event contract tests."""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.api.package_line_edit import (
	add_pp_package_line,
)
from kentender_procurement.procurement_planning.api.workflow import (
	cancel_package,
	cancel_plan,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CANCELLED,
	PLAN_ACTIVE,
	PLAN_CANCELLED,
	PLAN_DRAFT,
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
from kentender_procurement.procurement_planning.services.package_review_service import (
	record_package_review_decision,
	submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.planning_audit_constants import (
	DEMAND_INCLUDED_IN_PLAN,
	METHOD_DECISION_RECORDED,
	PACKAGE_APPROVED,
	PACKAGE_CANCELLED,
	PACKAGE_CREATED,
	PACKAGE_LINE_CREATED,
	PACKAGE_SUBMITTED_FOR_REVIEW,
	PLAN_CANCELLED as PLAN_CANCELLED_EVENT,
	READINESS_CHECK_RUN,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	assert_audit_event_fields,
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
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


class TestPP2AuditEventsP2016(IntegrationTestCase):
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
			if doctype == "Planning Audit Event":
				if frappe.db.exists(doctype, name):
					doc = frappe.get_doc(doctype, name)
					doc.flags.ignore_pp_aud_allow_delete = True
					doc.flags.ignore_pp_aud_append_only_override = True
					doc.delete(ignore_permissions=True)
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
		dept = ensure_department(f"Dept Aud {frappe.generate_hash(length=4)}", ent)
		bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
		return bl_name, ent, dept, bl_code

	def _mk_plan(self, *, status: str = PLAN_ACTIVE) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"Aud plan {frappe.generate_hash(length=4)}",
				"plan_code": f"PP-AUD-{frappe.generate_hash()[:6]}",
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
				"title": f"Aud demand {frappe.generate_hash(length=4)}",
				"demand_id": f"DEM-AUD-{frappe.generate_hash()[:8]}",
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
		jc = f"JRN-AUD-{frappe.generate_hash()[:8]}"
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
			(jc, now, now, jc, f"Audit test journey {jc}", demand_id),
		)
		self._track("Procurement Journey", jc)
		return jc

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

	def _seed_approved_review(self, package_code: str) -> str:
		code = f"PKGREV-{package_code}-001"
		if frappe.db.exists("Package Review Decision", code):
			return code
		doc = frappe.get_doc(
			{
				"doctype": "Package Review Decision",
				"review_decision_code": code,
				"package_code": package_code,
				"decision_type": "Approved",
				"decided_by": "Administrator",
				"decided_at": now_datetime(),
				"from_state": "In Review",
				"to_state": "Approved",
				"decision_reason": "Approved for audit chain test.",
			}
		)
		doc.insert(ignore_permissions=True)
		self._track("Package Review Decision", code)
		return code

	def _audit_events(
		self, object_code: str | None = None, event_type: str | None = None
	) -> list[dict]:
		filters: dict = {}
		if object_code:
			filters["object_code"] = object_code
		if event_type:
			filters["event_type"] = event_type
		return frappe.get_all(
			"Planning Audit Event",
			filters=filters,
			fields=[
				"name",
				"event_code",
				"event_type",
				"object_type",
				"object_code",
				"actor",
				"occurred_at",
				"from_state",
				"to_state",
				"reason",
			],
			order_by="occurred_at asc, creation asc",
		)

	def _audit_count(self, *, event_type: str, object_code: str | None = None) -> int:
		return len(self._audit_events(object_code=object_code, event_type=event_type))

	def _run_happy_path_chain(self) -> dict:
		bl_name, entity, dept, bl_code = self._seed_budget_line()
		if not bl_name:
			raise RuntimeError("no budget line")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand = self._mk_demand(bl_name, entity, dept)
		journey_code = self._mk_journey(demand.demand_id)
		item_code = f"DEMITEM-AUD-{frappe.generate_hash()[:8]}"
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
		line_codes = list(pkg_out.get("package_line_codes") or [])
		for lc in line_codes:
			self._track("Procurement Package Line", lc)
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"journey_code",
			journey_code,
			update_modified=False,
		)

		method_out = record_package_method_decision(package_code, _works_payload(), "Administrator")
		decision_code = method_out.get("method_decision_code") or f"METHDEC-{package_code}"
		self._track("Package Method Decision", decision_code)

		self._seed_upstream_handoffs(journey_code, demand.demand_id, bl_code)
		self._seed_approved_review(package_code)
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
		if readiness_code:
			self._track("Package Readiness Result", readiness_code)

		submit_out = submit_package_for_review(package_code, "Administrator")
		submit_code = submit_out.get("review_decision_code")
		if submit_code:
			self._track("Package Review Decision", submit_code)

		approve_out = record_package_review_decision(
			package_code, {"decision": "Approved"}, "Administrator"
		)
		approve_code = approve_out.get("review_decision_code")
		if approve_code and approve_code != submit_code:
			self._track("Package Review Decision", approve_code)

		return {
			"inclusion_code": inclusion_code,
			"package_code": package_code,
			"line_code": line_codes[0] if line_codes else None,
			"decision_code": decision_code,
			"readiness_code": readiness_code,
			"demand_id": demand.demand_id,
			"plan_name": plan_name,
			"budget_line_id": bl_name,
			"item_code": item_code,
		}

	def test_audit_contract_happy_path_chain(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")

		ctx = self._run_happy_path_chain()
		frappe.db.commit()

		checks = [
			(DEMAND_INCLUDED_IN_PLAN, ctx["inclusion_code"]),
			(PACKAGE_CREATED, ctx["package_code"]),
			(PACKAGE_LINE_CREATED, ctx["line_code"]),
			(METHOD_DECISION_RECORDED, ctx["decision_code"]),
			(READINESS_CHECK_RUN, ctx["readiness_code"]),
			(PACKAGE_SUBMITTED_FOR_REVIEW, ctx["package_code"]),
			(PACKAGE_APPROVED, ctx["package_code"]),
		]
		for event_type, object_code in checks:
			self.assertTrue(object_code, msg=f"missing object for {event_type}")
			self.assertGreaterEqual(
				self._audit_count(event_type=event_type, object_code=object_code),
				1,
				msg=f"expected audit for {event_type} on {object_code}",
			)

		counts_before = {
			(event_type, object_code): self._audit_count(
				event_type=event_type, object_code=object_code
			)
			for event_type, object_code in checks
		}

		create_package_from_planning_inclusion(ctx["inclusion_code"], "Administrator")
		record_package_method_decision(ctx["package_code"], _works_payload(), "Administrator")
		run_package_readiness_checks(ctx["package_code"], "Administrator")
		record_package_review_decision(
			ctx["package_code"], {"decision": "Approved"}, "Administrator"
		)
		frappe.db.commit()

		idempotent_checks = [
			c for c in checks if c[0] != DEMAND_INCLUDED_IN_PLAN
		]
		for event_type, object_code in idempotent_checks:
			self.assertEqual(
				self._audit_count(event_type=event_type, object_code=object_code),
				counts_before[(event_type, object_code)],
				msg=f"idempotent recall duplicated {event_type}",
			)

	def test_workflow_cancel_plan_emits_audit(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		plan_name = self._mk_plan(status=PLAN_DRAFT)
		frappe.db.commit()
		reason = "Test cancel plan audit"

		out = cancel_plan(plan_id=plan_name, reason=reason)
		self.assertEqual(out.get("status"), PLAN_CANCELLED)

		rows = self._audit_events(object_code=plan_name, event_type=PLAN_CANCELLED_EVENT)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].get("reason"), reason)
		self.assertEqual(rows[0].get("from_state"), PLAN_DRAFT)
		self.assertEqual(rows[0].get("to_state"), PLAN_CANCELLED)

	def test_workflow_cancel_package_emits_audit(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")

		ctx = self._run_happy_path_chain()
		package_code = ctx["package_code"]
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"status",
			"In Review",
			update_modified=False,
		)
		frappe.db.commit()
		reason = "Test cancel package audit"

		out = cancel_package(package_id=package_code, reason=reason)
		self.assertEqual(out.get("status"), PKG_CANCELLED)

		rows = self._audit_events(object_code=package_code, event_type=PACKAGE_CANCELLED)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].get("reason"), reason)

	def test_package_line_add_emits_audit(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")

		bl_name, entity, dept, _bl_code = self._seed_budget_line()
		if not bl_name:
			self.skipTest("No active Budget Line available")
		plan_name = self._mk_plan(status=PLAN_ACTIVE)
		demand1 = self._mk_demand(bl_name, entity, dept)
		demand2 = self._mk_demand(bl_name, entity, dept)
		self._mk_journey(demand1.demand_id)
		frappe.db.commit()

		incl = include_demand_in_procurement_plan(
			demand1.demand_id,
			[f"DEMITEM-LINE-{frappe.generate_hash()[:8]}"],
			plan_name,
			"Administrator",
		)
		inclusion_code = incl.get("inclusion_code")
		self.assertTrue(inclusion_code)
		self._track("Procurement Handoff Card", inclusion_code)

		pkg_out = create_package_from_planning_inclusion(inclusion_code, "Administrator")
		package_code = pkg_out.get("package_code")
		self.assertTrue(package_code)
		self._track("Procurement Package", package_code)
		for lc in pkg_out.get("package_line_codes") or []:
			self._track("Procurement Package Line", lc)
		frappe.db.commit()

		before = self._audit_count(event_type=PACKAGE_LINE_CREATED)
		out = add_pp_package_line(
			package=package_code,
			demand_id=demand2.demand_id,
			budget_line_id=bl_name,
			amount=100,
		)
		self.assertTrue(out.get("ok"))
		line_name = out.get("name")
		self.assertTrue(line_name)
		self._track("Procurement Package Line", line_name)
		line_code = frappe.db.get_value("Procurement Package Line", line_name, "package_line_code") or line_name

		after = self._audit_count(event_type=PACKAGE_LINE_CREATED, object_code=line_code)
		self.assertEqual(after, 1)
		self.assertGreater(self._audit_count(event_type=PACKAGE_LINE_CREATED), before)

	def test_planning_audit_event_append_only(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")

		event_code = record_planning_audit_event(
			event_type="Contract Test Event",
			object_type="Procurement Plan",
			object_code=f"PP-APPEND-{frappe.generate_hash()[:6]}",
			to_state="Draft",
			actor="Administrator",
		)
		self.assertTrue(event_code)
		self._track("Planning Audit Event", event_code)

		planner_email = f"planner-aud-{frappe.generate_hash(length=6)}@pp2.test"
		if not frappe.db.exists("User", planner_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": planner_email,
					"first_name": "Audit",
					"last_name": "Planner",
					"send_welcome_email": 0,
					"enabled": 1,
				}
			)
			user.insert(ignore_permissions=True)
			self._track("User", planner_email)
		if not frappe.db.exists("Has Role", {"parent": planner_email, "role": "Procurement Planner"}):
			frappe.get_doc(
				{"doctype": "Has Role", "parent": planner_email, "parenttype": "User", "role": "Procurement Planner"}
			).insert(ignore_permissions=True)

		frappe.set_user(planner_email)
		doc = frappe.get_doc("Planning Audit Event", event_code)
		doc.reason = "mutated"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Planning Audit Event", event_code, ignore_permissions=True)

		frappe.set_user("Administrator")

	def test_audit_required_fields(self) -> None:
		if self._skip:
			self.skipTest("PP or Demand not installed")
		if not self._require_template():
			self.skipTest("No active Procurement Template with profiles available")

		ctx = self._run_happy_path_chain()
		frappe.db.commit()

		samples = [
			*self._audit_events(object_code=ctx["inclusion_code"], event_type=DEMAND_INCLUDED_IN_PLAN),
			*self._audit_events(object_code=ctx["package_code"], event_type=PACKAGE_CREATED),
			*self._audit_events(object_code=ctx["readiness_code"], event_type=READINESS_CHECK_RUN),
		]
		self.assertTrue(samples)
		for row in samples:
			assert_audit_event_fields(row)
