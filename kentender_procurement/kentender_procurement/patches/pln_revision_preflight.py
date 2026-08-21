"""Refuse the Planning revision migration when legacy data is ambiguous."""

from __future__ import annotations

import frappe


def _duplicates(sql: str) -> list[tuple]:
	return frappe.db.sql(sql)


def execute() -> None:
	issues: list[str] = []
	if frappe.db.table_exists("Procurement Plan"):
		rows = _duplicates(
			"""
			select procuring_entity, financial_year, count(*)
			from `tabProcurement Plan`
			group by procuring_entity, financial_year having count(*) > 1
			"""
		)
		if rows:
			issues.append(f"duplicate PE/FY Plans: {rows[:10]}")
	if frappe.db.table_exists("Procurement Plan Version"):
		rows = _duplicates(
			"""
			select plan, count(*) from `tabProcurement Plan Version`
			where status in ('Draft', 'In review', 'Returned')
			group by plan having count(*) > 1
			"""
		)
		if rows:
			issues.append(f"multiple open Versions: {rows[:10]}")
	if frappe.db.table_exists("Plan Demand Allocation"):
		rows = _duplicates(
			"""
			select demand_item, count(*) from `tabPlan Demand Allocation`
			where status in ('Draft', 'Effective')
			group by demand_item having count(*) > 1
			"""
		)
		if rows:
			issues.append(f"duplicate active Need-Item holds: {rows[:10]}")
	if issues:
		raise RuntimeError(
			"PLN_REVISION_PREFLIGHT_FAILED — resolve these records before migrate: "
			+ "; ".join(issues)
		)
