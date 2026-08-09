# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-002 — Approved demand planning drawer payload (UI spec §8)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt, getdate

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)
from kentender_procurement.procurement_lifecycle.demand_planning_status import (
	build_demand_planning_status_payload,
)
from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import VALID_PROCUREMENT_CATEGORIES
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_budget_line_ref,
	_org_unit_label,
	_planning_usage_label,
	_primary_budget_line,
	load_demand_items_for_drawer,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	can_include_demand_in_plan,
)

_DRAWER_DEMAND_FIELDS = (
	"name",
	"demand_code",
	"title",
	"status",
	"planning_ready",
	"planning_usage",
	"procurement_category",
	"owner_org_unit",
	"procuring_entity",
	"confirmed_estimate",
	"requester_estimate",
	"currency",
	"approved_at",
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


def _resolve_demand_header(demand_code: str) -> dict[str, Any] | None:
	"""Resolve Demand by business code or document name (MVP fields)."""
	key = (demand_code or "").strip()
	if not key or not demand_doctype_available():
		return None
	row = frappe.db.get_value(
		"Demand", {"demand_code": key}, _DRAWER_DEMAND_FIELDS, as_dict=True
	)
	if not row:
		row = frappe.db.get_value("Demand", key, _DRAWER_DEMAND_FIELDS, as_dict=True)
	return row


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


def _strategy_snapshot_from_demand(demand_name: str | None) -> dict[str, str]:
	"""Primary Demand Strategy Reference as id/code/name (no raw-only display)."""
	empty = {"id": "", "code": "", "name": ""}
	if not demand_name or not frappe.db.exists("Demand Strategy Reference", {"demand": demand_name}):
		# Still try Primary lookup.
		pass
	if not demand_name:
		return empty
	primary = frappe.db.get_value(
		"Demand Strategy Reference",
		{"demand": demand_name, "reference_type": "Primary"},
		["name", "target_code", "target_name", "snapshot_label"],
		as_dict=True,
	)
	if not primary:
		return empty
	code = (primary.get("target_code") or "").strip()
	name = (primary.get("target_name") or primary.get("snapshot_label") or code).strip()
	return {
		"id": primary.get("name") or "",
		"code": code,
		"name": name,
	}


def _default_item_codes(demand_name: str) -> list[str]:
	rows = frappe.get_all(
		"Demand Item",
		filters={"demand": demand_name},
		fields=["item_code"],
		order_by="creation asc",
		limit_page_length=100,
	)
	return [(r.get("item_code") or "").strip() for r in rows if (r.get("item_code") or "").strip()]


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

	if not demand_doctype_available():
		from kentender_procurement.procurement_lifecycle.demand_module_gate import RETIRED_MESSAGE

		return _fail(
			code="DEMAND_MODULE_RETIRED",
			message=RETIRED_MESSAGE,
			role_key=role_key,
		)

	header = _resolve_demand_header(demand_code)
	if not header:
		return _fail(code="NOT_FOUND", message="Demand not found.", role_key=role_key)

	demand_name = header.get("name") or ""
	try:
		pp_scope.assert_may_act_on_demand(demand_name, user=actor)
	except frappe.PermissionError:
		return _fail(
			code="PP_ACCESS_DENIED",
			message="You do not have access to this demand.",
			role_key=role_key,
		)

	business_code = (header.get("demand_code") or demand_code).strip()
	category = (header.get("procurement_category") or "").strip()

	item_codes = [c.strip() for c in (demand_item_codes or []) if (c or "").strip()]
	if not item_codes:
		item_codes = _default_item_codes(demand_name)

	plan_row = _resolve_plan_row(plan_code)
	resolved_plan_code = (plan_code or "").strip()
	# Inclusion guard may still be gated (INT-003); treat retired as soft empty checks.
	try:
		inclusion_guard = can_include_demand_in_plan(
			business_code,
			item_codes,
			resolved_plan_code,
			actor,
		)
	except Exception:
		inclusion_guard = {"allowed": False, "checks": [], "blockers": []}
	if inclusion_guard is None:
		inclusion_guard = {"allowed": False, "checks": [], "blockers": []}

	# Local MVP eligibility when inclusion still fail-closed.
	if inclusion_guard.get("error_code") == "DEMAND_MODULE_RETIRED" or not inclusion_guard.get(
		"checks"
	):
		status_ok = (header.get("status") or "").strip() == "Approved" and cint(
			header.get("planning_ready")
		)
		budget_line = _primary_budget_line(demand_name)
		budget_ok = bool(budget_line)
		items_ok = bool(item_codes)
		inclusion_guard = {
			"allowed": bool(status_ok and budget_ok and items_ok),
			"checks": [
				{"id": "demand_approved", "label": "Demand approved", "ok": status_ok},
				{"id": "budget_linked", "label": "Budget line linked", "ok": budget_ok},
				{
					"id": "not_already_packaged",
					"label": "Demand item not already packaged",
					"ok": items_ok,
				},
			],
			"blockers": [],
		}

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

	budget_line_name = _primary_budget_line(demand_name)
	budget_line_ref = _budget_line_ref(budget_line_name)
	budget_context_payload: dict[str, Any] | None = None
	strategy_objective = _strategy_snapshot_from_demand(demand_name)
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
	if not approval_route:
		approval_route = f"/app/demand/{demand_name}"

	approval_dt = header.get("approved_at")
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

	estimate = flt(header.get("confirmed_estimate") or header.get("requester_estimate"))

	return {
		"ok": True,
		"role_key": role_key,
		"demand": {
			"id": demand_name,
			"code": business_code,
			"name": (header.get("title") or business_code).strip(),
			"status": (header.get("status") or "").strip(),
			"planning_status": _planning_usage_label(header.get("planning_usage") or ""),
			"department": _org_unit_label(header.get("owner_org_unit")),
			"category": category,
			"estimated_value": estimate,
			"currency": (header.get("currency") or "KES").strip() or "KES",
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
