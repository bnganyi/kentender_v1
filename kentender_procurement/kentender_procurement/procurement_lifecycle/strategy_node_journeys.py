# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-002 / LV-R5-002-02 — read-only procurement links for Strategy Objective / Strategy Target.

Returns linked ``Procurement Journey`` summaries and ``Budget Line`` rows (id, code, name)
for desk panels. Navigation aggregate only (ADR-PLC-002).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe


def _journey_open_route(journey_code: str | None, fallback_name: str) -> str:
	code = (journey_code or "").strip() or (fallback_name or "").strip()
	if not code:
		return "/desk/plc-procurement-journey"
	return f"/desk/plc-procurement-journey/{code}"


def _journey_rows_for_names(names: list[str]) -> list[dict[str, Any]]:
	if not names:
		return []
	rows = frappe.get_all(
		"Procurement Journey",
		filters={"name": ["in", names]},
		fields=["name", "journey_code", "journey_title", "current_stage_label", "modified"],
		order_by="modified desc",
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		jc = (r.get("journey_code") or r.get("name") or "").strip()
		nm = (r.get("name") or "").strip()
		out.append(
			{
				"journey_code": jc,
				"journey_title": (r.get("journey_title") or "").strip(),
				"current_stage_label": (r.get("current_stage_label") or "").strip(),
				"open_route": _journey_open_route(r.get("journey_code"), nm),
			}
		)
	return out


def _budget_line_entries(names: list[str]) -> list[dict[str, Any]]:
	if not names:
		return []
	rows = frappe.get_all(
		"Budget Line",
		filters={"name": ["in", names]},
		fields=["name", "budget_line_code", "budget_line_name"],
		order_by="modified desc",
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		docname = (r.get("name") or "").strip()
		code = (r.get("budget_line_code") or docname).strip()
		title = (r.get("budget_line_name") or "").strip()
		out.append(
			{
				"id": docname,
				"code": code,
				"name": title,
				"list_route": f"/app/budget-line/{quote(docname, safe='')}",
			}
		)
	return out


def build_procurement_links_payload(strategy_node_doctype: str, name: str) -> dict[str, Any]:
	"""Return journeys + budget lines linked to a strategy node. Caller enforces permissions."""
	dt = (strategy_node_doctype or "").strip()
	nm = (name or "").strip()
	if not dt or not nm:
		return {
			"ok": False,
			"error": "MISSING_PARAMS",
			"message": "strategy_node_doctype and name are required.",
			"journeys": [],
			"budget_lines": [],
		}

	if dt == "Strategy Objective":
		row = frappe.db.get_value(
			"Strategy Objective",
			nm,
			["objective_code", "objective_title"],
			as_dict=True,
		)
		if not row:
			return {
				"ok": False,
				"error": "NOT_FOUND",
				"message": "Strategy Objective not found.",
				"journeys": [],
				"budget_lines": [],
			}
		ocode = (row.get("objective_code") or "").strip()
		journey_names = frappe.get_all(
			"Procurement Journey",
			filters={"strategy_ref": ocode},
			pluck="name",
			order_by="modified desc",
			limit=200,
		)
		bl_names = frappe.get_all(
			"Budget Line",
			filters={"output_indicator": nm},
			pluck="name",
			order_by="modified desc",
			limit=200,
		)
	elif dt == "Strategy Target":
		row = frappe.db.get_value(
			"Strategy Target",
			nm,
			["target_code", "target_title"],
			as_dict=True,
		)
		if not row:
			return {
				"ok": False,
				"error": "NOT_FOUND",
				"message": "Strategy Target not found.",
				"journeys": [],
				"budget_lines": [],
			}
		tcode = (row.get("target_code") or "").strip()
		# Budget lines link by Link field (doc name). Multiple rows may share the same
		# business target_code (data repair / reseed); union all names for that code.
		name_candidates: list[str] = []
		if tcode:
			name_candidates = list(
				frappe.get_all(
					"Strategy Target",
					filters={"target_code": tcode},
					pluck="name",
					limit=100,
				)
				or []
			)
		if nm not in name_candidates:
			name_candidates.append(nm)
		bl_names = frappe.get_all(
			"Budget Line",
			filters={"performance_target": ["in", name_candidates]},
			pluck="name",
			order_by="modified desc",
			limit=200,
		)
		if not bl_names:
			journey_names = []
		else:
			journey_names = frappe.get_all(
				"Procurement Journey",
				filters={"budget_line_ref": ["in", bl_names]},
				pluck="name",
				order_by="modified desc",
				limit=200,
			)
	else:
		frappe.throw(
			frappe._(
				"Unsupported strategy node type; use Strategy Objective or Strategy Target."
			),
			title=frappe._("Invalid doctype"),
			exc=frappe.ValidationError,
		)

	# Dedupe journey names while preserving order
	seen: set[str] = set()
	unique_journeys: list[str] = []
	for jn in journey_names:
		if jn and jn not in seen:
			seen.add(jn)
			unique_journeys.append(jn)

	biz_code = (row.get("objective_code") or row.get("target_code") or "").strip()
	biz_title = (row.get("objective_title") or row.get("target_title") or "").strip()

	return {
		"ok": True,
		"strategy_node_doctype": dt,
		"strategy_node_name": nm,
		"business_code": biz_code,
		"business_title": biz_title,
		"journeys": _journey_rows_for_names(unique_journeys),
		"budget_lines": _budget_line_entries(bl_names),
	}
