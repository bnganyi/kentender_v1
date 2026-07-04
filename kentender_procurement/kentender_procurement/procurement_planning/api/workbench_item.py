# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-002 — Unified Workbench item view-model API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	get_workbench_item_view_model,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"queue": "",
		"total": 0,
		"limit": 0,
		"start": 0,
		"items": [],
	}


@frappe.whitelist()
def get_pp_workbench_item_view_model(
	queue: str,
	limit: int = 20,
	start: int = 0,
	include_test_data: int = 0,
	search: str | None = None,
	department: str | None = None,
	category: str | None = None,
	value_range: str | None = None,
	created_from: str | None = None,
	created_to: str | None = None,
	sort: str | None = None,
) -> dict[str, Any]:
	"""Return canonical PP3 workbench items for one queue."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to Procurement Planning workbench queues."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
		require_package_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	return get_workbench_item_view_model(
		queue=queue,
		actor=frappe.session.user,
		limit=limit,
		start=start,
		include_test_data=bool(cint(include_test_data or 0)),
		search=search,
		department=department,
		category=category,
		value_range=value_range,
		created_from=created_from,
		created_to=created_to,
		sort=sort,
	)


# W10 — filter-drawer option lists (department names, category values, value
# ranges, sort keys), ported in spirit from
# `demand_intake.api.queue_list.get_dia_queue_filter_meta` per the "use the
# DIA implementation" direction: same shape (list of {value, label}), same
# never-expose-raw-ids rule — `value` here is always the display text itself
# (department name / category), never a Procuring Department hash id, since
# every workbench queue's `department_label`/`category_label` filter match is
# a case-insensitive substring match against that same display text.
@frappe.whitelist()
def get_pp_workbench_filter_meta() -> dict[str, Any]:
	"""Read-only option lists for the workbench Filter drawer and Sort menu."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to Procurement Planning workbench queues."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
		require_package_read=False,
	)
	if denied:
		return {"ok": False, "error_code": denied.get("error_code"), "message": denied.get("message")}

	departments: list[dict[str, str]] = []
	if frappe.db.exists("DocType", "Procuring Department"):
		rows = frappe.get_all(
			"Procuring Department",
			fields=["department_name"],
			filters={"department_name": ["is", "set"]},
			order_by="department_name asc",
			limit_page_length=400,
		)
		seen: set[str] = set()
		for row in rows:
			label = str(row.get("department_name") or "").strip()
			if label and label not in seen:
				seen.add(label)
				departments.append({"value": label, "label": label})

	categories = [{"value": c, "label": c} for c in ("Works", "Goods", "Services", "Consultancy")]
	value_ranges = [
		{"value": "under_100m", "label": "Under KES 100M"},
		{"value": "100m_500m", "label": "KES 100M \u2013 500M"},
		{"value": "over_500m", "label": "Over KES 500M"},
	]
	sort_options = [
		{"value": "newest", "label": "Newest first"},
		{"value": "oldest", "label": "Oldest first"},
		{"value": "value_desc", "label": "Value: High to Low"},
		{"value": "value_asc", "label": "Value: Low to High"},
		{"value": "title_asc", "label": "Title: A to Z"},
		{"value": "title_desc", "label": "Title: Z to A"},
	]
	return {
		"ok": True,
		"departments": departments,
		"categories": categories,
		"value_ranges": value_ranges,
		"sort_options": sort_options,
	}
