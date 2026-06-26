# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-005 — Package workbench list rows (PP2 UI §12 / PRD §13.5)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.api.package_detail import _actions_for_workbench
from kentender_procurement.procurement_planning.package_journey_surfaces import (
	journey_link_hints_by_package_codes,
)
from kentender_procurement.procurement_planning.package_planning_release_display import (
	_tm2_name_and_title,
	batch_planning_release_handoff_hints_for_packages,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PKG_RETURNED,
	READINESS_NOT_RUN,
	pkg_workbench_group,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_budget_line_ref,
)

_PACKAGE_FIELDS = [
	"name",
	"package_code",
	"package_name",
	"package_description",
	"status",
	"readiness_status",
	"latest_readiness_code",
	"procurement_method",
	"procurement_category",
	"estimated_value",
	"currency",
	"budget_line_id",
	"tender_code",
	"journey_code",
	"procuring_entity_code",
	"fiscal_year",
	"plan_id",
	"creation",
	"modified",
]

_NEXT_ACTION_LABELS: dict[str, str] = {
	"complete_package": "Complete and submit the procurement package.",
	"open_package": "Open the procurement package.",
	"review_package": "Review the procurement package.",
	"mark_ready_for_release": "Mark the package ready for release.",
	"release_to_tender": "Release the package to Tender Management.",
	"view_release": "View the planning release handoff.",
	"view_tender": "View tender.",
}


def _tender_ref(
	tender_code: str | None,
	*,
	handoff: dict[str, Any] | None = None,
) -> dict[str, str] | None:
	code = (tender_code or "").strip()
	if not code and handoff:
		code = str(handoff.get("tender_code") or "").strip()
	if not code:
		return None
	name, title = _tm2_name_and_title(code)
	display = title or str(handoff.get("tender_title") or "").strip() or code
	return {
		"id": name or code,
		"code": code,
		"name": display,
	}


def _readiness_ref(latest_code: str | None, readiness_status: str | None) -> dict[str, str] | None:
	code = (latest_code or "").strip()
	status = (readiness_status or "").strip()
	if not code and not status:
		return None
	label = code or status
	return {"code": code, "name": label}


def _workbench_actions(
	status: str,
	role_key: str,
	*,
	plan_status: str = "",
) -> dict[str, bool]:
	return _actions_for_workbench(status, role_key, plan_status=plan_status)


def derive_package_next_action(
	status: str,
	role_key: str,
	*,
	plan_status: str = "",
	handoff: dict[str, Any] | None = None,
) -> dict[str, str]:
	"""Return stable machine key + human label for workbench list rows."""
	st = (status or "").strip()
	rk = role_key or "auditor"
	handoff_status = str((handoff or {}).get("status") or "").strip()

	if st == PKG_CONSUMED or handoff_status == "Consumed":
		key = "view_tender"
	elif st == PKG_RELEASED:
		key = "view_release"
	else:
		actions = _workbench_actions(st, rk, plan_status=plan_status)
		if st == PKG_READY_FOR_RELEASE and actions.get("release"):
			key = "release_to_tender"
		elif st == PKG_APPROVED and actions.get("mark_ready"):
			key = "mark_ready_for_release"
		elif st == PKG_IN_REVIEW and actions.get("approve"):
			key = "review_package"
		elif st in (PKG_DRAFT, PKG_RETURNED) and actions.get("submit"):
			key = "complete_package"
		elif actions.get("edit") or actions.get("submit"):
			key = "complete_package"
		else:
			key = "open_package"

	return {
		"key": key,
		"label": _NEXT_ACTION_LABELS.get(key, _NEXT_ACTION_LABELS["open_package"]),
	}


def _base_filters(filters: dict[str, Any]) -> dict[str, Any]:
	clauses: dict[str, Any] = {"is_active": 1}

	plan = (filters.get("plan") or "").strip()
	if plan:
		plan_name = plan
		if not frappe.db.exists("Procurement Plan", plan):
			plan_name = frappe.db.get_value("Procurement Plan", {"plan_code": plan}, "name") or ""
		if plan_name:
			clauses["plan_id"] = plan_name
		else:
			clauses["name"] = "__none__"

	status = (filters.get("status") or "").strip()
	if status:
		clauses["status"] = status

	category = (filters.get("category") or "").strip()
	if category:
		clauses["procurement_category"] = category

	method = (filters.get("method") or "").strip()
	if method:
		clauses["procurement_method"] = method

	fiscal_year = (filters.get("fiscal_year") or "").strip()
	if fiscal_year:
		clauses["fiscal_year"] = fiscal_year

	procuring_entity = (filters.get("procuring_entity") or "").strip()
	if procuring_entity:
		clauses["procuring_entity_code"] = procuring_entity

	readiness_status = (filters.get("readiness_status") or "").strip()
	if readiness_status:
		clauses["readiness_status"] = readiness_status

	return clauses


def _apply_search(rows: list[dict[str, Any]], search_text: str) -> list[dict[str, Any]]:
	q = (search_text or "").strip().lower()
	if not q:
		return rows
	out: list[dict[str, Any]] = []
	for row in rows:
		pkg = row.get("package") or {}
		budget = row.get("budget_line") or {}
		hay = " ".join(
			[
				str(pkg.get("code") or ""),
				str(pkg.get("name") or ""),
				str(budget.get("code") or ""),
				str(budget.get("name") or ""),
			]
		).lower()
		if q in hay:
			out.append(row)
	return out


def _apply_handoff_filter(rows: list[dict[str, Any]], handoff_status: str) -> list[dict[str, Any]]:
	target = (handoff_status or "").strip()
	if not target:
		return rows
	out: list[dict[str, Any]] = []
	for row in rows:
		handoff = row.get("planning_release_handoff") or {}
		status = str(handoff.get("status") or "").strip()
		if status == target:
			out.append(row)
	return out


def _plan_status_for(pkg: dict[str, Any], plan_status_cache: dict[str, str]) -> str:
	plan_id = (pkg.get("plan_id") or "").strip()
	if not plan_id:
		return ""
	if plan_id not in plan_status_cache:
		plan_status_cache[plan_id] = frappe.db.get_value("Procurement Plan", plan_id, "status") or ""
	return plan_status_cache[plan_id]


def _active_demand_count_by_package(package_codes: list[str]) -> dict[str, int]:
	if not package_codes:
		return {}
	placeholder = ", ".join(["%s"] * len(package_codes))
	rows = frappe.db.sql(
		f"""
		SELECT package_id, COUNT(DISTINCT demand_id) AS demand_count
		FROM `tabProcurement Package Line`
		WHERE ifnull(is_active, 1) = 1
		  AND package_id IN ({placeholder})
		GROUP BY package_id
		""",
		tuple(package_codes),
		as_dict=True,
	)
	out: dict[str, int] = {}
	for row in rows:
		pkg = str(row.get("package_id") or "").strip()
		if not pkg:
			continue
		out[pkg] = cint(row.get("demand_count") or 0)
	return out


def _format_row(
	pkg: dict[str, Any],
	*,
	role_key: str,
	journey: dict[str, Any] | None,
	planning_release_handoff: dict[str, Any] | None,
	plan_status: str,
	consolidated_demand_count: int = 0,
) -> dict[str, Any]:
	package_code = (pkg.get("package_code") or pkg.get("name") or "").strip()
	status = (pkg.get("status") or "").strip()
	readiness_status = (pkg.get("readiness_status") or "").strip() or READINESS_NOT_RUN
	return {
		"package": {
			"id": pkg.get("name") or "",
			"code": package_code,
			"name": (pkg.get("package_name") or package_code).strip(),
			"description": (pkg.get("package_description") or "").strip(),
		},
		"status": status,
		"workbench_group": pkg_workbench_group(status),
		"readiness_status": readiness_status,
		"readiness": _readiness_ref(pkg.get("latest_readiness_code"), readiness_status),
		"method": (pkg.get("procurement_method") or "").strip(),
		"category": (pkg.get("procurement_category") or "").strip(),
		"estimated_value": flt(pkg.get("estimated_value")),
		"currency": (pkg.get("currency") or "KES").strip() or "KES",
		"budget_line": _budget_line_ref(pkg.get("budget_line_id")),
		"tender": _tender_ref(pkg.get("tender_code"), handoff=planning_release_handoff),
		"journey": journey,
		"planning_release_handoff": planning_release_handoff,
		"procuring_entity_code": (pkg.get("procuring_entity_code") or "").strip(),
		"fiscal_year": (pkg.get("fiscal_year") or "").strip(),
		"next_action": derive_package_next_action(
			status,
			role_key,
			plan_status=plan_status,
			handoff=planning_release_handoff,
		),
		"consolidated_demand_count": cint(consolidated_demand_count or 0),
		"procuring_entity_label": str(pkg.get("procuring_entity_code") or "").strip(),
		"created_on": str(pkg.get("creation") or "").strip(),
		"updated_at": str(pkg.get("modified") or "").strip(),
	}


def get_package_workbench_rows(
	filters: dict[str, Any] | None,
	actor: str,
) -> dict[str, Any]:
	"""Return scoped package workbench rows for PP2 Packages surface."""
	filters = dict(filters or {})
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"

	if not frappe.db.exists("DocType", "Procurement Package"):
		return {
			"ok": False,
			"error_code": "PP_NOT_INSTALLED",
			"message": "Procurement Planning is not installed on this site.",
			"role_key": role_key,
			"total": 0,
			"rows": [],
			"filters_applied": filters,
		}

	clauses = _base_filters(filters)
	try:
		pkgs = frappe.get_list(
			"Procurement Package",
			filters=clauses,
			fields=_PACKAGE_FIELDS,
			order_by="modified desc",
			limit_page_length=5000,
		)
	except frappe.PermissionError:
		return {
			"ok": False,
			"error_code": "NO_PACKAGE_PERMISSION",
			"message": "You do not have permission to read procurement packages.",
			"role_key": role_key,
			"total": 0,
			"rows": [],
			"filters_applied": filters,
		}

	scoped: list[dict[str, Any]] = []
	for pkg in pkgs:
		entity_code = (pkg.get("procuring_entity_code") or "").strip()
		if not entity_code:
			demand_id = (pkg.get("demand_id") or "").strip()
			if demand_id:
				entity_code = (frappe.db.get_value("Demand", demand_id, "procuring_entity") or "").strip()
		if not pp_scope.entity_in_user_scope(entity_code, actor):
			continue
		scoped.append(pkg)

	package_codes = [
		str(p.get("package_code") or "").strip() for p in scoped if str(p.get("package_code") or "").strip()
	]
	journey_by_pkg = journey_link_hints_by_package_codes(package_codes)
	release_by_pkg = batch_planning_release_handoff_hints_for_packages(package_codes, journey_by_pkg)
	demand_count_by_pkg = _active_demand_count_by_package(package_codes)
	plan_status_cache: dict[str, str] = {}

	formatted: list[dict[str, Any]] = []
	for pkg in scoped:
		package_code = str(pkg.get("package_code") or "").strip()
		plan_status = _plan_status_for(pkg, plan_status_cache)
		formatted.append(
			_format_row(
				pkg,
				role_key=role_key,
				journey=journey_by_pkg.get(package_code),
				planning_release_handoff=release_by_pkg.get(package_code),
				plan_status=plan_status,
				consolidated_demand_count=demand_count_by_pkg.get(package_code, 0),
			)
		)

	formatted = _apply_search(formatted, str(filters.get("search_text") or ""))
	formatted = _apply_handoff_filter(formatted, str(filters.get("handoff_status") or ""))

	total = len(formatted)
	start = max(cint(filters.get("start") or 0), 0)
	limit = cint(filters.get("limit") or 50)
	if limit <= 0:
		limit = 50
	if limit > 200:
		limit = 200

	return {
		"ok": True,
		"role_key": role_key,
		"total": total,
		"rows": formatted[start : start + limit],
		"filters_applied": filters,
	}
