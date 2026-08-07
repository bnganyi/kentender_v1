# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-001 — Approved demands awaiting Planning queue (PP2-FR-001 / pack §7.1)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt, getdate

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	ALLOWED_DEMAND_STATUSES,
	_active_package_line_for_demand,
	_active_package_line_for_item_code,
	_demand_budget_ok,
	demand_has_unpackaged_planning_inclusion,
)

_QUEUE_DEMAND_FIELDS = [
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
	"modified",
]

_ITEM_FIELDS = [
	"name",
	"item_description",
	"category",
	"estimated_unit_cost",
	"line_total",
	"quantity",
	"uom",
	"idx",
]

READY_TO_PLAN_QUEUE = "ready-to-plan"
BLOCKED_QUEUE = "blocked"
ALREADY_PLANNED_QUEUE = "already-planned"
_SUPPORTED_QUEUE_KEYS = {READY_TO_PLAN_QUEUE, BLOCKED_QUEUE, ALREADY_PLANNED_QUEUE}


def _derive_demand_item_code(demand_code: str, line_idx: int) -> str:
	code = (demand_code or "").strip().upper()
	stem = code[4:] if code.startswith("DEM-") else code
	return f"DEMITEM-{stem}-{int(line_idx):03d}"


def _planning_status_label(*, status: str, planning_status: str) -> str:
	st = (status or "").strip()
	ps = (planning_status or "").strip()
	if st == "Planning Ready" or ps in ("Not Planned", "Planning Ready"):
		return "Ready for Planning"
	if ps == "Partially Planned":
		return "Partially Planned"
	return ps or "Ready for Planning"


def _base_demand_filters(filters: dict[str, Any]) -> list[list[Any]]:
	"""Demand filters aligned with DIA approved-not-planned / planning-ready semantics."""
	clauses: list[list[Any]] = [
		["status", "in", list(ALLOWED_DEMAND_STATUSES)],
		["planning_status", "!=", "Fully Planned"],
	]

	procuring_entity = (filters.get("procuring_entity") or "").strip()
	if procuring_entity:
		clauses.append(["procuring_entity", "=", procuring_entity])

	planning_status = (filters.get("planning_status") or "").strip()
	if planning_status:
		clauses.append(["planning_status", "=", planning_status])

	category = (filters.get("category") or "").strip()
	if category:
		clauses.append(["requisition_type", "=", category])

	return clauses


def _demand_passes_queue_eligibility(row: dict[str, Any]) -> bool:
	if (row.get("status") or "").strip() not in ALLOWED_DEMAND_STATUSES:
		return False

	planning_status = (row.get("planning_status") or "").strip()
	status = (row.get("status") or "").strip()
	if planning_status == "Fully Planned":
		return False
	if status == "Approved" and planning_status not in ("Not Planned", "Partially Planned"):
		return False

	if not _demand_budget_ok(row):
		return False

	demand_name = row.get("name") or ""
	if _active_package_line_for_demand(demand_name):
		return False

	items = frappe.get_all(
		"Demand Item",
		filters={"parent": demand_name, "parenttype": "Demand"},
		fields=["name", "idx"],
		order_by="idx asc",
		limit_page_length=100,
	)
	if not items:
		return False

	demand_code = (row.get("demand_id") or demand_name or "").strip()
	if demand_has_unpackaged_planning_inclusion(demand_code):
		return False
	for item in items:
		item_code = _derive_demand_item_code(demand_code, int(item.get("idx") or 1))
		if _active_package_line_for_item_code(item_code):
			return False

	return True


def _load_demand_items(demand_name: str, demand_code: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Demand Item",
		filters={"parent": demand_name, "parenttype": "Demand"},
		fields=_ITEM_FIELDS,
		order_by="idx asc",
		limit_page_length=100,
	)
	out: list[dict[str, Any]] = []
	for row in rows:
		idx = int(row.get("idx") or len(out) + 1)
		code = _derive_demand_item_code(demand_code, idx)
		desc = (row.get("item_description") or "").strip()
		out.append(
			{
				"id": row.get("name") or "",
				"code": code,
				"name": desc or code,
				"category": (row.get("category") or "").strip(),
				"estimated_value": flt(row.get("line_total") or row.get("estimated_unit_cost")),
			}
		)
	return out


def load_demand_items_for_drawer(demand_name: str, demand_code: str) -> list[dict[str, Any]]:
	"""Return demand item refs with drawer fields (uom, quantity)."""
	rows = frappe.get_all(
		"Demand Item",
		filters={"parent": demand_name, "parenttype": "Demand"},
		fields=_ITEM_FIELDS,
		order_by="idx asc",
		limit_page_length=100,
	)
	out: list[dict[str, Any]] = []
	for row in rows:
		idx = int(row.get("idx") or len(out) + 1)
		code = _derive_demand_item_code(demand_code, idx)
		desc = (row.get("item_description") or "").strip()
		out.append(
			{
				"id": row.get("name") or "",
				"code": code,
				"name": desc or code,
				"category": (row.get("category") or "").strip(),
				"uom": (row.get("uom") or "").strip(),
				"quantity": flt(row.get("quantity")),
				"estimated_value": flt(row.get("line_total") or row.get("estimated_unit_cost")),
			}
		)
	return out


def _department_label(department_id: str | None) -> str:
	"""Resolve a `requesting_department` Link id to its display name.

	`Demand.requesting_department` is a Link to `Procuring Department`, whose
	`name` is a random hash (autoname="hash") — never a value fit for
	end-user display. Only `department_name` is presentable.
	"""
	dept_id = (department_id or "").strip()
	if not dept_id:
		return ""
	return (frappe.db.get_value("Procuring Department", dept_id, "department_name") or "").strip()


def _budget_line_ref(budget_line_name: str | None) -> dict[str, str]:
	bl_name = (budget_line_name or "").strip()
	if not bl_name or not frappe.db.exists("Budget Line", bl_name):
		return {"id": "", "code": "", "name": ""}
	# MVP-1 Budget Line: generated_reference + title (legacy budget_line_code removed).
	meta_fields = {df.fieldname for df in frappe.get_meta("Budget Line").fields}
	fields = ["name"]
	if "generated_reference" in meta_fields:
		fields.append("generated_reference")
	if "title" in meta_fields:
		fields.append("title")
	if "budget_line_code" in meta_fields:
		fields.append("budget_line_code")
	if "budget_line_name" in meta_fields:
		fields.append("budget_line_name")
	row = frappe.db.get_value("Budget Line", bl_name, tuple(fields), as_dict=True) or {}
	code = (
		(row.get("generated_reference") or row.get("budget_line_code") or row.get("name") or "")
	).strip()
	name = (row.get("title") or row.get("budget_line_name") or code).strip()
	return {
		"id": row.get("name") or "",
		"code": code,
		"name": name,
	}


def _format_row(row: dict[str, Any]) -> dict[str, Any]:
	demand_name = row.get("name") or ""
	demand_code = (row.get("demand_id") or demand_name or "").strip()
	approval_dt = row.get("finance_approved_at")
	approval_date = getdate(approval_dt).isoformat() if approval_dt else ""
	category = (row.get("requisition_type") or "").strip()
	if not category:
		items = _load_demand_items(demand_name, demand_code)
		category = (items[0].get("category") if items else "") or ""

	return {
		"demand": {
			"id": demand_name,
			"code": demand_code,
			"name": (row.get("title") or demand_code).strip(),
		},
		"department": _department_label(row.get("requesting_department")),
		"category": category,
		"estimated_value": flt(row.get("total_amount")),
		"currency": "KES",
		"budget_line": _budget_line_ref(row.get("budget_line")),
		"approval_date": approval_date,
		"planning_status": _planning_status_label(
			status=(row.get("status") or "").strip(),
			planning_status=(row.get("planning_status") or "").strip(),
		),
		"demand_items": _load_demand_items(demand_name, demand_code),
		"blocker_summary": None,
		"next_action": "include_in_plan",
	}


def _value_range_matches(range_key: str, amount: float) -> bool:
	"""Mirrors `workbench_item_view_model._value_range_matches` so the Needs
	Planning queue's value-range filter behaves identically to the other 5
	workbench queues (same bucket keys, same semantics)."""
	key = (range_key or "").strip().lower()
	value = flt(amount or 0)
	if key in ("", "all", "all_values"):
		return True
	if key in ("under_kes_100m", "under_100m"):
		return value < 100_000_000
	if key in ("kes_100m_500m", "100m_500m"):
		return 100_000_000 <= value <= 500_000_000
	if key in ("over_kes_500m", "over_500m"):
		return value > 500_000_000
	return True


def _to_date_or_none(value: Any):
	text = str(value or "").strip()
	if not text:
		return None
	try:
		return getdate(text)
	except Exception:
		return None


def _apply_extra_filters(
	rows: list[dict[str, Any]],
	*,
	department: str | None = None,
	value_range: str | None = None,
	created_from: str | None = None,
	created_to: str | None = None,
) -> list[dict[str, Any]]:
	"""Department/value-range/created-range refinements — additive to
	`_apply_search`, kept separate since they operate on already-formatted
	rows (post `_format_row`) rather than raw Demand fields."""
	dept_q = (department or "").strip().lower()
	date_from = _to_date_or_none(created_from)
	date_to = _to_date_or_none(created_to)
	if not (dept_q or value_range or date_from or date_to):
		return rows
	out: list[dict[str, Any]] = []
	for row in rows:
		if dept_q and dept_q not in str(row.get("department") or "").strip().lower():
			continue
		if not _value_range_matches(str(value_range or ""), row.get("estimated_value")):
			continue
		row_date = _to_date_or_none(row.get("approval_date"))
		if date_from and row_date and row_date < date_from:
			continue
		if date_to and row_date and row_date > date_to:
			continue
		out.append(row)
	return out


def _apply_demand_sort(rows: list[dict[str, Any]], sort: str | None) -> list[dict[str, Any]]:
	"""Mirrors `workbench_item_view_model._apply_sort` for parity across all
	6 workbench queues."""
	sort_key = (sort or "").strip().lower()
	if not sort_key or sort_key == "newest":
		return sorted(
			rows,
			key=lambda row: (_to_date_or_none(row.get("approval_date")) is None, _to_date_or_none(row.get("approval_date"))),
			reverse=True,
		)
	if sort_key == "oldest":
		return sorted(
			rows,
			key=lambda row: (_to_date_or_none(row.get("approval_date")) is None, _to_date_or_none(row.get("approval_date"))),
		)
	if sort_key in ("value_high_low", "value_desc"):
		return sorted(rows, key=lambda row: flt(row.get("estimated_value") or 0), reverse=True)
	if sort_key in ("value_low_high", "value_asc"):
		return sorted(rows, key=lambda row: flt(row.get("estimated_value") or 0))
	if sort_key in ("title_asc", "name_asc"):
		return sorted(rows, key=lambda row: str((row.get("demand") or {}).get("name") or "").strip().lower())
	if sort_key in ("title_desc", "name_desc"):
		return sorted(
			rows,
			key=lambda row: str((row.get("demand") or {}).get("name") or "").strip().lower(),
			reverse=True,
		)
	return rows


def _apply_search(rows: list[dict[str, Any]], search_text: str) -> list[dict[str, Any]]:
	q = (search_text or "").strip().lower()
	if not q:
		return rows
	out: list[dict[str, Any]] = []
	for row in rows:
		demand = row.get("demand") or {}
		hay = " ".join(
			[
				str(demand.get("code") or ""),
				str(demand.get("name") or ""),
				str(row.get("department") or ""),
				str(row.get("category") or ""),
				str((row.get("budget_line") or {}).get("code") or ""),
			]
		).lower()
		if q in hay:
			out.append(row)
	return out


def _normalize_queue_key(filters: dict[str, Any]) -> str:
	queue = str(filters.get("queue") or "").strip().lower()
	return queue if queue in _SUPPORTED_QUEUE_KEYS else READY_TO_PLAN_QUEUE


def _queue_blocker_label(row: dict[str, Any]) -> str:
	if not _demand_budget_ok(row):
		return "Missing approved budget link"
	if _active_package_line_for_demand(row.get("name") or ""):
		return "Already included in active package"
	demand_name = row.get("name") or ""
	demand_code = (row.get("demand_id") or demand_name or "").strip()
	items = frappe.get_all(
		"Demand Item",
		filters={"parent": demand_name, "parenttype": "Demand"},
		fields=["idx"],
		order_by="idx asc",
		limit_page_length=100,
	)
	for item in items:
		item_code = _derive_demand_item_code(demand_code, int(item.get("idx") or 1))
		if _active_package_line_for_item_code(item_code):
			return "Already included in active package"
	return "Demand has planning blockers"


def _ready_rows(
	*,
	filters: dict[str, Any],
	actor: str,
	clauses: list[list[Any]],
) -> list[dict[str, Any]]:
	demand_rows = frappe.get_all(
		"Demand",
		filters=clauses,
		fields=_QUEUE_DEMAND_FIELDS,
		order_by="modified desc",
		limit_page_length=5000,
	)
	eligible_rows: list[dict[str, Any]] = []
	for row in demand_rows:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity"), actor):
			continue
		if not _demand_passes_queue_eligibility(row):
			continue
		demand_code = (row.get("demand_id") or row.get("name") or "").strip()
		if demand_has_unpackaged_planning_inclusion(demand_code):
			continue
		eligible_rows.append(_format_row(row))
	return _apply_search(eligible_rows, str(filters.get("search_text") or ""))


def _blocked_rows(*, filters: dict[str, Any], actor: str, clauses: list[list[Any]]) -> list[dict[str, Any]]:
	demand_rows = frappe.get_all(
		"Demand",
		filters=clauses,
		fields=_QUEUE_DEMAND_FIELDS,
		order_by="modified desc",
		limit_page_length=5000,
	)
	out: list[dict[str, Any]] = []
	for row in demand_rows:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity"), actor):
			continue
		status = (row.get("status") or "").strip()
		if status not in ALLOWED_DEMAND_STATUSES:
			continue
		planning_status = (row.get("planning_status") or "").strip()
		if planning_status == "Fully Planned":
			continue
		if _demand_passes_queue_eligibility(row):
			continue
		demand_code = (row.get("demand_id") or row.get("name") or "").strip()
		if demand_has_unpackaged_planning_inclusion(demand_code):
			continue
		entry = _format_row(row)
		blocker = _queue_blocker_label(row)
		entry["planning_status"] = "Blocked"
		entry["blocker_summary"] = {"count": 1, "label": blocker}
		out.append(entry)
	return _apply_search(out, str(filters.get("search_text") or ""))


def _already_planned_rows(
	*,
	filters: dict[str, Any],
	actor: str,
	allowed_entities: set[str] | None,
) -> list[dict[str, Any]]:
	clauses: list[list[Any]] = [
		["status", "in", list(ALLOWED_DEMAND_STATUSES)],
		["planning_status", "=", "Fully Planned"],
	]
	procuring_entity = (filters.get("procuring_entity") or "").strip()
	if procuring_entity:
		clauses.append(["procuring_entity", "=", procuring_entity])
	category = (filters.get("category") or "").strip()
	if category:
		clauses.append(["requisition_type", "=", category])
	if allowed_entities is not None:
		if not allowed_entities:
			return []
		clauses.append(["procuring_entity", "in", sorted(allowed_entities)])

	demand_rows = frappe.get_all(
		"Demand",
		filters=clauses,
		fields=_QUEUE_DEMAND_FIELDS,
		order_by="modified desc",
		limit_page_length=5000,
	)
	out: list[dict[str, Any]] = []
	for row in demand_rows:
		if not pp_scope.entity_in_user_scope(row.get("procuring_entity"), actor):
			continue
		entry = _format_row(row)
		entry["planning_status"] = "Fully Planned"
		entry["next_action"] = "open_package"
		out.append(entry)
	return _apply_search(out, str(filters.get("search_text") or ""))


def get_approved_demands_for_queue(
	filters: dict[str, Any] | None,
	actor: str,
) -> dict[str, Any]:
	"""Return approved demands for queue-aware Approved Demands route."""
	filters = dict(filters or {})
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	queue_key = _normalize_queue_key(filters)
	filters["queue"] = queue_key

	if not frappe.db.exists("DocType", "Demand"):
		from kentender_procurement.procurement_lifecycle.demand_module_gate import (
			RETIRED_MESSAGE,
		)

		return {
			"ok": True,
			"error_code": "DEMAND_MODULE_RETIRED",
			"message": RETIRED_MESSAGE,
			"role_key": role_key,
			"queue_key": queue_key,
			"total": 0,
			"rows": [],
			"filters_applied": filters,
			"skipped": True,
		}

	allowed_entities = pp_scope.get_user_allowed_entities(actor)
	if allowed_entities is not None and not allowed_entities:
		return {
			"ok": True,
			"role_key": role_key,
			"queue_key": queue_key,
			"total": 0,
			"rows": [],
			"filters_applied": filters,
		}

	base_clauses = _base_demand_filters(filters)
	if allowed_entities is not None:
		base_clauses.append(["procuring_entity", "in", sorted(allowed_entities)])

	if queue_key == BLOCKED_QUEUE:
		formatted = _blocked_rows(filters=filters, actor=actor, clauses=base_clauses)
	elif queue_key == ALREADY_PLANNED_QUEUE:
		formatted = _already_planned_rows(
			filters=filters,
			actor=actor,
			allowed_entities=allowed_entities,
		)
	else:
		formatted = _ready_rows(filters=filters, actor=actor, clauses=base_clauses)

	formatted = _apply_extra_filters(
		formatted,
		department=filters.get("department"),
		value_range=filters.get("value_range"),
		created_from=filters.get("created_from"),
		created_to=filters.get("created_to"),
	)
	formatted = _apply_demand_sort(formatted, filters.get("sort"))

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
		"queue_key": queue_key,
		"total": total,
		"rows": formatted[start : start + limit],
		"filters_applied": filters,
	}


def get_approved_demands_awaiting_planning(
	filters: dict[str, Any] | None,
	actor: str,
) -> dict[str, Any]:
	"""Return approved, budget-linked demands eligible for Planning inclusion."""
	filters = dict(filters or {})
	filters["queue"] = READY_TO_PLAN_QUEUE
	return get_approved_demands_for_queue(filters, actor)
