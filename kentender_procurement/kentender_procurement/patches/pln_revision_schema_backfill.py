"""Backfill revised Planning lineage keys and install database constraints."""

from __future__ import annotations

import frappe


def _has_index(table: str, name: str) -> bool:
	return bool(frappe.db.sql(f"show index from `{table}` where Key_name=%s", name))


def _add_index(table: str, name: str, columns: str, *, unique: bool = False) -> None:
	if _has_index(table, name):
		return
	keyword = "unique " if unique else ""
	frappe.db.sql_ddl(f"alter table `{table}` add {keyword}index `{name}` ({columns})")


def execute() -> None:
	if frappe.db.has_column("Procurement Plan Version", "open_version_slot"):
		frappe.db.sql(
			"""
			update `tabProcurement Plan Version`
			set open_version_slot = case
				when status in ('Draft', 'In review', 'Returned') then plan else null end
			"""
		)
	if frappe.db.has_column("Plan Demand Allocation", "source_org_unit"):
		frappe.db.sql(
			"""
			update `tabPlan Demand Allocation` a
			inner join `tabDemand` d on d.name = a.demand
			set a.source_org_unit = d.owner_org_unit
			where coalesce(a.source_org_unit, '') = ''
			"""
		)
	if frappe.db.has_column("Plan Demand Allocation", "source_funding_allocation"):
		frappe.db.sql(
			"""
			update `tabPlan Demand Allocation` a
			inner join `tabDemand Funding Allocation` f on f.demand = a.demand
			set a.source_funding_allocation = f.name
			where coalesce(a.source_funding_allocation, '') = ''
			"""
		)
	if frappe.db.has_column("Plan Demand Allocation", "active_hold_key"):
		frappe.db.sql(
			"""
			update `tabPlan Demand Allocation`
			set active_hold_key = case
				when status in ('Draft', 'Effective') then demand_item else null end
			"""
		)

	_add_index("tabProcurement Plan", "uniq_pln_pe_fy", "`procuring_entity`, `financial_year`", unique=True)
	_add_index("tabProcurement Plan Version", "uniq_pln_version_number", "`plan`, `version_number`", unique=True)
	_add_index("tabProcurement Plan Version", "uniq_pln_open_version", "`open_version_slot`", unique=True)
	_add_index(
		"tabProcurement Plan Item",
		"uniq_pln_formation_batch",
		"`plan`, `formation_idempotency_key`, `formation_batch_index`",
		unique=True,
	)
	_add_index("tabPlan Demand Allocation", "uniq_pln_active_hold", "`active_hold_key`", unique=True)
	_add_index("tabProcurement Plan Item", "idx_pln_item_plan_state", "`plan`, `baseline_state`")
	_add_index("tabPlan Demand Allocation", "idx_pln_alloc_demand_status", "`demand`, `status`")
	_add_index("tabPlan Demand Allocation", "idx_pln_alloc_version", "`proposed_in_version`, `status`")

	# Frappe model sync does not remove orphaned physical columns.
	if frappe.db.has_column("Procurement Plan", "coordinating_org_unit"):
		frappe.db.sql_ddl("alter table `tabProcurement Plan` drop column `coordinating_org_unit`")
