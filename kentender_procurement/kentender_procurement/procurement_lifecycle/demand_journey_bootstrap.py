# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Materialize a Procurement Journey for approved demands that lack PLC linkage."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.procurement_lifecycle.demand_approval_handoff import (
	create_demand_approval_certificate,
)

_DEMAND_FIELDS = (
	"name",
	"demand_code",
	"title",
	"status",
	"planning_ready",
	"procurement_category",
	"procuring_entity",
)


def _journey_code_from_demand_code(demand_code: str) -> str:
	code = (demand_code or "").strip()
	if not code:
		return ""
	for prefix in ("DMD-", "DEM-"):
		if code.upper().startswith(prefix):
			return f"JRN-{code[len(prefix):]}"
	return f"JRN-{code}"


def _procuring_entity_code(raw: str | None) -> str:
	ent = (raw or "").strip()
	if not ent:
		return "PE-MOH"
	if ent.upper().startswith("PE-"):
		return ent
	return f"PE-{ent}"


def _fiscal_year_label(budget_line_name: str | None) -> str:
	bl = (budget_line_name or "").strip()
	if not bl:
		return "2026/2027"
	budget = frappe.db.get_value("Budget Line", bl, "budget")
	period = frappe.db.get_value("Budget", budget, "fiscal_period") if budget else None
	return str(period or "2026/2027")


def _budget_line_business_code(budget_line_name: str | None) -> str:
	bl = (budget_line_name or "").strip()
	if not bl:
		return ""
	code = frappe.db.get_value("Budget Line", bl, "generated_reference")
	if not code:
		try:
			code = frappe.db.get_value("Budget Line", bl, "budget_line_code")
		except Exception:
			code = None
	return (code or bl).strip()


def _journey_procurement_category(raw: str | None) -> str:
	category = (raw or "").strip().lower()
	if "consult" in category:
		return "Consultancy"
	if "service" in category:
		return "Services"
	if "work" in category or "construction" in category:
		return "Works"
	return "Goods"


def _load_demand(demand_code: str) -> dict[str, Any] | None:
	code = (demand_code or "").strip()
	if not code:
		return None
	row = frappe.db.get_value("Demand", {"demand_code": code}, _DEMAND_FIELDS, as_dict=True)
	if row:
		return row
	return frappe.db.get_value("Demand", code, _DEMAND_FIELDS, as_dict=True)


def _resolve_existing_journey_code(demand_code: str, demand_row: dict[str, Any]) -> str | None:
	business_code = (demand_row.get("demand_code") or demand_code or "").strip()
	for ref in (business_code, demand_row.get("name")):
		ref = (ref or "").strip()
		if not ref:
			continue
		jc = frappe.db.get_value(
			"Procurement Journey",
			{"demand_ref": ref},
			"journey_code",
			order_by="modified desc",
		)
		if jc:
			return jc
	return None


def _confirmed_budget_line(demand_name: str) -> str:
	return (
		frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": demand_name, "bo_confirmation_status": "Confirmed"},
			"budget_line",
			order_by="creation asc",
		)
		or ""
	)


def _ensure_handoff(demand_code: str, journey_code: str) -> None:
	create_demand_approval_certificate(demand_code, journey_code)


def ensure_procurement_journey_for_demand_code(demand_code: str) -> str | None:
	"""Create or return the journey code linked to an approved demand."""
	from kentender_procurement.procurement_lifecycle.demand_module_gate import (
		demand_doctype_available,
	)

	demand_code = (demand_code or "").strip()
	if not demand_code:
		return None
	if not demand_doctype_available():
		return None

	demand = _load_demand(demand_code)
	if not demand:
		return None

	status = (demand.get("status") or "").strip()
	if status != "Approved" or not int(demand.get("planning_ready") or 0):
		return None

	business_code = (demand.get("demand_code") or demand_code).strip()
	existing = _resolve_existing_journey_code(demand_code, demand)
	if existing:
		_ensure_handoff(business_code, existing)
		return existing

	journey_code = _journey_code_from_demand_code(business_code)
	if not journey_code:
		return None
	budget_line = _confirmed_budget_line(str(demand["name"]))

	if frappe.db.exists("Procurement Journey", journey_code):
		frappe.db.set_value(
			"Procurement Journey",
			journey_code,
			"demand_ref",
			business_code,
			update_modified=True,
		)
	else:
		title = (demand.get("title") or business_code).strip()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": journey_code,
				"journey_title": title,
				"description": f"Procurement journey for approved Demand {business_code}.",
				"procuring_entity_code": _procuring_entity_code(demand.get("procuring_entity")),
				"fiscal_year": _fiscal_year_label(budget_line),
				"procurement_category": _journey_procurement_category(
					demand.get("procurement_category")
				),
				"current_stage_key": "demand_approved",
				"current_stage_label": "Need Approved",
				"current_status_category": "In Progress",
				"current_owner_module": "Procurement Planning",
				"current_owner_role": "Planning Authority",
				"next_action": "Include the approved demand in the procurement plan.",
				"demand_ref": business_code,
				"budget_line_ref": _budget_line_business_code(budget_line),
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"created_at": now_datetime(),
				"updated_at": now_datetime(),
				"is_master_seed": 0,
			}
		)
		doc.insert(ignore_permissions=True)

	_ensure_handoff(business_code, journey_code)

	return journey_code
