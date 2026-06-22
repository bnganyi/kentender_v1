# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-003 / P5C-004 / P5C-005 / P5C-006 / P5C-007 — Planning Home queue slices."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, cint, flt, fmt_money, getdate, nowdate

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_IN_REVIEW,
	PKG_READY_FOR_RELEASE,
	PKG_RETURNED,
	PKG_RELEASED,
	READINESS_FAILED,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_base_demand_filters,
	_demand_passes_queue_eligibility,
	get_approved_demands_awaiting_planning,
)
from kentender_procurement.procurement_planning.services.planning_home_summary import (
	_count_blocked,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	ALLOWED_DEMAND_STATUSES,
	_demand_budget_ok,
)
from kentender_procurement.procurement_planning.services.package_workbench import (
	get_package_workbench_rows,
)

PLANNING_HOME_QUEUE_LIMIT = 5
NEEDS_PLANNING_HOME_LIMIT = PLANNING_HOME_QUEUE_LIMIT
NEEDS_PLANNING_VIEW_ALL_HREF = "/desk/procurement-planning?queue=needs-planning"
NEEDS_REVIEW_VIEW_ALL_HREF = "/desk/procurement-planning?queue=needs-review"
READY_RELEASE_VIEW_ALL_HREF = "/desk/procurement-planning?queue=ready-to-release"
RELEASED_RECENTLY_VIEW_ALL_HREF = "/desk/procurement-planning?queue=released-recently"
BLOCKED_VIEW_ALL_HREF = "/desk/procurement-planning?queue=blocked"
RELEASED_RECENTLY_DAYS = 90
_BLOCKED_PACKAGE_READINESS_STATUSES = (READINESS_FAILED, "Blocked")


def _funding_label(budget_line: dict[str, Any] | None) -> str:
	bl = budget_line or {}
	if (bl.get("id") or bl.get("code") or "").strip():
		return frappe._("Budget linked")
	return ""


def _format_value_display(value: Any, currency: str) -> str:
	cur = (currency or "KES").strip() or "KES"
	amount = flt(value)
	if amount:
		return fmt_money(amount, currency=cur)
	return fmt_money(0, currency=cur)


def _build_subtitle(*, category: str, value_display: str, currency: str, funding_label: str) -> str:
	parts: list[str] = []
	cat = (category or "").strip()
	if cat:
		parts.append(cat)
	value_part = (value_display or "").strip()
	cur = (currency or "KES").strip() or "KES"
	if value_part:
		if cur and cur not in value_part:
			parts.append(f"{value_part} {cur}")
		else:
			parts.append(value_part)
	funding = (funding_label or "").strip()
	if funding:
		parts.append(funding)
	return " · ".join(parts)


def format_needs_planning_work_item(row: dict[str, Any]) -> dict[str, Any]:
	"""Map approved-demand queue row to Planning Home work-item view model (§7.1)."""
	demand = row.get("demand") or {}
	demand_id = (demand.get("id") or "").strip()
	title = (demand.get("name") or demand.get("code") or demand_id).strip()
	currency = (row.get("currency") or "KES").strip() or "KES"
	value_display = _format_value_display(row.get("estimated_value"), currency)
	funding = _funding_label(row.get("budget_line"))
	subtitle = _build_subtitle(
		category=(row.get("category") or "").strip(),
		value_display=value_display,
		currency=currency,
		funding_label=funding,
	)
	return {
		"id": demand_id,
		"title": title,
		"subtitle": subtitle,
		"next_action_label": frappe._("Include in procurement plan"),
		"primary_action": {
			"label": frappe._("Open"),
			"action": "open_demand",
			"target": demand_id,
		},
	}


def _build_package_subtitle(*, category: str, method: str, value_display: str, currency: str) -> str:
	parts: list[str] = []
	cat = (category or "").strip()
	if cat:
		parts.append(cat)
	meth = (method or "").strip()
	if meth:
		parts.append(meth)
	value_part = (value_display or "").strip()
	cur = (currency or "KES").strip() or "KES"
	if value_part:
		if cur and cur not in value_part:
			parts.append(f"{value_part} {cur}")
		else:
			parts.append(value_part)
	return " · ".join(parts)


def format_needs_review_work_item(row: dict[str, Any]) -> dict[str, Any]:
	"""Map package workbench row to Planning Home work-item view model (§7.1)."""
	package = row.get("package") or {}
	package_id = (package.get("id") or "").strip()
	title = (package.get("name") or package.get("code") or package_id).strip()
	currency = (row.get("currency") or "KES").strip() or "KES"
	value_display = _format_value_display(row.get("estimated_value"), currency)
	subtitle = _build_package_subtitle(
		category=(row.get("category") or "").strip(),
		method=(row.get("method") or "").strip(),
		value_display=value_display,
		currency=currency,
	)
	return {
		"id": package_id,
		"title": title,
		"subtitle": subtitle,
		"next_action_label": frappe._("Review package"),
		"primary_action": {
			"label": frappe._("Open"),
			"action": "open_package",
			"target": package_id,
		},
	}


def format_ready_to_release_work_item(row: dict[str, Any]) -> dict[str, Any]:
	"""Map ready-to-release package row to Planning Home work-item view model (§7.1)."""
	package = row.get("package") or {}
	package_id = (package.get("id") or "").strip()
	title = (package.get("name") or package.get("code") or package_id).strip()
	currency = (row.get("currency") or "KES").strip() or "KES"
	value_display = _format_value_display(row.get("estimated_value"), currency)
	subtitle = _build_package_subtitle(
		category=(row.get("category") or "").strip(),
		method=(row.get("method") or "").strip(),
		value_display=value_display,
		currency=currency,
	)
	return {
		"id": package_id,
		"title": title,
		"subtitle": subtitle,
		"next_action_label": frappe._("Release package"),
		"primary_action": {
			"label": frappe._("Open"),
			"action": "open_package",
			"target": package_id,
		},
	}


def format_released_recently_work_item(row: dict[str, Any]) -> dict[str, Any]:
	"""Map released/consumed package row to Planning Home work-item view model."""
	package = row.get("package") or {}
	package_id = (package.get("id") or "").strip()
	title = (package.get("name") or package.get("code") or package_id).strip()
	status = (row.get("status") or "").strip()
	if status == PKG_CONSUMED:
		subtitle = frappe._("Released to Tender Management · Tender created")
	else:
		subtitle = frappe._("Released to Tender Management")
	tender = row.get("tender") or {}
	tender_target = (tender.get("code") or tender.get("id") or package_id).strip()
	return {
		"id": package_id,
		"title": title,
		"subtitle": subtitle,
		"next_action_label": frappe._("Continue in Tender Management"),
		"primary_action": {
			"label": frappe._("Open Tender"),
			"action": "open_tender",
			"target": tender_target,
		},
		"secondary_actions": [
			{
				"label": frappe._("View Package"),
				"action": "open_package",
				"target": package_id,
			}
		],
	}


def _format_blocked_subtitle(*, category: str, method: str, value_display: str, currency: str, blocker: str) -> str:
	base = _build_package_subtitle(
		category=category,
		method=method,
		value_display=value_display,
		currency=currency,
	)
	parts = [p for p in [base, (blocker or "").strip()] if p]
	return " · ".join(parts)


def format_blocked_work_item(row: dict[str, Any]) -> dict[str, Any]:
	"""Map blocked demand/package row to Planning Home work-item view model."""
	blocked_type = (row.get("blocked_type") or "").strip()
	demand = row.get("demand") or {}
	package = row.get("package") or {}
	is_demand = blocked_type == "demand"
	ref = demand if is_demand else package
	ref_id = (ref.get("id") or "").strip()
	title = (ref.get("name") or ref.get("code") or ref_id).strip()
	currency = (row.get("currency") or "KES").strip() or "KES"
	value_display = _format_value_display(row.get("estimated_value"), currency)
	subtitle = _format_blocked_subtitle(
		category=(row.get("category") or "").strip(),
		method=(row.get("method") or "").strip(),
		value_display=value_display,
		currency=currency,
		blocker=(row.get("blocker_message") or "").strip(),
	)
	return {
		"id": ref_id,
		"title": title,
		"subtitle": subtitle,
		"next_action_label": frappe._("Resolve blocker"),
		"primary_action": {
			"label": frappe._("Resolve blocker"),
			"action": "open_demand" if is_demand else "open_package",
			"target": ref_id,
		},
	}


def _queue_error_envelope(
	*,
	ok: bool,
	role_key: str,
	queue_key: str,
	limit: int,
	view_all_href: str,
	error_code: str | None = None,
	message: str | None = None,
	total: int = 0,
	items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	out: dict[str, Any] = {
		"ok": ok,
		"role_key": role_key,
		"queue_key": queue_key,
		"total": max(int(total or 0), 0),
		"limit": limit,
		"items": items or [],
		"view_all_href": view_all_href,
	}
	if error_code:
		out["error_code"] = error_code
	if message:
		out["message"] = message
	return out


def get_needs_review_home_queue(actor: str | None = None) -> dict[str, Any]:
	"""Return Needs Review home queue slice (max five items)."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	limit = PLANNING_HOME_QUEUE_LIMIT

	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _queue_error_envelope(
			ok=False,
			role_key=role_key,
			queue_key="needs_review",
			limit=limit,
			view_all_href=NEEDS_REVIEW_VIEW_ALL_HREF,
			error_code="PP_NOT_INSTALLED",
			message=frappe._("Procurement Planning is not installed on this site."),
		)

	queue_out = get_package_workbench_rows(
		{"status": PKG_IN_REVIEW, "limit": limit, "start": 0},
		actor,
	)
	if not queue_out.get("ok"):
		return _queue_error_envelope(
			ok=False,
			role_key=queue_out.get("role_key") or role_key,
			queue_key="needs_review",
			limit=limit,
			view_all_href=NEEDS_REVIEW_VIEW_ALL_HREF,
			error_code=queue_out.get("error_code") or "PP_QUEUE_ERROR",
			message=queue_out.get("message") or frappe._("Unable to load Needs Review queue."),
		)

	rows = queue_out.get("rows") or []
	total = cint(queue_out.get("total") or 0)
	items = [format_needs_review_work_item(row) for row in rows if row]

	return _queue_error_envelope(
		ok=True,
		role_key=queue_out.get("role_key") or role_key,
		queue_key="needs_review",
		limit=limit,
		view_all_href=NEEDS_REVIEW_VIEW_ALL_HREF,
		total=total,
		items=items,
	)


def _released_recently_rows(actor: str, *, limit: int) -> tuple[list[dict[str, Any]], int]:
	cutoff = add_days(nowdate(), -RELEASED_RECENTLY_DAYS)
	pkgs = frappe.get_all(
		"Procurement Package",
		filters={
			"is_active": 1,
			"status": ("in", [PKG_RELEASED, PKG_CONSUMED]),
		},
		fields=[
			"name",
			"package_code",
			"package_name",
			"status",
			"tender_code",
			"procuring_entity_code",
			"released_to_tender_at",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=5000,
	)
	filtered: list[dict[str, Any]] = []
	for row in pkgs or []:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity_code"), actor):
			continue
		released_at = row.get("released_to_tender_at") or row.get("modified")
		if not released_at:
			continue
		if getdate(released_at) < getdate(cutoff):
			continue
		package_code = (row.get("package_code") or row.get("name") or "").strip()
		tender_code = (row.get("tender_code") or "").strip()
		filtered.append(
			{
				"status": (row.get("status") or "").strip(),
				"package": {
					"id": (row.get("name") or "").strip(),
					"code": package_code,
					"name": (row.get("package_name") or package_code).strip(),
				},
				"tender": (
					{
						"id": tender_code,
						"code": tender_code,
						"name": tender_code,
					}
					if tender_code
					else {}
				),
			}
		)
	total = len(filtered)
	return filtered[:limit], total


def _blocked_demand_rows(actor: str) -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Demand"):
		return []
	clauses = _base_demand_filters({})
	allowed_entities = pp_scope.get_user_allowed_entities(actor)
	if allowed_entities is not None and not allowed_entities:
		return []
	if allowed_entities is not None:
		clauses.append(["procuring_entity", "in", sorted(allowed_entities)])
	rows = frappe.get_all(
		"Demand",
		filters=clauses,
		fields=[
			"name",
			"demand_id",
			"title",
			"status",
			"planning_status",
			"procuring_entity",
			"budget_line",
			"total_amount",
			"requisition_type",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=5000,
	)
	out: list[dict[str, Any]] = []
	for row in rows or []:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity"), actor):
			continue
		status = (row.get("status") or "").strip()
		if status not in ALLOWED_DEMAND_STATUSES:
			continue
		if _demand_passes_queue_eligibility(row):
			continue
		planning_status = (row.get("planning_status") or "").strip()
		if not _demand_budget_ok(row):
			blocker = frappe._("Missing approved budget link")
		elif planning_status != "Fully Planned":
			blocker = frappe._("Demand is not fully planned")
		else:
			blocker = frappe._("Demand has planning blockers")
		demand_id = (row.get("name") or "").strip()
		demand_code = (row.get("demand_id") or demand_id).strip()
		out.append(
			{
				"blocked_type": "demand",
				"demand": {
					"id": demand_id,
					"code": demand_code,
					"name": (row.get("title") or demand_code).strip(),
				},
				"category": (row.get("requisition_type") or "").strip(),
				"estimated_value": flt(row.get("total_amount")),
				"currency": "KES",
				"blocker_message": blocker,
				"modified": row.get("modified"),
			}
		)
	return out


def _blocked_package_rows(actor: str) -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return []
	rows = frappe.get_all(
		"Procurement Package",
		filters={"is_active": 1},
		fields=[
			"name",
			"package_code",
			"package_name",
			"status",
			"readiness_status",
			"procurement_category",
			"procurement_method",
			"estimated_value",
			"currency",
			"procuring_entity_code",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=5000,
	)
	out: list[dict[str, Any]] = []
	for row in rows or []:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity_code"), actor):
			continue
		status = (row.get("status") or "").strip()
		readiness_status = (row.get("readiness_status") or "").strip()
		is_blocked = status == PKG_RETURNED or readiness_status in _BLOCKED_PACKAGE_READINESS_STATUSES
		if not is_blocked:
			continue
		if status == PKG_RETURNED:
			blocker = frappe._("Returned for correction")
		elif readiness_status in _BLOCKED_PACKAGE_READINESS_STATUSES:
			blocker = frappe._("Readiness checks failed")
		else:
			blocker = frappe._("Package has planning blockers")
		package_id = (row.get("name") or "").strip()
		package_code = (row.get("package_code") or package_id).strip()
		out.append(
			{
				"blocked_type": "package",
				"package": {
					"id": package_id,
					"code": package_code,
					"name": (row.get("package_name") or package_code).strip(),
				},
				"category": (row.get("procurement_category") or "").strip(),
				"method": (row.get("procurement_method") or "").strip(),
				"estimated_value": flt(row.get("estimated_value")),
				"currency": (row.get("currency") or "KES").strip() or "KES",
				"blocker_message": blocker,
				"modified": row.get("modified"),
			}
		)
	return out


def _blocked_rows(actor: str, *, limit: int) -> tuple[list[dict[str, Any]], int]:
	merged = _blocked_demand_rows(actor) + _blocked_package_rows(actor)
	merged.sort(key=lambda row: str(row.get("modified") or ""), reverse=True)
	return merged[:limit], _count_blocked(actor)


def get_blocked_home_queue(actor: str | None = None) -> dict[str, Any]:
	"""Return Blocked home queue slice (max five items)."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	limit = PLANNING_HOME_QUEUE_LIMIT

	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _queue_error_envelope(
			ok=False,
			role_key=role_key,
			queue_key="blocked",
			limit=limit,
			view_all_href=BLOCKED_VIEW_ALL_HREF,
			error_code="PP_NOT_INSTALLED",
			message=frappe._("Procurement Planning is not installed on this site."),
		)

	rows, total = _blocked_rows(actor, limit=limit)
	items = [format_blocked_work_item(row) for row in rows if row]
	return _queue_error_envelope(
		ok=True,
		role_key=role_key,
		queue_key="blocked",
		limit=limit,
		view_all_href=BLOCKED_VIEW_ALL_HREF,
		total=total,
		items=items,
	)


def get_released_recently_home_queue(actor: str | None = None) -> dict[str, Any]:
	"""Return Released Recently home queue slice (max five items)."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	limit = PLANNING_HOME_QUEUE_LIMIT

	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _queue_error_envelope(
			ok=False,
			role_key=role_key,
			queue_key="released_recently",
			limit=limit,
			view_all_href=RELEASED_RECENTLY_VIEW_ALL_HREF,
			error_code="PP_NOT_INSTALLED",
			message=frappe._("Procurement Planning is not installed on this site."),
		)

	rows, total = _released_recently_rows(actor, limit=limit)
	items = [format_released_recently_work_item(row) for row in rows if row]
	return _queue_error_envelope(
		ok=True,
		role_key=role_key,
		queue_key="released_recently",
		limit=limit,
		view_all_href=RELEASED_RECENTLY_VIEW_ALL_HREF,
		total=total,
		items=items,
	)


def get_needs_planning_home_queue(actor: str | None = None) -> dict[str, Any]:
	"""Return Needs Planning home queue slice (max five items)."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	limit = NEEDS_PLANNING_HOME_LIMIT

	if not frappe.db.exists("DocType", "Procurement Plan"):
		return {
			"ok": False,
			"error_code": "PP_NOT_INSTALLED",
			"message": frappe._("Procurement Planning is not installed on this site."),
			"role_key": role_key,
			"queue_key": "needs_planning",
			"total": 0,
			"limit": limit,
			"items": [],
			"view_all_href": NEEDS_PLANNING_VIEW_ALL_HREF,
		}

	queue_out = get_approved_demands_awaiting_planning(
		{"limit": limit, "start": 0},
		actor,
	)
	if not queue_out.get("ok"):
		return {
			"ok": False,
			"error_code": queue_out.get("error_code") or "PP_QUEUE_ERROR",
			"message": queue_out.get("message") or frappe._("Unable to load Needs Planning queue."),
			"role_key": queue_out.get("role_key") or role_key,
			"queue_key": "needs_planning",
			"total": 0,
			"limit": limit,
			"items": [],
			"view_all_href": NEEDS_PLANNING_VIEW_ALL_HREF,
		}

	rows = queue_out.get("rows") or []
	total = cint(queue_out.get("total") or 0)
	items = [format_needs_planning_work_item(row) for row in rows if row]

	return {
		"ok": True,
		"role_key": queue_out.get("role_key") or role_key,
		"queue_key": "needs_planning",
		"total": max(total, 0),
		"limit": limit,
		"items": items,
		"view_all_href": NEEDS_PLANNING_VIEW_ALL_HREF,
	}


def get_ready_to_release_home_queue(actor: str | None = None) -> dict[str, Any]:
	"""Return Ready to Release home queue slice (max five items)."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	limit = PLANNING_HOME_QUEUE_LIMIT

	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _queue_error_envelope(
			ok=False,
			role_key=role_key,
			queue_key="ready_to_release",
			limit=limit,
			view_all_href=READY_RELEASE_VIEW_ALL_HREF,
			error_code="PP_NOT_INSTALLED",
			message=frappe._("Procurement Planning is not installed on this site."),
		)

	queue_out = get_package_workbench_rows(
		{"status": PKG_READY_FOR_RELEASE, "limit": limit, "start": 0},
		actor,
	)
	if not queue_out.get("ok"):
		return _queue_error_envelope(
			ok=False,
			role_key=queue_out.get("role_key") or role_key,
			queue_key="ready_to_release",
			limit=limit,
			view_all_href=READY_RELEASE_VIEW_ALL_HREF,
			error_code=queue_out.get("error_code") or "PP_QUEUE_ERROR",
			message=queue_out.get("message") or frappe._("Unable to load Ready to Release queue."),
		)

	rows = queue_out.get("rows") or []
	total = cint(queue_out.get("total") or 0)
	items = [format_ready_to_release_work_item(row) for row in rows if row]

	return _queue_error_envelope(
		ok=True,
		role_key=queue_out.get("role_key") or role_key,
		queue_key="ready_to_release",
		limit=limit,
		view_all_href=READY_RELEASE_VIEW_ALL_HREF,
		total=total,
		items=items,
	)
