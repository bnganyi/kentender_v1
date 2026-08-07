# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-002 — Planning Home summary counts (reset addendum §7.2).

Count semantics align with future P5C-003..007 home queue sections:
- needs_planning: approved demands eligible for planning inclusion
- needs_review: active packages in In Review
- ready_to_release: active packages Ready for Release
- released_recently: packages released/consumed within the recent window
- blocked: scoped demands/packages with planning blockers (budget/eligibility/readiness)
"""

from __future__ import annotations

from typing import Any

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.utils import add_days, getdate, nowdate

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_IN_REVIEW,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PKG_RETURNED,
	READINESS_FAILED,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_base_demand_filters,
	_demand_passes_queue_eligibility,
	get_approved_demands_awaiting_planning,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	ALLOWED_DEMAND_STATUSES,
	_demand_budget_ok,
	demand_has_unpackaged_planning_inclusion,
)

PLANNING_HOME_SUMMARY_KEYS = (
	"needs_planning",
	"needs_review",
	"ready_to_release",
	"released_recently",
	"blocked",
)

RELEASED_RECENTLY_DAYS = 90

_QUEUE_DEMAND_FIELDS = [
	"name",
	"demand_id",
	"title",
	"status",
	"planning_status",
	"procuring_entity",
	"budget_line",
	"total_amount",
]


def _empty_summary() -> dict[str, int]:
	return {key: 0 for key in PLANNING_HOME_SUMMARY_KEYS}


def _count_scoped_packages(actor: str, filters: dict[str, Any]) -> int:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return 0
	clauses = dict(filters or {})
	clauses.setdefault("is_active", 1)
	try:
		rows = frappe.get_all(
			"Procurement Package",
			filters=clauses,
			pluck="name",
			limit=0,
		)
	except frappe.PermissionError:
		return 0
	count = 0
	for name in rows or []:
		entity = frappe.db.get_value("Procurement Package", name, "procuring_entity_code") or ""
		if pp_scope.entity_in_user_scope(entity, actor):
			count += 1
	return count


def _count_needs_planning(actor: str) -> int:
	out = get_approved_demands_awaiting_planning({}, actor)
	if not out.get("ok"):
		return 0
	return int(out.get("total") or 0)


def _count_needs_review(actor: str) -> int:
	return _count_scoped_packages(actor, {"status": PKG_IN_REVIEW})


def _count_ready_to_release(actor: str) -> int:
	return _count_scoped_packages(actor, {"status": PKG_READY_FOR_RELEASE})


def _count_released_recently(actor: str) -> int:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return 0
	cutoff = add_days(nowdate(), -RELEASED_RECENTLY_DAYS)
	rows = frappe.get_all(
		"Procurement Package",
		filters={
			"is_active": 1,
			"status": ("in", [PKG_RELEASED, PKG_CONSUMED]),
		},
		fields=["name", "procuring_entity_code", "released_to_tender_at", "modified"],
		limit_page_length=5000,
	)
	count = 0
	for row in rows or []:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity_code"), actor):
			continue
		released_at = row.get("released_to_tender_at") or row.get("modified")
		if not released_at:
			continue
		if getdate(released_at) >= getdate(cutoff):
			count += 1
	return count


def _count_blocked_demands(actor: str) -> int:
	if not demand_consumers_live():
		return 0
	clauses = _base_demand_filters({})
	allowed_entities = pp_scope.get_user_allowed_entities(actor)
	if allowed_entities is not None and not allowed_entities:
		return 0
	if allowed_entities is not None:
		clauses.append(["procuring_entity", "in", sorted(allowed_entities)])

	rows = frappe.get_all(
		"Demand",
		filters=clauses,
		fields=_QUEUE_DEMAND_FIELDS,
		limit_page_length=5000,
	)
	count = 0
	for row in rows or []:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity"), actor):
			continue
		status = (row.get("status") or "").strip()
		if status not in ALLOWED_DEMAND_STATUSES:
			continue
		if _demand_passes_queue_eligibility(row):
			continue
		demand_code = (row.get("demand_id") or row.get("name") or "").strip()
		if demand_has_unpackaged_planning_inclusion(demand_code):
			continue
		if not _demand_budget_ok(row):
			count += 1
			continue
		planning_status = (row.get("planning_status") or "").strip()
		if planning_status != "Fully Planned":
			count += 1
	return count


def _count_blocked_packages(actor: str) -> int:
	blocked_statuses = (READINESS_FAILED, "Blocked")
	count = _count_scoped_packages(actor, {"readiness_status": ("in", list(blocked_statuses))})
	count += _count_scoped_packages(actor, {"status": PKG_RETURNED})
	return count


def _count_blocked(actor: str) -> int:
	return _count_blocked_demands(actor) + _count_blocked_packages(actor)


def get_planning_home_summary(actor: str | None = None) -> dict[str, Any]:
	"""Return Planning Home summary counts for the reset dashboard."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"

	if not frappe.db.exists("DocType", "Procurement Plan"):
		return {
			"ok": False,
			"error_code": "PP_NOT_INSTALLED",
			"message": "Procurement Planning is not installed on this site.",
			"role_key": role_key,
			"summary": _empty_summary(),
		}

	summary = {
		"needs_planning": _count_needs_planning(actor),
		"needs_review": _count_needs_review(actor),
		"ready_to_release": _count_ready_to_release(actor),
		"released_recently": _count_released_recently(actor),
		"blocked": _count_blocked(actor),
	}
	for key in PLANNING_HOME_SUMMARY_KEYS:
		summary[key] = max(int(summary.get(key) or 0), 0)

	return {
		"ok": True,
		"role_key": role_key,
		"summary": summary,
	}
