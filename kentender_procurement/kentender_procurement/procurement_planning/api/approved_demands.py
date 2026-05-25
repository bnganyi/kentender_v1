# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-001 — Approved demands awaiting Planning queue API."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates, pp_policy
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import PlanningPermission


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"total": 0,
		"rows": [],
		"filters_applied": {},
	}


def _include_fail(
	*,
	code: str,
	message: str,
	role_key: str = "auditor",
	blockers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
	out: dict[str, Any] = {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}
	if blockers:
		out["blockers"] = blockers
	return out


def _planning_gate() -> tuple[str | None, dict[str, Any] | None]:
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to the Procurement Planning approved demands queue."),
		fail=_fail,
		installed_doctype="Procurement Plan",
	)


def _include_planning_gate() -> tuple[str | None, dict[str, Any] | None]:
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return None, _include_fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	role_key = resolve_pp_role_key()
	if not role_key or not pp_api_gates.check_profile_access(
		pp_api_gates.PLANNING_QUEUE_READ,
		require_demand_read=False,
	):
		return None, _include_fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to include demands in a procurement plan."),
			role_key=role_key or "auditor",
		)
	try:
		pp_policy.assert_may_include_demand_in_plan()
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return None, _include_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key or "auditor",
		)
	return role_key, None


def _parse_filters(
	search_text: str | None = None,
	category: str | None = None,
	planning_status: str | None = None,
	procuring_entity: str | None = None,
	start: int | str | None = 0,
	limit: int | str | None = 50,
	filters: str | None = None,
) -> dict[str, Any]:
	out: dict[str, Any] = {
		"search_text": (search_text or "").strip(),
		"category": (category or "").strip(),
		"planning_status": (planning_status or "").strip(),
		"procuring_entity": (procuring_entity or "").strip(),
		"start": max(cint(start or 0), 0),
		"limit": cint(limit or 50),
	}
	if filters:
		try:
			parsed = json.loads(filters) if isinstance(filters, str) else filters
		except (TypeError, ValueError, json.JSONDecodeError):
			parsed = {}
		if isinstance(parsed, dict):
			for key, value in parsed.items():
				if key in out and value not in (None, ""):
					out[key] = value
	return out


@frappe.whitelist()
def get_pp_approved_demands_awaiting_planning(
	search_text: str | None = None,
	category: str | None = None,
	planning_status: str | None = None,
	procuring_entity: str | None = None,
	start: int | str | None = 0,
	limit: int | str | None = 50,
	filters: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted Planning queue — approved demands awaiting inclusion."""
	role_key, gate_err = _planning_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	parsed_filters = _parse_filters(
		search_text=search_text,
		category=category,
		planning_status=planning_status,
		procuring_entity=procuring_entity,
		start=start,
		limit=limit,
		filters=filters,
	)
	return get_approved_demands_awaiting_planning(parsed_filters, frappe.session.user)


def _parse_item_codes(raw: str | list[str] | None) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, list):
		return [str(c).strip() for c in raw if str(c).strip()]
	text = (raw or "").strip()
	if not text:
		return []
	try:
		parsed = json.loads(text)
	except (TypeError, ValueError, json.JSONDecodeError):
		return [text]
	if isinstance(parsed, list):
		return [str(c).strip() for c in parsed if str(c).strip()]
	return []


@frappe.whitelist()
def get_pp_approved_demand_planning_drawer(
	demand_code: str | None = None,
	plan_code: str | None = None,
	demand_item_codes: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted Planning drawer — demand summary and eligibility checks."""
	role_key, gate_err = _planning_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.approved_demand_drawer import (
		get_approved_demand_planning_drawer,
	)

	return get_approved_demand_planning_drawer(
		(demand_code or "").strip(),
		plan_code=(plan_code or "").strip() or None,
		demand_item_codes=_parse_item_codes(demand_item_codes),
		actor=frappe.session.user,
	)


@frappe.whitelist()
def include_pp_demand_in_procurement_plan(
	demand_code: str | None = None,
	procurement_plan_code: str | None = None,
	demand_item_codes: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted Planning write — include approved demand in procurement plan."""
	role_key, gate_err = _include_planning_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	demand_code = (demand_code or "").strip()
	plan_code = (procurement_plan_code or "").strip()
	item_codes = _parse_item_codes(demand_item_codes)

	if not demand_code or not plan_code:
		return _include_fail(
			code="MISSING_PARAMS",
			message=_("Demand code and procurement plan code are required."),
			role_key=role_key,
		)

	from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
		can_include_demand_in_plan,
		include_demand_in_procurement_plan,
	)

	try:
		out = include_demand_in_procurement_plan(
			demand_code,
			item_codes,
			plan_code,
			frappe.session.user,
		)
	except frappe.ValidationError as exc:
		guard = can_include_demand_in_plan(demand_code, item_codes, plan_code, frappe.session.user)
		blockers = (guard.get("blockers") or []) if isinstance(guard, dict) else []
		error_code = (
			(blockers[0].get("code") if blockers else None)
			or getattr(exc, "title", None)
			or "VALIDATION_ERROR"
		)
		return _include_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key,
			blockers=blockers or None,
		)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return _include_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key,
		)

	return {
		"ok": True,
		"role_key": role_key,
		**out,
	}
