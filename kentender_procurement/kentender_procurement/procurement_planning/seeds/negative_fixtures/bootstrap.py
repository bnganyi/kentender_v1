# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared upstream/bootstrap helpers for NEG-PP2 fixtures (isolated from WORKS master seed)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import frappe
from frappe.utils import add_days, flt, now_datetime, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_lifecycle.handoff_card_service import create_or_update_handoff_card
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_DRAFT,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
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
	reconcile_package_readiness_staleness,
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

SEED_ACTOR = "Administrator"

_WORKS_METHOD = {
	"procurement_category": "Works",
	"procurement_method": "Open Tender",
	"required_std_category": "Works",
	"required_std_type": "Building and Associated Civil Engineering Works",
	"method_basis": "Template",
	"override_flag": False,
}


def ensure_pp2_prerequisites() -> None:
	ensure_currency_kes()


def resolve_budget_line() -> tuple[str | None, str | None, str | None, str | None]:
	bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BUD-MOH-INFRA-2026-001"}, "name")
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
	data = ctx.get("data") or {}
	entity = data.get("procuring_entity")
	dept = ensure_department(f"NEG Dept {frappe.generate_hash(length=4)}", entity)
	bl_code = (data.get("budget_line_code") or bl_name or "").strip()
	return bl_name, entity, dept, bl_code


def require_template() -> str | None:
	tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
	if not tpl:
		return None
	row = frappe.db.get_value(
		"Procurement Template",
		tpl[0],
		(
			"name",
			"risk_profile_id",
			"kpi_profile_id",
			"vendor_management_profile_id",
			"default_method",
			"default_contract_type",
		),
		as_dict=True,
	)
	if not row or not all(
		row.get(key)
		for key in ("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id")
	):
		return None
	return row["name"]


def _rename_doc_if_needed(doctype: str, current: str, target: str) -> str:
	current_name = (current or "").strip()
	target_name = (target or "").strip()
	if not target_name or current_name == target_name:
		return current_name or target_name
	if frappe.db.exists(doctype, target_name):
		return target_name
	frappe.rename_doc(doctype, current_name, target_name, force=1, merge=0)
	return target_name


def _resolve_demand_docname(demand_code: str) -> str | None:
	code = (demand_code or "").strip()
	if not code:
		return None
	if frappe.db.exists("Demand", code):
		return code
	return frappe.db.get_value("Demand", {"demand_id": code}, "name")


def upsert_plan(*, plan_code: str, status: str = PLAN_ACTIVE) -> str:
	if frappe.db.exists("Procurement Plan", plan_code):
		frappe.db.set_value(
			"Procurement Plan",
			plan_code,
			{"status": status, "is_master_seed": 0},
			update_modified=False,
		)
		return plan_code
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"name": plan_code,
			"plan_code": plan_code,
			"plan_name": f"NEG plan {plan_code}",
			"fiscal_year": 2029,
			"status": status,
			"currency": "KES",
			"is_master_seed": 0,
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return plan_code


def upsert_demand(
	*,
	demand_code: str,
	budget_line: str | None,
	entity: str,
	dept: str,
	status: str = "Approved",
) -> str:
	existing = _resolve_demand_docname(demand_code)
	if existing:
		frappe.db.set_value(
			"Demand",
			existing,
			{
				"status": status,
				"budget_line": budget_line,
				"is_master_seed": 0,
			},
			update_modified=False,
		)
		return demand_code
	doc = frappe.get_doc(
		{
			"doctype": "Demand",
			"demand_id": demand_code,
			"title": f"NEG demand {demand_code}",
			"requisition_type": "Works",
			"procuring_entity": entity,
			"requesting_department": dept,
			"request_date": today(),
			"required_by_date": add_days(today(), 90),
			"priority_level": "Normal",
			"demand_type": "Planned",
			"specification_summary": "NEG fixture demand",
			"budget_line": budget_line,
			"items": [
				{
					"item_description": "NEG item",
					"category": "Works",
					"uom": "Lot",
					"quantity": 1,
					"estimated_unit_cost": 100000,
				}
			],
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	frappe.db.set_value("Demand", doc.name, "status", status, update_modified=False)
	return demand_code


def upsert_journey(*, journey_code: str, demand_code: str) -> str:
	if frappe.db.exists("Procurement Journey", journey_code):
		return journey_code
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
		 %s, %s, %s, 'MOH', 'Works', 'Open Tender', '2029',
		 'planning_inclusion', 'Planning Inclusion', 'In Progress',
		 'Procurement Planning', 0, 0, 0)
		""",
		(journey_code, now, now, journey_code, f"NEG journey {journey_code}", demand_code),
	)
	return journey_code


def seed_upstream_handoffs(*, journey_code: str, demand_code: str, budget_line_code: str) -> None:
	suffix = journey_code[4:] if journey_code.upper().startswith("JRN-") else journey_code
	for handoff_code, title, source_mod, target_mod, src_type, src_code in (
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
	):
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
				"is_master_seed": 0,
			}
		)


def include_and_package(
	*,
	demand_code: str,
	plan_code: str,
	journey_code: str,
	demand_item_code: str,
	inclusion_code: str | None = None,
	package_code: str | None = None,
) -> dict[str, str]:
	incl = include_demand_in_procurement_plan(
		demand_code,
		[demand_item_code],
		plan_code,
		SEED_ACTOR,
	)
	inclusion = (incl or {}).get("inclusion_code") or inclusion_code
	if not inclusion:
		frappe.throw("NEG fixture inclusion failed.", title="NEG_FIXTURE_SETUP")
	if inclusion_code and inclusion != inclusion_code:
		inclusion = _rename_doc_if_needed("Procurement Handoff Card", inclusion, inclusion_code)
		frappe.db.set_value(
			"Procurement Handoff Card",
			inclusion,
			{"is_master_seed": 0},
			update_modified=False,
		)

	pkg_out = create_package_from_planning_inclusion(inclusion, SEED_ACTOR)
	pkg = (pkg_out or {}).get("package_code") or package_code
	if not pkg:
		frappe.throw("NEG fixture package failed.", title="NEG_FIXTURE_SETUP")
	if package_code and pkg != package_code:
		pkg = _rename_doc_if_needed("Procurement Package", pkg, package_code)
	frappe.db.set_value(
		"Procurement Package",
		pkg,
		{"journey_code": journey_code, "is_master_seed": 0},
		update_modified=False,
	)
	return {
		"inclusion_code": inclusion,
		"package_code": pkg,
		"demand_item_code": demand_item_code,
	}


def approve_package(package_code: str) -> None:
	submit_out = submit_package_for_review(package_code, SEED_ACTOR)
	submit_code = submit_out.get("review_decision_code")
	if submit_code:
		frappe.db.set_value(
			"Package Review Decision",
			submit_code,
			{"is_master_seed": 0},
			update_modified=False,
		)
	record_package_review_decision(package_code, {"decision": "Approved"}, SEED_ACTOR)


def build_ready_for_release(
	*,
	plan_code: str,
	demand_code: str,
	journey_code: str,
	inclusion_code: str,
	package_code: str,
	demand_item_code: str,
	budget_line_code: str,
) -> dict[str, str]:
	include_and_package(
		demand_code=demand_code,
		plan_code=plan_code,
		journey_code=journey_code,
		demand_item_code=demand_item_code,
		inclusion_code=inclusion_code,
		package_code=package_code,
	)
	record_package_method_decision(package_code, _WORKS_METHOD, SEED_ACTOR)
	approve_package(package_code)
	seed_upstream_handoffs(
		journey_code=journey_code,
		demand_code=demand_code,
		budget_line_code=budget_line_code,
	)
	frappe.db.set_value(
		"Procurement Package",
		package_code,
		{"schedule_start": today(), "schedule_end": add_days(today(), 30)},
		update_modified=False,
	)
	readiness_out = run_package_readiness_checks(package_code, SEED_ACTOR)
	readiness_code = readiness_out.get("readiness_code")
	if readiness_out.get("result_status") != READINESS_PASSED:
		frappe.throw("NEG fixture readiness failed.", title="NEG_FIXTURE_SETUP")
	mark_package_ready_for_release(package_code, SEED_ACTOR)
	return {
		"package_code": package_code,
		"journey_code": journey_code,
		"readiness_code": readiness_code or "",
	}


def _release_patches(*, has_tender: bool = True):
	return patch.multiple(
		"kentender_procurement.procurement_planning.services.package_release_service",
		deliver_procurement_package_release=MagicMock(),
		package_has_release_tender=MagicMock(return_value=has_tender),
		validate_package_for_release_xmv=MagicMock(
			return_value=MagicMock(has_critical=MagicMock(return_value=False))
		),
	)


def release_package(
	*,
	package_code: str,
	journey_code: str,
	release_code: str | None = None,
) -> str:
	expected = release_code or pkgrel_handoff_code_from_journey_code(journey_code)
	with _release_patches(has_tender=True):
		out = release_package_to_tender_management(package_code, SEED_ACTOR)
	rc = (out or {}).get("release_code") or expected
	if release_code and rc != release_code:
		if frappe.db.exists("Procurement Handoff Card", rc):
			frappe.rename_doc("Procurement Handoff Card", rc, release_code, force=1, merge=0)
		rc = release_code
	frappe.db.set_value(
		"Procurement Handoff Card",
		rc,
		{"is_master_seed": 0},
		update_modified=False,
	)
	return rc


def seed_method_decision_missing_std(*, method_decision_code: str, package_code: str) -> None:
	record_package_method_decision(package_code, _WORKS_METHOD, SEED_ACTOR)
	auto_code = f"METHDEC-{package_code}"
	if frappe.db.exists("Package Method Decision", auto_code):
		_rename_doc_if_needed("Package Method Decision", auto_code, method_decision_code)
	frappe.db.set_value(
		"Package Method Decision",
		method_decision_code,
		{"required_std_category": "", "required_std_type": "", "is_master_seed": 0},
		update_modified=False,
	)
	frappe.db.set_value(
		"Procurement Package",
		package_code,
		{"required_std_category": "", "required_std_type": ""},
		update_modified=False,
	)


def seed_package_missing_method(*, package_code: str) -> None:
	auto_code = f"METHDEC-{package_code}"
	if frappe.db.exists("Package Method Decision", auto_code):
		frappe.delete_doc("Package Method Decision", auto_code, force=1)
	frappe.db.set_value(
		"Procurement Package",
		package_code,
		{"procurement_method": ""},
		update_modified=False,
	)


def upsert_method_decision(
	*,
	method_decision_code: str,
	package_code: str,
	payload: dict[str, Any],
) -> None:
	if frappe.db.exists("Package Method Decision", method_decision_code):
		doc = frappe.get_doc("Package Method Decision", method_decision_code)
		for key, value in payload.items():
			doc.set(key, value)
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		return
	record_package_method_decision(package_code, payload, SEED_ACTOR)
	if frappe.db.exists("Package Method Decision", f"METHDEC-{package_code}"):
		frappe.rename_doc(
			"Package Method Decision",
			f"METHDEC-{package_code}",
			method_decision_code,
			force=1,
			merge=0,
		)
	frappe.db.set_value(
		"Package Method Decision",
		method_decision_code,
		{"is_master_seed": 0},
		update_modified=False,
	)


def add_active_package_line(
	*,
	package_code: str,
	demand_code: str,
	budget_line: str,
	demand_item_code: str,
	amount: float = 100000,
) -> str:
	demand_name = frappe.db.get_value("Demand", {"demand_id": demand_code}, "name") or demand_code
	line = frappe.get_doc(
		{
			"doctype": "Procurement Package Line",
			"package_id": package_code,
			"demand_id": demand_name,
			"budget_line_id": budget_line,
			"demand_item_code": demand_item_code,
			"amount": amount,
			"quantity": 1.0,
			"line_status": "Draft",
			"is_active": 1,
		}
	)
	line.flags.ignore_mandatory = True
	line.insert(ignore_permissions=True)
	frappe.db.set_value(
		"Procurement Package Line",
		line.name,
		{"is_master_seed": 0},
		update_modified=False,
	)
	return line.name


def upsert_empty_package(*, plan_code: str, package_code: str, journey_code: str) -> None:
	template_name = require_template()
	if not template_name:
		frappe.throw("No active Procurement Template for NEG fixture.", title="NEG_FIXTURE_SETUP")
	template = frappe.db.get_value(
		"Procurement Template",
		template_name,
		(
			"name",
			"default_method",
			"default_contract_type",
			"risk_profile_id",
			"kpi_profile_id",
			"vendor_management_profile_id",
		),
		as_dict=True,
	) or {}
	dcp = frappe.get_all("Decision Criteria Profile", limit=1, pluck="name")
	if frappe.db.exists("Procurement Package", package_code):
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			{
				"status": PKG_DRAFT,
				"plan_id": plan_code,
				"journey_code": journey_code,
				"is_master_seed": 0,
			},
			update_modified=False,
		)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_code": package_code,
				"package_name": f"NEG package {package_code}",
				"plan_id": plan_code,
				"template_id": template.get("name"),
				"procurement_method": template.get("default_method") or "Open Tender",
				"contract_type": template.get("default_contract_type") or "Fixed Price",
				"currency": "KES",
				"status": PKG_DRAFT,
				"journey_code": journey_code,
				"risk_profile_id": template.get("risk_profile_id"),
				"kpi_profile_id": template.get("kpi_profile_id"),
				"vendor_management_profile_id": template.get("vendor_management_profile_id"),
				"decision_criteria_profile_id": dcp[0] if dcp else None,
				"is_active": 1,
				"is_master_seed": 0,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
	for line_name in frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code, "is_active": 1},
		pluck="name",
	):
		frappe.db.set_value("Procurement Package Line", line_name, "is_active", 0, update_modified=False)


def mark_readiness_stale(package_code: str) -> None:
	line = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code, "is_active": 1},
		fields=["name", "amount"],
		limit=1,
	)
	if line:
		frappe.db.set_value(
			"Procurement Package Line",
			line[0]["name"],
			"amount",
			flt(line[0].get("amount")) + 5000,
			update_modified=True,
		)
	frappe.db.set_value(
		"Procurement Package",
		package_code,
		"estimated_value",
		frappe.db.get_value("Procurement Package", package_code, "estimated_value") + 5000,
		update_modified=True,
	)
	reconcile_package_readiness_staleness(package_code)


def upsert_tm2_tender(
	*,
	tender_code: str,
	package_code: str,
	plan_name: str,
	procurement_method: str = "Open Tender",
	procurement_category: str = "Works",
) -> str:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		frappe.throw("TM2 Tender DocType not installed.", title="NEG_FIXTURE_SETUP")
	if frappe.db.exists("TM2 Tender", tender_code):
		frappe.db.set_value(
			"TM2 Tender",
			tender_code,
			{
				"procurement_method": procurement_method,
				"procurement_category": procurement_category,
				"procurement_package_code": package_code,
				"procurement_plan_code": plan_name,
				"is_master_seed": 0,
			},
			update_modified=False,
		)
		return tender_code
	doc = frappe.get_doc(
		{
			"doctype": "TM2 Tender",
			"name": tender_code,
			"tender_code": tender_code,
			"tender_title": f"NEG tender {tender_code}",
			"procurement_method": procurement_method,
			"procurement_category": procurement_category,
			"procurement_package_code": package_code,
			"procurement_plan_code": plan_name,
			"status": "Draft",
			"is_master_seed": 0,
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return tender_code
