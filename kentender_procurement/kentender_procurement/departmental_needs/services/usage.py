from __future__ import annotations

from collections import defaultdict

import frappe
from frappe.utils import flt

from kentender_procurement.departmental_needs.constants import USAGE_FULL, USAGE_NOT_INCLUDED, USAGE_PARTIAL


def planning_usage(need: str) -> str:
	items = frappe.get_all("Departmental Need Item", filters={"departmental_need": need}, fields=["name", "indicative_quantity"])
	if not items:
		return USAGE_NOT_INCLUDED
	allocated: dict[str, float] = defaultdict(float)
	for row in frappe.get_all(
		"Plan Need Allocation",
		filters={"departmental_need": need, "status": "Effective"},
		fields=["departmental_need_item", "allocated_quantity"],
	):
		allocated[row.departmental_need_item] += flt(row.allocated_quantity)
	if not any(allocated.values()):
		return USAGE_NOT_INCLUDED
	if all(allocated[item.name] >= flt(item.indicative_quantity) for item in items):
		return USAGE_FULL
	return USAGE_PARTIAL


def effective_allocation_count(need: str) -> int:
	return frappe.db.count("Plan Need Allocation", {"departmental_need": need, "status": "Effective"})


def draft_allocation_count(need: str) -> int:
	return frappe.db.count("Plan Need Allocation", {"departmental_need": need, "status": "Draft"})
