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

_ALLOWED_DEMAND_STATUSES = frozenset(("Approved", "Planning Ready"))
_DEMAND_FIELDS = (
	"name",
	"demand_id",
	"title",
	"status",
	"requisition_type",
	"procuring_entity",
	"budget_line",
)


def _journey_code_from_demand_id(demand_id: str) -> str:
	did = (demand_id or "").strip()
	if not did:
		return ""
	for prefix in ("DEM-", "DIA-"):
		if did.upper().startswith(prefix):
			return f"JRN-{did[len(prefix):]}"
	return f"JRN-{did}"


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
	year = frappe.db.get_value("Budget Line", bl, "fiscal_year")
	try:
		y = int(year)
	except (TypeError, ValueError):
		return "2026/2027"
	return f"{y}/{y + 1}"


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


def _load_demand(demand_code: str) -> dict[str, Any] | None:
	code = (demand_code or "").strip()
	if not code:
		return None
	row = frappe.db.get_value("Demand", {"demand_id": code}, _DEMAND_FIELDS, as_dict=True)
	if row:
		return row
	return frappe.db.get_value("Demand", code, _DEMAND_FIELDS, as_dict=True)


def _resolve_existing_journey_code(demand_code: str, demand_row: dict[str, Any]) -> str | None:
	demand_id = (demand_row.get("demand_id") or demand_code or "").strip()
	for ref in (demand_id, demand_row.get("name")):
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
	if status not in _ALLOWED_DEMAND_STATUSES:
		return None

	existing = _resolve_existing_journey_code(demand_code, demand)
	if existing:
		return existing

	demand_id = (demand.get("demand_id") or demand_code).strip()
	journey_code = _journey_code_from_demand_id(demand_id)
	if not journey_code:
		return None

	if frappe.db.exists("Procurement Journey", journey_code):
		frappe.db.set_value(
			"Procurement Journey",
			journey_code,
			"demand_ref",
			demand_id,
			update_modified=True,
		)
	else:
		title = (demand.get("title") or demand_id).strip()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": journey_code,
				"journey_title": title,
				"description": f"Procurement journey for approved demand {demand_id}.",
				"procuring_entity_code": _procuring_entity_code(demand.get("procuring_entity")),
				"fiscal_year": _fiscal_year_label(demand.get("budget_line")),
				"procurement_category": (demand.get("requisition_type") or "Goods").strip(),
				"current_stage_key": "demand_approved",
				"current_stage_label": "Need Approved",
				"current_status_category": "In Progress",
				"current_owner_module": "Procurement Planning",
				"current_owner_role": "Planning Authority",
				"next_action": "Include the approved demand in the procurement plan.",
				"demand_ref": demand_id,
				"budget_line_ref": _budget_line_business_code(demand.get("budget_line")),
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"created_at": now_datetime(),
				"updated_at": now_datetime(),
				"is_master_seed": 0,
			}
		)
		doc.insert(ignore_permissions=True)

	demapp_suffix = journey_code[4:] if journey_code.upper().startswith("JRN-") else journey_code
	demapp_code = f"DEMAPP-{demapp_suffix}"
	if not frappe.db.exists("Procurement Handoff Card", demapp_code):
		try:
			create_demand_approval_certificate(demand_id, journey_code)
		except ValueError:
			pass

	return journey_code
