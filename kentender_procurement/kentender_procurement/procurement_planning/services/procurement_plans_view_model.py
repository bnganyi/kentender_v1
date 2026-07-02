# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-002+ — Procurement Plans setup/oversight view-models."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.api.landing import (
	_plan_workbench_action_flags,
	resolve_pp_role_key,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_RELEASED,
	PKG_RETURNED,
	PLAN_ACTIVE,
	PLAN_CANCELLED,
	PLAN_CLOSED,
	PLAN_SUPERSEDED,
	READINESS_FAILED,
)
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	_entity_label,
	_fiscal_year_label,
)

_PLANNING_INCLUSION_TITLE = "Planning Inclusion Record"


def _session_user(actor: str | None) -> str:
	return (actor or frappe.session.user or "").strip() or frappe.session.user


def _counts_label(*, demands: int, packages: int, released: int) -> str:
	parts: list[str] = []
	if demands == 1:
		parts.append(f"{demands} demand")
	elif demands:
		parts.append(f"{demands} demands")
	else:
		parts.append("0 demands")
	if packages == 1:
		parts.append(f"{packages} package")
	elif packages:
		parts.append(f"{packages} packages")
	else:
		parts.append("0 packages")
	if released == 1:
		parts.append(f"{released} released")
	elif released:
		parts.append(f"{released} released")
	else:
		parts.append("0 released")
	return " · ".join(parts)


def _plan_counts(plan_code: str) -> tuple[int, int, int]:
	code = (plan_code or "").strip()
	if not code:
		return 0, 0, 0
	demands = 0
	if frappe.db.exists("DocType", "Procurement Handoff Card"):
		demands = frappe.db.count(
			"Procurement Handoff Card",
			{
				"handoff_title": _PLANNING_INCLUSION_TITLE,
				"target_object_code": code,
			},
		)
	packages = 0
	released = 0
	if frappe.db.exists("DocType", "Procurement Package"):
		packages = frappe.db.count(
			"Procurement Package",
			{"plan_id": code, "is_active": 1},
		)
		released = frappe.db.count(
			"Procurement Package",
			{
				"plan_id": code,
				"is_active": 1,
				"status": ["in", [PKG_RELEASED, PKG_CONSUMED]],
			},
		)
	return int(demands or 0), int(packages or 0), int(released or 0)


def _plan_blockers_count(plan_code: str, *, actor: str) -> int:
	code = (plan_code or "").strip()
	if not code or not frappe.db.exists("DocType", "Procurement Package"):
		return 0
	rows = frappe.get_all(
		"Procurement Package",
		filters={"plan_id": code, "is_active": 1},
		fields=["name", "status", "readiness_status", "procuring_entity_code"],
		limit_page_length=500,
	)
	count = 0
	for row in rows or []:
		entity = (row.get("procuring_entity_code") or "").strip()
		if not pp_scope.entity_in_user_scope(entity, actor):
			continue
		status = (row.get("status") or "").strip()
		readiness = (row.get("readiness_status") or "").strip()
		if status == PKG_RETURNED or readiness == READINESS_FAILED:
			count += 1
	return count


def _blockers_label(count: int) -> str:
	if count <= 0:
		return "None"
	if count == 1:
		return "1 blocker"
	return f"{count} blockers"


def _status_label(status: str | None, *, is_active: int | bool) -> str:
	value = (status or "").strip()
	if value == PLAN_ACTIVE and cint(is_active):
		return "Active"
	return value or "Draft"


def _entity_ref(entity_code: str | None) -> dict[str, str]:
	code = (entity_code or "").strip()
	name = _entity_label(code) if code else ""
	return {"id": code, "code": code, "name": name or code}


def _status_tone(status: str | None, *, is_active: int | bool) -> str:
	value = (status or "").strip()
	if value == PLAN_ACTIVE and cint(is_active):
		return "success"
	if value == "Draft":
		return "warning"
	if value == PLAN_SUPERSEDED:
		return "works"
	return "neutral"


def _row_action(status: str | None, *, is_active: int | bool) -> str:
	value = (status or "").strip()
	if value in (PLAN_CLOSED, PLAN_CANCELLED, PLAN_SUPERSEDED):
		return "archive"
	return "open"


def _plan_row(row: dict[str, Any]) -> dict[str, Any]:
	plan_code = (row.get("plan_code") or row.get("name") or "").strip()
	title = (row.get("plan_name") or plan_code).strip()
	fiscal_year = _fiscal_year_label(row.get("fiscal_year"))
	status = (row.get("status") or "").strip()
	is_active = cint(row.get("is_active"))
	demands, packages, released = _plan_counts(plan_code)
	return {
		"plan_id": plan_code,
		"plan_code": plan_code,
		"title": title,
		"fiscal_year": fiscal_year,
		"status_label": _status_label(status, is_active=is_active),
		"demands_count": demands,
		"packages_count": packages,
		"released_count": released,
		"counts_label": _counts_label(
			demands=demands,
			packages=packages,
			released=released,
		),
		"is_active_plan": status == PLAN_ACTIVE and is_active == 1,
	}


def _hub_ledger_row(row: dict[str, Any]) -> dict[str, Any]:
	"""Hub ledger row with reference entity, value, badge tone, and row action."""
	base = _plan_row(row)
	plan_code = (base.get("plan_code") or "").strip()
	entity_code = (row.get("procuring_entity") or "").strip()
	status = (row.get("status") or "").strip()
	is_active = cint(row.get("is_active"))
	currency = (row.get("currency") or "KES").strip() or "KES"
	total_value = flt(row.get("total_planned_value") or 0)
	row_action = _row_action(status, is_active=is_active)
	return {
		**base,
		"id": plan_code,
		"code": plan_code,
		"name": base.get("title") or plan_code,
		"entity": _entity_ref(entity_code),
		"entity_name": _entity_label(entity_code),
		"status_tone": _status_tone(status, is_active=is_active),
		"currency": currency,
		"total_value": total_value,
		"row_action": row_action,
		"is_archived": row_action == "archive",
	}


def _fetch_scoped_plan_rows(*, actor: str) -> list[dict[str, Any]]:
	user = _session_user(actor)
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return []
	try:
		rows = frappe.get_list(
			"Procurement Plan",
			fields=[
				"name",
				"plan_code",
				"plan_name",
				"fiscal_year",
				"procuring_entity",
				"status",
				"is_active",
				"currency",
				"total_planned_value",
			],
			order_by="is_active desc, modified desc",
			limit_page_length=500,
		)
	except frappe.PermissionError:
		return []
	out: list[dict[str, Any]] = []
	for row in rows:
		entity = (row.get("procuring_entity") or "").strip()
		if not pp_scope.entity_in_user_scope(entity, user):
			continue
		out.append(row)
	return out


def get_planning_hub_plans_page(
	*,
	actor: str | None = None,
	search: str | None = None,
	start: int = 0,
	limit: int = 20,
) -> dict[str, Any]:
	"""Return paginated hub ledger rows for the Planning Hub."""
	user = _session_user(actor)
	role_key = resolve_pp_role_key(user) or "auditor"
	rows = [_hub_ledger_row(row) for row in _fetch_scoped_plan_rows(actor=user)]
	query = (search or "").strip().lower()
	if query:
		filtered: list[dict[str, Any]] = []
		for row in rows:
			blob = " ".join(
				[
					str(row.get("name") or ""),
					str(row.get("code") or ""),
					str((row.get("entity") or {}).get("name") or ""),
					str(row.get("fiscal_year") or ""),
					str(row.get("status_label") or ""),
				]
			).lower()
			if query in blob:
				filtered.append(row)
		rows = filtered
	total = len(rows)
	start_i = max(int(start or 0), 0)
	limit_i = max(int(limit or 20), 1)
	page_rows = rows[start_i : start_i + limit_i]
	return {
		"ok": True,
		"role_key": role_key,
		"total": total,
		"start": start_i,
		"limit": limit_i,
		"rows": page_rows,
	}


def get_procurement_plans_list_view_model(*, actor: str | None = None) -> dict[str, Any]:
	"""Return PP3 Procurement Plans list envelope (P4-002)."""
	user = _session_user(actor)
	role_key = resolve_pp_role_key(user) or "auditor"
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return {"ok": True, "role_key": role_key, "plans": []}
	try:
		rows = frappe.get_list(
			"Procurement Plan",
			fields=[
				"name",
				"plan_code",
				"plan_name",
				"fiscal_year",
				"procuring_entity",
				"status",
				"is_active",
			],
			order_by="is_active desc, modified desc",
			limit_page_length=200,
		)
	except frappe.PermissionError:
		return {"ok": True, "role_key": role_key, "plans": []}

	plans: list[dict[str, Any]] = []
	for row in rows:
		entity = (row.get("procuring_entity") or "").strip()
		if not pp_scope.entity_in_user_scope(entity, user):
			continue
		plans.append(_plan_row(row))
	return {"ok": True, "role_key": role_key, "plans": plans}


def get_procurement_plan_summary_view_model(
	*,
	plan_id: str | None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Return PP3 selected plan summary envelope (P4-003)."""
	user = _session_user(actor)
	role_key = resolve_pp_role_key(user) or "auditor"
	code = (plan_id or "").strip()
	if not code:
		return {
			"ok": False,
			"error_code": "MISSING_PLAN",
			"message": "Select a procurement plan to view its summary.",
			"role_key": role_key,
		}
	if not frappe.db.exists("Procurement Plan", code):
		return {
			"ok": False,
			"error_code": "PLAN_NOT_FOUND",
			"message": "Procurement plan could not be found.",
			"role_key": role_key,
		}
	doc = frappe.get_doc("Procurement Plan", code)
	entity = (doc.procuring_entity or "").strip()
	if not pp_scope.entity_in_user_scope(entity, user):
		return {
			"ok": False,
			"error_code": "PP_ACCESS_DENIED",
			"message": "You do not have access to this procurement plan.",
			"role_key": role_key,
		}
	row = _plan_row(
		{
			"name": doc.name,
			"plan_code": doc.plan_code,
			"plan_name": doc.plan_name,
			"fiscal_year": doc.fiscal_year,
			"status": doc.status,
			"is_active": doc.is_active,
		}
	)
	blockers_count = _plan_blockers_count(code, actor=user)
	flags = _plan_workbench_action_flags(role_key, {"status": doc.status})
	return {
		"ok": True,
		"role_key": role_key,
		"plan_id": code,
		"title": row.get("title"),
		"status_label": row.get("status_label"),
		"fiscal_year": row.get("fiscal_year"),
		"demands_count": row.get("demands_count"),
		"packages_count": row.get("packages_count"),
		"released_count": row.get("released_count"),
		"blockers_count": blockers_count,
		"blockers_label": _blockers_label(blockers_count),
		"is_active_plan": row.get("is_active_plan"),
		"show_activate_plan": bool(flags.get("show_activate_plan")),
		"show_close_plan": bool(flags.get("show_close_plan")),
		"show_open_in_workbench": True,
		"show_view_evidence": True,
	}
