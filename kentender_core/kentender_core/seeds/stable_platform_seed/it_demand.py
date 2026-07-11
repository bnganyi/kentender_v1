# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT demand supplement — DEM-MOH-2026-002."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds._common import ensure_department
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEMAND_CODE,
	IT_DEMAND_ESTIMATE,
	IT_DEMAND_TITLE,
	IT_DEPT_NAME,
)
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import (
	resolve_procuring_entity_moh,
)

_U_REQ = "requisitioner@moh.test"
_U_HOD = "hod.approver@moh.test"
_U_FIN = "finance.reviewer@moh.test"

_SPEC_SUBMITTED_AT = "2026-03-08 09:15:00"
_SPEC_HOD_APPROVED_AT = "2026-03-09 11:00:00"
_SPEC_APPROVED_AT = "2026-03-10 15:00:00"
_SPEC_REQUEST_DATE = "2026-03-08"
_SPEC_REQUIRED_BY_DATE = "2026-11-30"


def _resolve_budget_line() -> str | None:
	return frappe.db.get_value("Budget Line", {"budget_line_code": IT_BUDGET_LINE_CODE}, "name")


def _insert_demand(entity: str, dept: str, budget_line: str) -> frappe.model.document.Document:
	row = {
		"doctype": "Demand",
		"title": IT_DEMAND_TITLE,
		"demand_id": IT_DEMAND_CODE,
		"procuring_entity": entity,
		"requesting_department": dept,
		"requested_by": _U_REQ,
		"created_by": _U_REQ,
		"request_date": _SPEC_REQUEST_DATE,
		"required_by_date": _SPEC_REQUIRED_BY_DATE,
		"priority_level": "High",
		"demand_type": "Planned",
		"requisition_type": "Goods",
		"budget_line": budget_line,
		"specification_summary": (
			"Procure and implement an integrated Hospital Management Information System (HMIS), "
			"network backbone, and clinical workstation infrastructure at Makutano District Hospital."
		),
		"beneficiary_summary": (
			"Clinical staff, records officers, and patients at Makutano District Hospital requiring "
			"digital patient records, billing integration, and secure network connectivity."
		),
		"delivery_location": "Makutano District Hospital ICT Centre, Kenya",
		"items": [
			{
				"item_description": (
					"HMIS software licences, application servers, network switches, wireless access points, "
					"clinical workstations, and implementation services."
				),
				"category": "Goods",
				"uom": "Lot",
				"quantity": 1.0,
				"estimated_unit_cost": IT_DEMAND_ESTIMATE,
				"notes": "Information Technology procurement aligned to KE-PPRA-IT-2022-04.",
			}
		],
		"status": "Draft",
		"reservation_status": "None",
		"planning_status": "Not Planned",
	}
	doc = frappe.get_doc(row)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	if frappe.db.get_value("Demand", doc.name, "demand_id") != IT_DEMAND_CODE:
		frappe.db.set_value("Demand", doc.name, "demand_id", IT_DEMAND_CODE, update_modified=False)
	return frappe.get_doc("Demand", doc.name)


def _promote_to_approved(demand_name: str) -> None:
	frappe.db.set_value(
		"Demand",
		demand_name,
		{
			"status": "Approved",
			"submitted_by": _U_REQ,
			"submitted_at": _SPEC_SUBMITTED_AT,
			"hod_approved_by": _U_HOD,
			"hod_approved_at": _SPEC_HOD_APPROVED_AT,
			"finance_approved_by": _U_FIN,
			"finance_approved_at": _SPEC_APPROVED_AT,
			"reservation_status": "Reserved",
			"reservation_reference": f"SEED-RES-{demand_name}",
		},
		update_modified=False,
	)


def upsert_it_demand_supplement() -> dict[str, Any]:
	"""Idempotent upsert of DEM-MOH-2026-002."""
	frappe.only_for(("System Manager", "Administrator"))

	entity = resolve_procuring_entity_moh()
	if not entity:
		return {
			"ok": False,
			"error_code": "MISSING_PROCURING_ENTITY",
			"message": "Procuring Entity PE-MOH not found.",
		}

	budget_line = _resolve_budget_line()
	if not budget_line:
		return {
			"ok": False,
			"error_code": "MISSING_BUDGET_LINE",
			"message": f"Budget Line {IT_BUDGET_LINE_CODE} not found.",
		}

	budget_line_entity = frappe.db.get_value("Budget Line", budget_line, "procuring_entity")
	if budget_line_entity:
		entity = budget_line_entity

	existing = frappe.db.get_value("Demand", {"demand_id": IT_DEMAND_CODE}, "name")
	if existing:
		return {
			"ok": True,
			"demand": existing,
			"demand_id": IT_DEMAND_CODE,
			"created": False,
			"status": frappe.db.get_value("Demand", existing, "status") or "",
		}

	dept = ensure_department(IT_DEPT_NAME, entity)
	doc = _insert_demand(entity, dept, budget_line)
	_promote_to_approved(doc.name)
	return {
		"ok": True,
		"demand": doc.name,
		"demand_id": IT_DEMAND_CODE,
		"created": True,
		"status": "Approved",
	}
