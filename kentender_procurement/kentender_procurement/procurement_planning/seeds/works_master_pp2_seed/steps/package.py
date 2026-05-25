# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure PKG-MOH-2026-001 and PKGLINE (spec §9–§10) via master-seed package creation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, get_datetime

from kentender_procurement.procurement_lifecycle.handoff_card_service import create_or_update_handoff_card
from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	recompute_package_estimated_value,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_EDITABLE_STATUSES,
	PKG_RELEASED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	CURRENCY,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	INCLUSION_CODE,
	INCLUSION_STATUS_PACKAGED,
	JOURNEY_CODE,
	PKG_CODE,
	PKG_DESCRIPTION,
	PKG_FISCAL_YEAR,
	PKG_LINE_CODE,
	PKG_LINE_DESCRIPTION,
	PKG_LINE_QUANTITY,
	PKG_LINE_STATUS_RELEASED,
	PKG_LINE_TITLE,
	PKG_LINE_UOM,
	PKG_PREPARED_AT,
	PKG_PRIORITY,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_CREATOR_EMAIL,
	PLAN_CREATOR_USER_CODE,
	PE_CODE,
	SEED_ACTOR,
	STD_VERSION_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.planning_references import resolve_demand_name

_REPAIRABLE_PACKAGE_FIELDS = (
	"plan_id",
	"template_id",
	"package_name",
	"package_description",
	"procurement_method",
	"contract_type",
	"procurement_category",
	"required_std_category",
	"required_std_type",
	"required_std_template_version_code",
	"currency",
	"is_active",
	"is_master_seed",
	"method_override_flag",
	"is_emergency",
	"planning_inclusion_code",
	"demand_id",
	"budget_line_id",
	"journey_code",
	"procuring_entity_code",
	"fiscal_year",
	"package_priority",
	"prepared_at",
	"created_by",
	"risk_profile_id",
	"kpi_profile_id",
	"decision_criteria_profile_id",
	"vendor_management_profile_id",
)

_REPAIRABLE_PACKAGE_LINE_FIELDS = (
	"package_id",
	"demand_id",
	"demand_item_code",
	"budget_line_id",
	"amount",
	"estimated_unit_cost",
	"line_title",
	"line_description",
	"procurement_category",
	"unit_of_measure",
	"quantity",
	"currency",
	"department",
	"priority",
	"line_status",
	"is_active",
	"is_master_seed",
)


def _resolve_budget_line_name() -> str:
	name = frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name")
	if name:
		return name
	if frappe.db.exists("Budget Line", BUDGET_LINE_CODE):
		return BUDGET_LINE_CODE
	frappe.throw(f"Budget Line {BUDGET_LINE_CODE} not found.", title="MISSING_BUDGET_LINE")


def _resolve_template_for_works() -> dict[str, Any]:
	demand_name = resolve_demand_name(DEMAND_CODE)
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
		if "Works" in str(types_raw):
			return row
	if rows:
		return rows[0]
	frappe.throw("No active procurement template found.", title="MISSING_TEMPLATE")


def _strict_package_values(
	*,
	prepared_by: str,
	template: dict[str, Any],
	plan: dict[str, Any],
	demand_name: str,
	budget_line_name: str,
) -> dict[str, Any]:
	return {
		"package_code": PKG_CODE,
		"plan_id": plan.name,
		"template_id": template["name"],
		"package_name": PKG_TITLE,
		"package_description": PKG_DESCRIPTION,
		"procurement_method": "Open Tender",
		"contract_type": template.get("default_contract_type") or "Fixed Price",
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"required_std_category": PKG_REQUIRED_STD_CATEGORY,
		"required_std_type": PKG_REQUIRED_STD_TYPE,
		"required_std_template_version_code": STD_VERSION_CODE,
		"currency": (plan.currency or CURRENCY).strip(),
		"status": PKG_DRAFT,
		"readiness_status": "Not Run",
		"is_active": 1,
		"is_master_seed": 1,
		"method_override_flag": 0,
		"is_emergency": 0,
		"locked_after_release": 0,
		"planning_inclusion_code": INCLUSION_CODE,
		"demand_id": demand_name,
		"budget_line_id": budget_line_name,
		"journey_code": JOURNEY_CODE,
		"procuring_entity_code": PE_CODE,
		"fiscal_year": PKG_FISCAL_YEAR,
		"package_priority": PKG_PRIORITY,
		"prepared_at": get_datetime(PKG_PREPARED_AT),
		"created_by": prepared_by,
		"risk_profile_id": template.get("risk_profile_id"),
		"kpi_profile_id": template.get("kpi_profile_id"),
		"decision_criteria_profile_id": template.get("decision_criteria_profile_id"),
		"vendor_management_profile_id": template.get("vendor_management_profile_id"),
	}


def _mark_inclusion_packaged(package_code: str) -> None:
	if not frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE):
		return
	doc = frappe.get_doc("Procurement Handoff Card", INCLUSION_CODE)
	locked = frappe.parse_json(doc.locked_summary or "{}")
	if not isinstance(locked, dict):
		locked = {}
	locked["created_package_code"] = package_code
	locked["inclusion_status"] = INCLUSION_STATUS_PACKAGED
	payload = {
		"handoff_code": doc.handoff_code,
		"handoff_title": doc.handoff_title,
		"journey_code": doc.journey_code,
		"source_module": doc.source_module,
		"target_module": doc.target_module,
		"source_object_type": doc.source_object_type,
		"source_object_code": doc.source_object_code,
		"target_object_type": doc.target_object_type,
		"target_object_code": doc.target_object_code,
		"status": doc.status,
		"generated_by": doc.generated_by,
		"generated_at": str(doc.generated_at) if doc.generated_at else None,
		"next_action": doc.next_action,
		"locked_summary": locked,
		"passed_forward_summary": frappe.parse_json(doc.passed_forward_summary or "{}"),
		"evidence_links": [],
		"technical_refs": frappe.parse_json(doc.technical_refs_json or "{}"),
		"is_master_seed": 1,
	}
	create_or_update_handoff_card(payload)


def _strict_package_line_values(
	*,
	demand_name: str,
	budget_line_name: str,
	demand: dict[str, Any],
) -> dict[str, Any]:
	return {
		"package_id": PKG_CODE,
		"package_line_code": PKG_LINE_CODE,
		"demand_id": demand_name,
		"budget_line_id": budget_line_name,
		"demand_item_code": DEMAND_ITEM_CODE,
		"amount": flt(demand.get("total_amount") or ESTIMATED_VALUE),
		"estimated_unit_cost": flt(demand.get("total_amount") or ESTIMATED_VALUE),
		"quantity": PKG_LINE_QUANTITY,
		"line_title": PKG_LINE_TITLE,
		"line_description": PKG_LINE_DESCRIPTION,
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"unit_of_measure": PKG_LINE_UOM,
		"currency": CURRENCY,
		"department": demand.get("requesting_department"),
		"priority": demand.get("priority_level") or PKG_PRIORITY,
		"line_status": PKG_DRAFT,
		"is_active": 1,
		"is_master_seed": 1,
	}


def _line_repair_allowed(*, package_status: str, line_status: str) -> bool:
	return (package_status or "").strip() in PKG_EDITABLE_STATUSES and (
		line_status or ""
	).strip() == PKG_DRAFT


def _ensure_master_package_line(*, demand_name: str, budget_line_name: str) -> dict[str, Any]:
	demand = frappe.db.get_value(
		"Demand",
		demand_name,
		("title", "total_amount", "requesting_department", "priority_level"),
		as_dict=True,
	) or {}
	values = _strict_package_line_values(
		demand_name=demand_name,
		budget_line_name=budget_line_name,
		demand=demand,
	)
	line_name = frappe.db.get_value(
		"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
	)
	if line_name:
		doc = frappe.get_doc("Procurement Package Line", line_name)
		package_status = frappe.db.get_value("Procurement Package", PKG_CODE, "status") or ""
		if _line_repair_allowed(package_status=package_status, line_status=doc.line_status):
			frappe.flags.skip_package_line_rollup = True
			try:
				for fieldname in _REPAIRABLE_PACKAGE_LINE_FIELDS:
					doc.set(fieldname, values[fieldname])
				doc.flags.ignore_mandatory = True
				doc.save(ignore_permissions=True)
				action = "repaired"
			finally:
				frappe.flags.pop("skip_package_line_rollup", None)
		else:
			action = "existing"
	else:
		frappe.flags.skip_package_line_rollup = True
		try:
			line = frappe.get_doc({"doctype": "Procurement Package Line", **values})
			line.flags.ignore_mandatory = True
			line.insert(ignore_permissions=True)
			action = "created"
		finally:
			frappe.flags.pop("skip_package_line_rollup", None)

	line_codes = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": PKG_CODE, "is_active": 1},
		pluck="package_line_code",
	)
	return {
		"action": action,
		"package_line_codes": line_codes or [PKG_LINE_CODE],
	}


def promote_master_package_line_released() -> dict[str, Any]:
	line_name = frappe.db.get_value(
		"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
	)
	if not line_name:
		return {"action": "missing", "package_line_code": PKG_LINE_CODE}

	package_status = frappe.db.get_value("Procurement Package", PKG_CODE, "status") or ""
	if package_status not in (PKG_RELEASED, PKG_CONSUMED):
		return {"action": "skipped", "package_line_code": PKG_LINE_CODE, "reason": "package_not_released"}

	line_status = frappe.db.get_value("Procurement Package Line", line_name, "line_status") or ""
	if (line_status or "").strip() == PKG_LINE_STATUS_RELEASED:
		return {"action": "existing", "package_line_code": PKG_LINE_CODE}

	frappe.db.set_value(
		"Procurement Package Line",
		line_name,
		{"line_status": PKG_LINE_STATUS_RELEASED},
		update_modified=False,
	)
	return {"action": "promoted", "package_line_code": PKG_LINE_CODE}


def ensure_master_package_line(*, demand_name: str | None = None, budget_line_name: str | None = None) -> dict[str, Any]:
	demand_name = demand_name or resolve_demand_name(DEMAND_CODE)
	budget_line_name = budget_line_name or _resolve_budget_line_name()
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		frappe.throw("Procurement Package not found.", title="MISSING_PACKAGE")
	return _ensure_master_package_line(demand_name=demand_name, budget_line_name=budget_line_name)


def _ensure_procurement_package(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	inclusion = get_planning_inclusion(INCLUSION_CODE)
	if not inclusion:
		frappe.throw("Planning inclusion not found.", title="MISSING_INCLUSION")

	linked = (inclusion or {}).get("created_package_code") or ""
	if linked and linked != PKG_CODE and frappe.db.exists("Procurement Package", linked):
		frappe.throw(
			f"Inconsistent master seed: inclusion links to {linked}, expected {PKG_CODE}. "
			"Use force_reset=True.",
			title="SEED_INCONSISTENT",
		)

	prepared_by = _ensure_seed_user(
		email=PLAN_CREATOR_EMAIL,
		user_code=PLAN_CREATOR_USER_CODE,
		full_name="Procurement Planner MOH",
	)
	demand_name = resolve_demand_name(DEMAND_CODE)
	budget_line_name = _resolve_budget_line_name()
	template = _resolve_template_for_works()
	plan = frappe.db.get_value("Procurement Plan", PLAN_CODE, ("name", "currency"), as_dict=True)
	if not plan:
		frappe.throw("Procurement Plan not found.", title="MISSING_PLAN")

	values = _strict_package_values(
		prepared_by=prepared_by,
		template=template,
		plan=plan,
		demand_name=demand_name,
		budget_line_name=budget_line_name,
	)
	existed = bool(frappe.db.exists("Procurement Package", PKG_CODE))
	if existed:
		doc = frappe.get_doc("Procurement Package", PKG_CODE)
		current_status = (doc.status or "").strip()
		if current_status in PKG_EDITABLE_STATUSES:
			doc.flags.ignore_validate_update_after_submit = True
			for fieldname in _REPAIRABLE_PACKAGE_FIELDS:
				doc.set(fieldname, values[fieldname])
			if current_status == PKG_DRAFT:
				doc.set("readiness_status", "Not Run")
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)
			action = "repaired"
		else:
			action = "existing"
	else:
		doc = frappe.get_doc({"doctype": "Procurement Package", **values})
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		action = "created"

	line_out = _ensure_master_package_line(
		demand_name=demand_name,
		budget_line_name=budget_line_name,
	)
	line_codes = line_out.get("package_line_codes") or [PKG_LINE_CODE]
	recompute_package_estimated_value(PKG_CODE)
	_mark_inclusion_packaged(PKG_CODE)

	return {
		"action": action,
		"package_code": PKG_CODE,
		"package_line_codes": line_codes,
	}


def ensure_master_package(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	return _ensure_procurement_package(actor=actor)
