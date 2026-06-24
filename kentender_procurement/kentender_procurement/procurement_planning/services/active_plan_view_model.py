# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-001 — Active Plan view-model adapter for PP3 Workbench."""

from __future__ import annotations

from datetime import date
from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.landing import (
	resolve_pp_role_key,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE

_CAN_CHANGE_PLAN_ROLES = frozenset(
	(
		"Procurement Planner",
		"Planning Authority",
		"Administrator",
		"System Manager",
	)
)


def _session_user(actor: str | None) -> str:
	return (actor or frappe.session.user or "").strip() or frappe.session.user


def _fiscal_year_value(raw: Any) -> int | None:
	if raw is None:
		return None
	text = str(raw).strip()
	if not text:
		return None
	if "/" in text:
		text = text.split("/", 1)[0].strip()
	if not text.isdigit():
		return None
	return int(text)


def _fiscal_year_label(raw: Any) -> str:
	fy = _fiscal_year_value(raw)
	if fy is None:
		fy = date.today().year
	return f"{fy}/{fy + 1}"


def _entity_label(entity_code: str | None) -> str:
	code = (entity_code or "").strip()
	if not code:
		return ""
	try:
		return (
			frappe.db.get_value("Procuring Entity", code, "entity_name")
			or code
		).strip()
	except Exception:
		return code


def _user_flags(actor: str) -> tuple[bool, bool]:
	try:
		can_view = bool(frappe.has_permission("Procurement Plan", "read", user=actor))
	except Exception:
		can_view = False
	try:
		roles = set(frappe.get_roles(actor))
	except Exception:
		roles = set()
	can_change = bool(roles & _CAN_CHANGE_PLAN_ROLES) and can_view
	return can_change, can_view


def _resolve_active_plan_row(
	actor: str,
	*,
	procuring_entity: str | None,
	fiscal_year: int | None,
) -> dict[str, Any] | None:
	filters: dict[str, Any] = {"status": PLAN_ACTIVE, "is_active": 1}
	if fiscal_year is not None:
		filters["fiscal_year"] = fiscal_year

	rows = frappe.get_list(
		"Procurement Plan",
		filters=filters,
		fields=[
			"name",
			"plan_code",
			"plan_name",
			"fiscal_year",
			"procuring_entity",
			"is_master_seed",
		],
		order_by="is_master_seed desc, modified desc",
		limit_page_length=50,
	)
	target_entity = (procuring_entity or "").strip()
	for row in rows:
		entity = (row.get("procuring_entity") or "").strip()
		if target_entity and entity != target_entity:
			continue
		if not pp_scope.entity_in_user_scope(entity, actor):
			continue
		return row
	return None


def get_active_plan_view_model(
	*,
	actor: str | None = None,
	procuring_entity: str | None = None,
	fiscal_year: Any | None = None,
) -> dict[str, Any]:
	"""Return PP3 P2-001 Active Plan view-model envelope."""
	user = _session_user(actor)
	role_key = resolve_pp_role_key(user) or "auditor"
	target_fy = _fiscal_year_value(fiscal_year)
	effective_fy = target_fy if target_fy is not None else date.today().year
	fy_label = _fiscal_year_label(effective_fy)
	can_change_plan, can_view_plan = _user_flags(user)
	active = _resolve_active_plan_row(
		user,
		procuring_entity=procuring_entity,
		fiscal_year=effective_fy,
	)
	if not active:
		return {
			"ok": True,
			"role_key": role_key,
			"has_active_plan": False,
			"fiscal_year": fy_label,
			"message": f"No active procurement plan exists for FY {fy_label}.",
			"primary_action": {"label": "Create Plan", "action": "create_plan"},
			"secondary_action": {
				"label": "Activate Existing Plan",
				"action": "activate_existing_plan",
			},
			"can_change_plan": can_change_plan,
			"can_view_plan": can_view_plan,
		}

	return {
		"ok": True,
		"role_key": role_key,
		"has_active_plan": True,
		"plan_code": (active.get("plan_code") or "").strip(),
		"plan_title": (active.get("plan_name") or active.get("plan_code") or "").strip(),
		"fiscal_year": _fiscal_year_label(active.get("fiscal_year")),
		"procuring_entity": _entity_label(active.get("procuring_entity")),
		"status_label": "Active",
		"can_change_plan": can_change_plan,
		"can_view_plan": can_view_plan,
	}
