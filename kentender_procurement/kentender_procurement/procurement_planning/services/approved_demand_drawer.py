# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-002 — Approved demand planning drawer payload (UI spec §8)."""

from __future__ import annotations

from typing import Any

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.utils import flt, getdate

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_procurement.procurement_lifecycle.demand_planning_status import (
	build_demand_planning_status_payload,
)
from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import VALID_PROCUREMENT_CATEGORIES
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_budget_line_ref,
	_derive_demand_item_code,
	_planning_status_label,
	load_demand_items_for_drawer,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	_resolve_demand_row,
	can_include_demand_in_plan,
)

_DRAWER_DEMAND_FIELDS = (
	"name",
	"demand_id",
	"title",
	"status",
	"planning_status",
	"requisition_type",
	"requesting_department",
	"procuring_entity",
	"total_amount",
	"budget_line",
	"finance_approved_at",
)

_DRAWER_CHECK_LABELS = {
	"demand_approved": "Demand approved",
	"budget_linked": "Budget line linked",
	"not_already_packaged": "Demand item not already packaged",
	"plan_active": "Procurement plan is active",
}


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _resolve_plan_row(plan_code: str | None) -> dict[str, Any] | None:
	code = (plan_code or "").strip()
	if not code:
		return None
	row = frappe.db.get_value(
		"Procurement Plan",
		{"plan_code": code},
		("name", "plan_code", "plan_name", "status"),
		as_dict=True,
	)
	if row:
		return row
	return frappe.db.get_value(
		"Procurement Plan",
		code,
		("name", "plan_code", "plan_name", "status"),
		as_dict=True,
	)


def _plan_ref(plan_row: dict[str, Any] | None) -> dict[str, str] | None:
	if not plan_row:
		return None
	return {
		"id": plan_row.get("name") or "",
		"code": (plan_row.get("plan_code") or plan_row.get("name") or "").strip(),
		"name": (plan_row.get("plan_name") or plan_row.get("plan_code") or "").strip(),
	}


def _strategy_objective_ref_from_demand(demand_name: str | None) -> dict[str, str]:
	"""XMOD-STR-004 — Demand Strategy Reference as id/code/name (no raw-only display)."""
	empty = {"id": "", "code": "", "name": ""}
	if not demand_name or not frappe.db.exists("Demand", demand_name):
		return empty
	try:
		from kentender_strategy.services.strategy_consumer import strategy_fields_from_doc
	except ImportError:
		return empty
	doc = frappe.get_doc("Demand", demand_name)
	sf = strategy_fields_from_doc(doc) or {}
	return {
		"id": (sf.get("performance_target") or sf.get("strategy_target") or "") or "",
		"code": (sf.get("performance_target_code") or "") or "",
		"name": (sf.get("performance_target_label") or "") or "",
	}


def _default_item_codes(demand_name: str, demand_code: str) -> list[str]:
	rows = frappe.get_all(
		"Demand Item",
		filters={"parent": demand_name, "parenttype": "Demand"},
		fields=["idx"],
		order_by="idx asc",
		limit_page_length=100,
	)
	codes: list[str] = []
	for row in rows:
		idx = int(row.get("idx") or len(codes) + 1)
		codes.append(_derive_demand_item_code(demand_code, idx))
	return codes


def _category_supported_label(category: str) -> str:
	cat = (category or "").strip()
	if cat:
		return f"Category supported: {cat}"
	return "Category supported"


def _build_drawer_checks(
	*,
	inclusion_guard: dict[str, Any],
	category: str,
	plan_code: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], bool]:
	checks: list[dict[str, Any]] = []
	blockers: list[dict[str, str]] = []

	for raw in inclusion_guard.get("checks") or []:
		check_id = str(raw.get("id") or "").strip()
		if check_id == "plan_active" and not (plan_code or "").strip():
			continue
		label = _DRAWER_CHECK_LABELS.get(check_id, str(raw.get("label") or check_id))
		checks.append(
			{
				"id": check_id,
				"label": label,
				"ok": bool(raw.get("ok")),
			}
		)

	category_ok = (category or "").strip() in VALID_PROCUREMENT_CATEGORIES
	checks.append(
		{
			"id": "category_supported",
			"label": _category_supported_label(category),
			"ok": category_ok,
		}
	)
	if not category_ok:
		blockers.append(
			{
				"code": "PP2-BLOCK-CATEGORY-UNSUPPORTED",
				"message": _category_supported_label(category),
			}
		)

	for raw in inclusion_guard.get("blockers") or []:
		blockers.append(
			{
				"code": str(raw.get("code") or ""),
				"message": str(raw.get("message") or ""),
			}
		)

	core_ids = ("demand_approved", "budget_linked", "not_already_packaged", "category_supported")
	core_ok = all(c.get("ok") for c in checks if c.get("id") in core_ids)
	if (plan_code or "").strip():
		allowed = bool(inclusion_guard.get("allowed")) and category_ok
	else:
		allowed = core_ok and not blockers

	return checks, blockers, allowed


def get_approved_demand_planning_drawer(
	demand_code: str,
	*,
	plan_code: str | None = None,
	demand_item_codes: list[str] | None = None,
	actor: str,
) -> dict[str, Any]:
	"""Return approved-demand drawer summary, context, evidence, and eligibility checks."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	demand_code = (demand_code or "").strip()
	if not demand_code:
		return _fail(code="MISSING_DEMAND", message="Demand code is required.", role_key=role_key)

	if not demand_consumers_live():
		from kentender_procurement.procurement_lifecycle.demand_module_gate import RETIRED_MESSAGE

		return _fail(
			code="DEMAND_MODULE_RETIRED",
			message=RETIRED_MESSAGE,
			role_key=role_key,
		)

	demand_row = _resolve_demand_row(demand_code)
	if not demand_row:
		return _fail(code="NOT_FOUND", message="Demand not found.", role_key=role_key)

	demand_name = demand_row.get("name") or ""
	try:
		pp_scope.assert_may_act_on_demand(demand_name, user=actor)
	except frappe.PermissionError:
		return _fail(
			code="PP_ACCESS_DENIED",
			message="You do not have access to this demand.",
			role_key=role_key,
		)

	header = frappe.db.get_value("Demand", demand_name, _DRAWER_DEMAND_FIELDS, as_dict=True) or {}
	business_code = (header.get("demand_id") or demand_code).strip()
	category = (header.get("requisition_type") or "").strip()
	if not category:
		items_preview = load_demand_items_for_drawer(demand_name, business_code)
		category = (items_preview[0].get("category") if items_preview else "") or ""

	item_codes = [c.strip() for c in (demand_item_codes or []) if (c or "").strip()]
	if not item_codes:
		item_codes = _default_item_codes(demand_name, business_code)

	plan_row = _resolve_plan_row(plan_code)
	resolved_plan_code = (plan_code or "").strip()
	inclusion_guard = can_include_demand_in_plan(
		business_code,
		item_codes,
		resolved_plan_code,
		actor,
	)
	if not resolved_plan_code:
		from kentender_procurement.procurement_planning.services.pp_governance_codes import DemandInclusion

		filtered_checks = [
			c for c in (inclusion_guard.get("checks") or []) if c.get("id") != "plan_active"
		]
		filtered_blockers = [
			b
			for b in (inclusion_guard.get("blockers") or [])
			if (b.get("code") or "") != DemandInclusion.PLAN_INACTIVE
		]
		inclusion_guard = {
			**inclusion_guard,
			"checks": filtered_checks,
			"blockers": filtered_blockers,
		}
	checks, blockers, allowed = _build_drawer_checks(
		inclusion_guard=inclusion_guard,
		category=category,
		plan_code=resolved_plan_code,
	)

	budget_line_ref = _budget_line_ref(header.get("budget_line"))
	budget_context_payload: dict[str, Any] | None = None
	strategy_objective = _strategy_objective_ref_from_demand(demand_name)
	if budget_line_ref.get("id"):
		budget_context_payload = get_budget_line_context(budget_line_ref["id"])

	journey_payload = build_demand_planning_status_payload(demand_name)
	approval_cert = journey_payload.get("demand_approval_certificate") if journey_payload.get("ok") else None
	approval_route = ""
	if isinstance(approval_cert, dict):
		approval_route = (
			approval_cert.get("demand_approval_record_route")
			or approval_cert.get("demand_form_route")
			or ""
		).strip()
	if not approval_route and approval_cert:
		approval_route = f"/app/demand/{demand_name}"

	approval_dt = header.get("finance_approved_at")
	approval_date = getdate(approval_dt).isoformat() if approval_dt else ""

	demand_items = load_demand_items_for_drawer(demand_name, business_code)
	funding = {}
	if budget_context_payload and budget_context_payload.get("ok"):
		data = budget_context_payload.get("data") or {}
		funding = {
			"amount_allocated": flt(data.get("amount_allocated")),
			"amount_available": flt(data.get("amount_available")),
			"currency": (data.get("currency") or "KES").strip() or "KES",
		}

	return {
		"ok": True,
		"role_key": role_key,
		"demand": {
			"id": demand_name,
			"code": business_code,
			"name": (header.get("title") or business_code).strip(),
			"status": (header.get("status") or "").strip(),
			"planning_status": _planning_status_label(
				status=(header.get("status") or "").strip(),
				planning_status=(header.get("planning_status") or "").strip(),
			),
			"department": (header.get("requesting_department") or "").strip(),
			"category": category,
			"estimated_value": flt(header.get("total_amount")),
			"currency": "KES",
			"approval_date": approval_date,
		},
		"target_plan": _plan_ref(plan_row),
		"budget_context": {
			"budget_line": budget_line_ref,
			"strategy_objective": strategy_objective,
			"funding": funding,
		},
		"demand_items": demand_items,
		"evidence": {
			"demand_approval_certificate": approval_cert,
			"view_route": approval_route,
		},
		"eligibility": {
			"allowed": allowed,
			"checks": checks,
			"blockers": blockers,
		},
		"actions": {
			"include_in_plan": allowed,
			"view_demand_approval_certificate": bool(approval_route),
			"approval_certificate_route": approval_route,
		},
	}
