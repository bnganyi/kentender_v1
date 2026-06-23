# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-002 — Unified Workbench item view-model adapter."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, fmt_money

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
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
	return fmt_money(value or 0, currency=cur)


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
		subtitle = " · ".join([s for s in (category, value, funding) if s])
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
				"blockers": [],
				"next_action_label": "Include in Plan",
				"primary_action": {"label": "Include in Plan", "action": "include_in_plan", "target": code},
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
		entry.update(
			{
				"state_label": str(row.get("status") or entry["state_label"]).strip(),
				"blockers": [],
				"next_action_label": label,
				"primary_action": {"label": label, "action": action, "target": code},
				"secondary_actions": [{"label": "View Package", "action": "view_package", "target": code}],
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
		entry.update(
			{
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
		out = get_approved_demands_awaiting_planning(
			{"start": safe_start, "limit": safe_limit},
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
		total = cint(out.get("total") or len(items))
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
		items = _blocked_items(rows[safe_start : safe_start + safe_limit], plan_label)
		return {
			"ok": True,
			"queue": queue_key,
			"total": cint(total),
			"limit": safe_limit,
			"start": safe_start,
			"items": items,
			"role_key": role_key,
		}

	if queue_key == "recently_released":
		read_limit = max(safe_limit + safe_start, 200)
		rows, total = _released_recently_rows(user, limit=read_limit)
		items = _recently_released_items(rows[safe_start : safe_start + safe_limit], plan_label)
		return {
			"ok": True,
			"queue": queue_key,
			"total": cint(total),
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
		{"status": status_map[queue_key], "start": safe_start, "limit": safe_limit},
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
	return {
		"ok": True,
		"queue": queue_key,
		"total": cint(out.get("total") or len(items)),
		"limit": safe_limit,
		"start": safe_start,
		"items": items,
		"role_key": out.get("role_key") or role_key,
	}
