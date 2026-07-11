# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT planning supplement — inclusion + package draft on PLAN-MOH-2026."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, get_datetime

from kentender_procurement.procurement_lifecycle.handoff_card_service import create_or_update_handoff_card
from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	recompute_package_estimated_value,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CURRENCY,
	PLAN_CODE,
	PLAN_CREATOR_EMAIL,
	PLAN_CREATOR_USER_CODE,
	SEED_ACTOR,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)
from kentender_procurement.procurement_planning.services.planning_references import resolve_demand_name
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEMAND_CODE,
	IT_DEMAND_ESTIMATE,
	IT_DEMAND_ITEM_CODE,
	IT_INCLUSION_CODE,
	IT_PKG_CODE,
	IT_PKG_LINE_CODE,
	IT_PKG_TITLE,
	IT_PROCUREMENT_CATEGORY,
	IT_REQUIRED_STD_CATEGORY,
	IT_REQUIRED_STD_TYPE,
	IT_STD_VERSION_CODE,
	PE_CODE,
	WORKS_JOURNEY_CODE,
)

_IT_PKG_DESCRIPTION = (
	"Procurement package for HMIS software, servers, network equipment, and implementation "
	"services at Makutano District Hospital."
)
_IT_INCLUSION_NOTE = (
	"Approved IT demand included in FY 2026/2027 procurement plan alongside Works renovation package."
)
_IT_INCLUDED_AT = "2026-04-12 10:30:00"
_IT_PKG_PREPARED_AT = "2026-04-19 14:00:00"
_IT_PKG_LINE_TITLE = "HMIS software, infrastructure, and implementation services"
_IT_PKG_LINE_DESCRIPTION = (
	"Consolidated IT package line derived from approved HMIS upgrade demand."
)


def _resolve_budget_line_name() -> str:
	name = frappe.db.get_value("Budget Line", {"budget_line_code": IT_BUDGET_LINE_CODE}, "name")
	if not name:
		frappe.throw(f"Budget Line {IT_BUDGET_LINE_CODE} not found.", title="MISSING_BUDGET_LINE")
	return name


def _resolve_template_for_it() -> dict[str, Any]:
	rows = frappe.get_all(
		"Procurement Template",
		filters={"is_active": 1},
		fields=[
			"name",
			"template_code",
			"default_method",
			"default_contract_type",
			"risk_profile_id",
			"kpi_profile_id",
			"decision_criteria_profile_id",
			"vendor_management_profile_id",
			"applicable_requisition_types",
		],
		order_by="modified desc",
	)
	for row in rows:
		types_raw = row.get("applicable_requisition_types") or ""
		if "Goods" in str(types_raw) or "Services" in str(types_raw):
			return row
	if rows:
		return rows[0]
	frappe.throw("No active procurement template found.", title="MISSING_TEMPLATE")


def _inclusion_payload(*, included_by: str) -> dict[str, Any]:
	return {
		"handoff_code": IT_INCLUSION_CODE,
		"handoff_title": "Planning Inclusion Record",
		"journey_code": WORKS_JOURNEY_CODE,
		"source_module": "Procurement Planning",
		"target_module": "Procurement Planning",
		"source_object_type": "Demand",
		"source_object_code": IT_DEMAND_CODE,
		"target_object_type": "Procurement Plan",
		"target_object_code": PLAN_CODE,
		"status": "Handed Off",
		"generated_by": included_by,
		"generated_at": _IT_INCLUDED_AT,
		"next_action": "Prepare a procurement package for the approved IT demand.",
		"locked_summary": {
			"procurement_plan": PLAN_CODE,
			"included_demand": IT_DEMAND_CODE,
			"budget_line": IT_BUDGET_LINE_CODE,
			"demand_item_codes": [IT_DEMAND_ITEM_CODE],
			"inclusion_note": _IT_INCLUSION_NOTE,
			"inclusion_status": "Included",
			"procuring_entity_code": PE_CODE,
			"fiscal_year": "2026/2027",
			"procurement_category": IT_PROCUREMENT_CATEGORY,
			"source_demand_status_at_inclusion": "Approved",
			"source_budget_status_at_inclusion": "Approved / Confirmed",
		},
		"passed_forward_summary": {
			"package_candidate": IT_PKG_TITLE,
			"category": IT_PROCUREMENT_CATEGORY,
			"estimated_value": flt(IT_DEMAND_ESTIMATE),
			"currency": CURRENCY,
			"required_std_version": IT_STD_VERSION_CODE,
		},
		"evidence_links": [
			{
				"label": "Procurement Plan",
				"object_type": "Procurement Plan",
				"object_code": PLAN_CODE,
				"module": "Procurement Planning",
				"route": f"/desk#Form/Procurement Plan/{PLAN_CODE}",
				"visibility": "Internal",
			}
		],
		"technical_refs": {
			"inclusion_code": IT_INCLUSION_CODE,
			"demand_item_codes": [IT_DEMAND_ITEM_CODE],
			"budget_line_code": IT_BUDGET_LINE_CODE,
		},
		"is_master_seed": True,
	}


def ensure_it_planning_inclusion(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	if not frappe.db.exists("Procurement Plan", PLAN_CODE):
		return {
			"ok": False,
			"error_code": "MISSING_PROCUREMENT_PLAN",
			"message": f"Procurement Plan {PLAN_CODE} not found. Run WORKS planning seed first.",
		}
	included_by = _ensure_seed_user(
		email=PLAN_CREATOR_EMAIL,
		user_code=PLAN_CREATOR_USER_CODE,
		full_name="Procurement Planner MOH",
	)
	existed = bool(frappe.db.exists("Procurement Handoff Card", IT_INCLUSION_CODE))
	result = create_or_update_handoff_card(_inclusion_payload(included_by=included_by))
	return {
		"ok": True,
		"action": "repaired" if existed else result.get("action", "created"),
		"inclusion_code": IT_INCLUSION_CODE,
	}


def ensure_it_planning_package(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	if not frappe.db.exists("Procurement Handoff Card", IT_INCLUSION_CODE):
		return {
			"ok": False,
			"error_code": "MISSING_INCLUSION",
			"message": f"Planning inclusion {IT_INCLUSION_CODE} not found.",
		}

	demand_name = resolve_demand_name(IT_DEMAND_CODE)
	budget_line_name = _resolve_budget_line_name()
	plan = frappe.get_doc("Procurement Plan", PLAN_CODE)
	template = _resolve_template_for_it()
	prepared_by = _ensure_seed_user(
		email=PLAN_CREATOR_EMAIL,
		user_code=PLAN_CREATOR_USER_CODE,
		full_name="Procurement Planner MOH",
	)

	if frappe.db.exists("Procurement Package", IT_PKG_CODE):
		pkg = frappe.get_doc("Procurement Package", IT_PKG_CODE)
		created = False
	else:
		pkg = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_code": IT_PKG_CODE,
				"plan_id": plan.name,
				"template_id": template["name"],
				"package_name": IT_PKG_TITLE,
				"package_description": _IT_PKG_DESCRIPTION,
				"procurement_method": template.get("default_method") or "Open Tender",
				"contract_type": template.get("default_contract_type") or "Fixed Price",
				"procurement_category": IT_PROCUREMENT_CATEGORY,
				"required_std_category": IT_REQUIRED_STD_CATEGORY,
				"required_std_type": IT_REQUIRED_STD_TYPE,
				"required_std_template_version_code": IT_STD_VERSION_CODE,
				"currency": (plan.currency or CURRENCY).strip(),
				"status": PKG_DRAFT,
				"readiness_status": "Not Run",
				"is_active": 1,
				"is_master_seed": 1,
				"planning_inclusion_code": IT_INCLUSION_CODE,
				"demand_id": demand_name,
				"budget_line_id": budget_line_name,
				"journey_code": WORKS_JOURNEY_CODE,
				"procuring_entity_code": PE_CODE,
				"fiscal_year": "2026/2027",
				"package_priority": "High",
				"prepared_at": get_datetime(_IT_PKG_PREPARED_AT),
				"created_by": prepared_by,
				"risk_profile_id": template.get("risk_profile_id"),
				"kpi_profile_id": template.get("kpi_profile_id"),
				"decision_criteria_profile_id": template.get("decision_criteria_profile_id"),
				"vendor_management_profile_id": template.get("vendor_management_profile_id"),
			}
		)
		pkg.flags.ignore_mandatory = True
		pkg.flags.ignore_validate = True
		pkg.insert(ignore_permissions=True)
		created = True

	if not frappe.db.exists("Procurement Package Line", {"package_line_code": IT_PKG_LINE_CODE}):
		line = frappe.get_doc(
			{
				"doctype": "Procurement Package Line",
				"package_line_code": IT_PKG_LINE_CODE,
				"package_id": IT_PKG_CODE,
				"demand_id": demand_name,
				"demand_item_code": IT_DEMAND_ITEM_CODE,
				"budget_line_id": budget_line_name,
				"amount": IT_DEMAND_ESTIMATE,
				"estimated_unit_cost": IT_DEMAND_ESTIMATE,
				"line_title": _IT_PKG_LINE_TITLE,
				"line_description": _IT_PKG_LINE_DESCRIPTION,
				"procurement_category": IT_PROCUREMENT_CATEGORY,
				"unit_of_measure": "Lot",
				"quantity": 1.0,
				"currency": CURRENCY,
				"priority": "High",
				"line_status": "Draft",
				"is_active": 1,
				"is_master_seed": 1,
			}
		)
		line.flags.ignore_mandatory = True
		line.flags.ignore_validate = True
		frappe.flags.skip_package_line_rollup = True
		try:
			line.insert(ignore_permissions=True)
		finally:
			frappe.flags.pop("skip_package_line_rollup", None)

	recompute_package_estimated_value(IT_PKG_CODE)

	inclusion = frappe.get_doc("Procurement Handoff Card", IT_INCLUSION_CODE)
	locked = frappe.parse_json(inclusion.locked_summary or "{}")
	if isinstance(locked, dict):
		locked["created_package_code"] = IT_PKG_CODE
		locked["inclusion_status"] = "Packaged"
		inclusion.locked_summary = locked
		inclusion.save(ignore_permissions=True)

	return {
		"ok": True,
		"package_code": IT_PKG_CODE,
		"package_line_code": IT_PKG_LINE_CODE,
		"created": created,
	}


def _with_plan_draft_for_seed(fn):
	"""Run seed mutation while strategic plan is temporarily Draft (G2 guard)."""
	from kentender_strategy.seeds.works_master_strategy_hierarchy import (
		PLAN_TITLE,
		START_YEAR,
		END_YEAR,
		resolve_procuring_entity_moh,
	)

	pe = resolve_procuring_entity_moh()
	if not pe:
		return fn()

	plan_name = frappe.db.get_value(
		"Strategic Plan",
		{
			"procuring_entity": pe,
			"start_year": START_YEAR,
			"end_year": END_YEAR,
			"strategic_plan_name": PLAN_TITLE,
		},
		"name",
	)
	if not plan_name:
		return fn()

	plan = frappe.get_doc("Strategic Plan", plan_name)
	prev_status = (plan.status or "").strip()
	if prev_status != "Draft":
		frappe.db.set_value("Strategic Plan", plan_name, "status", "Draft", update_modified=False)
	try:
		return fn()
	finally:
		if prev_status != "Draft":
			frappe.db.set_value("Strategic Plan", plan_name, "status", prev_status, update_modified=False)


def upsert_it_planning_supplement(*, include_package: bool = True) -> dict[str, Any]:
	"""Ensure IT planning inclusion (and optional package draft) on the shared MOH plan."""
	frappe.only_for(("System Manager", "Administrator"))

	def _run() -> dict[str, Any]:
		inclusion = ensure_it_planning_inclusion()
		if not inclusion.get("ok"):
			return inclusion
		out: dict[str, Any] = {"ok": True, "inclusion": inclusion}
		if include_package:
			pkg = ensure_it_planning_package()
			if not pkg.get("ok"):
				return pkg
			out["package"] = pkg
		return out

	return _with_plan_draft_for_seed(_run)
