# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-002 — Unified Workbench item view-model adapter."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import cint, flt, fmt_money, pretty_date

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.services.workbench_demo_scope import (
	filter_demo_workbench_items,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_READY_FOR_RELEASE,
)
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	get_active_plan_view_model,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
)
from kentender_procurement.procurement_planning.services.package_workbench import (
	get_package_workbench_rows,
)
from kentender_procurement.procurement_planning.services.planning_home_queues import (
	_blocked_rows,
	_released_recently_rows,
)

SUPPORTED_QUEUES = frozenset(
	(
		"needs_planning",
		"draft_packages",
		"needs_review",
		"ready_release",
		"blocked",
		"recently_released",
	)
)

_QUEUE_STATE_LABELS = {
	"needs_planning": "Needs planning",
	"draft_packages": "Draft package",
	"needs_review": "Needs review",
	"ready_release": "Ready to release",
	"blocked": "Blocked",
	"recently_released": "Released recently",
}

_PACKAGE_ACTION_MAP = {
	"complete_package": ("Complete Package", "complete_package"),
	"review_package": ("Review Package", "review_package"),
	"mark_ready_for_release": ("Mark Ready for Release", "mark_ready_for_release"),
	"release_to_tender": ("Release to Tender", "release_to_tender"),
	"view_release": ("View Release", "view_release"),
	"view_tender": ("View Tender", "view_tender"),
	"open_package": ("Open Package", "open_package"),
}


def _session_user(actor: str | None) -> str:
	return (actor or frappe.session.user or "").strip() or frappe.session.user


def _money(value: Any, currency: str) -> str:
	cur = (currency or "KES").strip() or "KES"
	formatted = fmt_money(flt(value or 0), currency=cur)
	if cur == "KES":
		cleaned = re.sub(r"^(Ksh\.?|Sh\.?|KES\.?)\s*", "", str(formatted)).strip()
		return f"KES {cleaned}"
	return formatted


def _apply_demo_scope(
	items: list[dict[str, Any]],
	*,
	include_test_data: bool,
) -> tuple[list[dict[str, Any]], int]:
	filtered = filter_demo_workbench_items(items, include_test_data=include_test_data)
	return filtered, len(filtered)


def _relative_label(raw: Any) -> str:
	text = str(raw or "").strip()
	if not text:
		return ""
	try:
		label = str(pretty_date(text, mini=True) or "").strip()
	except Exception:
		label = ""
	return f"Updated {label}" if label else ""


def _active_plan_label(actor: str) -> str:
	vm = get_active_plan_view_model(actor=actor)
	if not vm.get("has_active_plan"):
		return ""
	title = str(vm.get("plan_title") or "").strip()
	code = str(vm.get("plan_code") or "").strip()
	if title and code:
		return f"{title} ({code})"
	return title or code


def _work_item_base(*, queue: str, code: str, title: str, subtitle: str, object_type: str, plan_label: str) -> dict[str, Any]:
	return {
		"work_item_id": f"{queue}:{code}",
		"title": title,
		"subtitle": subtitle,
		"state_label": _QUEUE_STATE_LABELS.get(queue, queue.replace("_", " ").title()),
		"queue": queue,
		"underlying_object_type": object_type,
		"underlying_object_code": code,
		"active_plan_label": plan_label,
		"technical_hidden_by_default": True,
	}


def _needs_planning_items(rows: list[dict[str, Any]], plan_label: str) -> list[dict[str, Any]]:
	items: list[dict[str, Any]] = []
	for row in rows:
		demand = row.get("demand") or {}
		code = str(demand.get("code") or "").strip()
		if not code:
			continue
		title = str(demand.get("name") or code).strip()
		category = str(row.get("category") or "").strip()
		value = _money(row.get("estimated_value"), row.get("currency") or "KES")
		funding = "Budget linked" if str((row.get("budget_line") or {}).get("id") or "").strip() else ""
		meta_line = " · ".join([s for s in (value,) if s])
		subtitle = " · ".join([s for s in (category, value, funding) if s])
		status_detail = (
			"Funding is linked. No blockers found."
			if funding
			else "Budget link is required before planning."
		)
		entry = _work_item_base(
			queue="needs_planning",
			code=code,
			title=title,
			subtitle=subtitle,
			object_type="approved_demand",
			plan_label=plan_label,
		)
		entry.update(
			{
				"category_label": category,
				"meta_line": meta_line,
				"budget_status": funding,
				"budget_status_label": funding,
				"status_pill_label": "Planning pending",
				"status_pill_tone": "demand",
				"updated_relative": _relative_label(row.get("approval_date") or row.get("modified")),
				"summary_detail_line": " · ".join(
					[s for s in ("Approved demand", category, value) if s]
				),
				"status_headline": "Ready to plan",
				"status_detail": status_detail,
				"next_step_detail": "Add this demand to the active procurement plan.",
				"list_next_action": "Add to active plan",
				"blockers": [],
				"next_action_label": "Add to Active Plan",
				"primary_action": {
					"label": "Add to Active Plan",
					"action": "include_in_plan",
					"target": code,
				},
				"secondary_actions": [{"label": "View Demand", "action": "view_demand", "target": code}],
			}
		)
		items.append(entry)
	return items


def _package_queue_items(rows: list[dict[str, Any]], queue: str, plan_label: str) -> list[dict[str, Any]]:
	items: list[dict[str, Any]] = []
	for row in rows:
		pkg = row.get("package") or {}
		code = str(pkg.get("code") or "").strip()
		if not code:
			continue
		title = str(pkg.get("name") or code).strip()
		package_description = str(pkg.get("description") or "").strip()
		category = str(row.get("category") or "").strip()
		method = str(row.get("method") or "").strip()
		value = _money(row.get("estimated_value"), row.get("currency") or "KES")
		subtitle = " · ".join([s for s in (category, method, value) if s])
		entry = _work_item_base(
			queue=queue,
			code=code,
			title=title,
			subtitle=subtitle,
			object_type="procurement_package",
			plan_label=plan_label,
		)
		next_action = row.get("next_action") or {}
		action_key = str(next_action.get("key") or "open_package").strip()
		label, action = _PACKAGE_ACTION_MAP.get(action_key, _PACKAGE_ACTION_MAP["open_package"])
		meta_line = " · ".join([s for s in (method, value) if s])
		status_detail = package_description or f"Next package action: {label}."
		entry.update(
			{
				"category_label": category,
				"meta_line": meta_line,
				"budget_status": "",
				"budget_status_label": "",
				"status_pill_label": str(row.get("status") or entry["state_label"]).strip(),
				"status_pill_tone": "package",
				"updated_relative": _relative_label(row.get("modified") or row.get("updated_at")),
				"summary_detail_line": " · ".join(
					[s for s in ("Procurement package", category, method, value) if s]
				),
				"status_headline": str(row.get("status") or entry["state_label"]).strip(),
				"status_detail": status_detail,
				"package_description": package_description,
				"next_step_detail": f"{label} to move this package forward.",
				"list_next_action": label,
				"state_label": str(row.get("status") or entry["state_label"]).strip(),
				"blockers": [],
				"next_action_label": label,
				"primary_action": {"label": label, "action": action, "target": code},
				"secondary_actions": [{"label": "View Package", "action": "view_package", "target": code}],
				"consolidated_demand_count": cint(row.get("consolidated_demand_count") or 0),
				"department_label": str(
					row.get("procuring_entity_label")
					or row.get("procuring_entity_code")
					or "",
				).strip(),
				"created_on": str(row.get("created_on") or row.get("updated_at") or "").strip(),
			}
		)
		items.append(entry)
	return items


def _blocked_items(rows: list[dict[str, Any]], plan_label: str) -> list[dict[str, Any]]:
	items: list[dict[str, Any]] = []
	for row in rows:
		is_demand = str(row.get("blocked_type") or "").strip() == "demand"
		ref = row.get("demand") if is_demand else row.get("package")
		ref = ref or {}
		code = str(ref.get("code") or "").strip()
		if not code:
			continue
		title = str(ref.get("name") or code).strip()
		category = str(row.get("category") or "").strip()
		method = str(row.get("method") or "").strip()
		value = _money(row.get("estimated_value"), row.get("currency") or "KES")
		blocker = str(row.get("blocker_message") or "").strip()
		subtitle = " · ".join([s for s in (category, method, value) if s])
		entry = _work_item_base(
			queue="blocked",
			code=code,
			title=title,
			subtitle=subtitle,
			object_type="approved_demand" if is_demand else "procurement_package",
			plan_label=plan_label,
		)
		meta_line = " · ".join([s for s in (method, value) if s])
		entry.update(
			{
				"category_label": category,
				"meta_line": meta_line,
				"budget_status": "",
				"budget_status_label": "",
				"status_pill_label": "Blocked",
				"status_pill_tone": "blocked",
				"updated_relative": _relative_label(row.get("modified") or row.get("updated_at")),
				"summary_detail_line": " · ".join(
					[
						s
						for s in (
							"Approved demand" if is_demand else "Procurement package",
							category,
							method,
							value,
						)
						if s
					]
				),
				"status_headline": "Blocked",
				"status_detail": blocker or "Resolve blockers before continuing.",
				"next_step_detail": "Resolve the blocker to continue planning.",
				"list_next_action": "Resolve blocker",
				"blockers": [{"label": blocker, "code": "BLOCKED"}] if blocker else [],
				"next_action_label": "Resolve Blocker",
				"primary_action": {
					"label": "Resolve Blocker",
					"action": "open_demand" if is_demand else "open_package",
					"target": code,
				},
				"secondary_actions": [],
			}
		)
		items.append(entry)
	return items


def _recently_released_items(rows: list[dict[str, Any]], plan_label: str) -> list[dict[str, Any]]:
	items: list[dict[str, Any]] = []
	for row in rows:
		pkg = row.get("package") or {}
		tender = row.get("tender") or {}
		code = str(pkg.get("code") or "").strip()
		if not code:
			continue
		title = str(pkg.get("name") or code).strip()
		subtitle = "Released to Tender Management"
		entry = _work_item_base(
			queue="recently_released",
			code=code,
			title=title,
			subtitle=subtitle,
			object_type="procurement_package",
			plan_label=plan_label,
		)
		tender_code = str(tender.get("code") or "").strip()
		entry.update(
			{
				"category_label": "Released",
				"meta_line": subtitle,
				"budget_status": "",
				"budget_status_label": "",
				"status_pill_label": "Released",
				"status_pill_tone": "released",
				"updated_relative": _relative_label(row.get("released_at") or row.get("modified")),
				"summary_detail_line": " · ".join(
					[s for s in ("Procurement package", subtitle) if s]
				),
				"status_headline": "Released",
				"status_detail": "This package has been released to Tender Management.",
				"next_step_detail": "Continue follow-up in Tender Management.",
				"list_next_action": "Continue in Tender Management",
				"state_label": "Released",
				"blockers": [],
				"next_action_label": "Continue in Tender Management",
				"primary_action": {
					"label": "Open Tender" if tender_code else "View Package",
					"action": "open_tender" if tender_code else "open_package",
					"target": tender_code or code,
				},
				"secondary_actions": [{"label": "View Package", "action": "view_package", "target": code}],
			}
		)
		items.append(entry)
	return items


def get_workbench_item_view_model(
	*,
	queue: str,
	actor: str | None = None,
	limit: int = 20,
	start: int = 0,
	include_test_data: bool = False,
) -> dict[str, Any]:
	"""Return unified PP3 workbench items for a queue."""
	user = _session_user(actor)
	queue_key = str(queue or "").strip()
	if queue_key not in SUPPORTED_QUEUES:
		return {
			"ok": False,
			"error_code": "PP_INVALID_QUEUE",
			"message": f"Unsupported workbench queue: {queue_key}",
			"queue": queue_key,
			"total": 0,
			"limit": max(cint(limit or 20), 1),
			"start": max(cint(start or 0), 0),
			"items": [],
			"role_key": resolve_pp_role_key(user) or "auditor",
		}

	safe_start = max(cint(start or 0), 0)
	safe_limit = max(cint(limit or 20), 1)
	role_key = resolve_pp_role_key(user) or "auditor"
	plan_label = _active_plan_label(user)

	if queue_key == "needs_planning":
		fetch_limit = max(safe_limit + safe_start, 500)
		out = get_approved_demands_awaiting_planning(
			{"start": 0, "limit": fetch_limit},
			user,
		)
		if not out.get("ok"):
			return {
				"ok": False,
				"error_code": out.get("error_code") or "PP_QUEUE_ERROR",
				"message": out.get("message") or "Unable to load needs planning queue.",
				"queue": queue_key,
				"total": 0,
				"limit": safe_limit,
				"start": safe_start,
				"items": [],
				"role_key": out.get("role_key") or role_key,
			}
		rows = out.get("rows") or []
		items = _needs_planning_items(rows, plan_label)
		total = len(items)
		items = items[safe_start : safe_start + safe_limit]
		return {
			"ok": True,
			"queue": queue_key,
			"total": total,
			"limit": safe_limit,
			"start": safe_start,
			"items": items,
			"role_key": out.get("role_key") or role_key,
		}

	if queue_key == "blocked":
		read_limit = max(safe_limit + safe_start, 200)
		rows, total = _blocked_rows(user, limit=read_limit)
		items = _blocked_items(rows, plan_label)
		items, scoped_total = _apply_demo_scope(items, include_test_data=include_test_data)
		items = items[safe_start : safe_start + safe_limit]
		return {
			"ok": True,
			"queue": queue_key,
			"total": scoped_total,
			"limit": safe_limit,
			"start": safe_start,
			"items": items,
			"role_key": role_key,
		}

	if queue_key == "recently_released":
		read_limit = max(safe_limit + safe_start, 200)
		rows, total = _released_recently_rows(user, limit=read_limit)
		items = _recently_released_items(rows, plan_label)
		items, scoped_total = _apply_demo_scope(items, include_test_data=include_test_data)
		items = items[safe_start : safe_start + safe_limit]
		return {
			"ok": True,
			"queue": queue_key,
			"total": scoped_total,
			"limit": safe_limit,
			"start": safe_start,
			"items": items,
			"role_key": role_key,
		}

	status_map = {
		"draft_packages": PKG_DRAFT,
		"needs_review": PKG_IN_REVIEW,
		"ready_release": PKG_READY_FOR_RELEASE,
	}
	out = get_package_workbench_rows(
		{"status": status_map[queue_key], "start": 0, "limit": max(safe_limit + safe_start, 200)},
		user,
	)
	if not out.get("ok"):
		return {
			"ok": False,
			"error_code": out.get("error_code") or "PP_QUEUE_ERROR",
			"message": out.get("message") or "Unable to load package queue.",
			"queue": queue_key,
			"total": 0,
			"limit": safe_limit,
			"start": safe_start,
			"items": [],
			"role_key": out.get("role_key") or role_key,
		}
	rows = out.get("rows") or []
	items = _package_queue_items(rows, queue_key, plan_label)
	items, total = _apply_demo_scope(items, include_test_data=include_test_data)
	items = items[safe_start : safe_start + safe_limit]
	return {
		"ok": True,
		"queue": queue_key,
		"total": total,
		"limit": safe_limit,
		"start": safe_start,
		"items": items,
		"role_key": out.get("role_key") or role_key,
	}
