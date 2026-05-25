# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 P1 — dev wipe of v1 Procurement Planning rows before PP2 schema sync.

User decision: no migration; delete conflicting planning data and reseed after migrate.
Runs in pre_model_sync so old status values do not block Select option changes.
"""

from __future__ import annotations

import frappe


def _delete_if_table(doctype: str) -> None:
	table = f"tab{doctype}"
	if frappe.db.table_exists(table):
		frappe.db.sql(f"delete from `{table}`")


def execute() -> None:
	for dt in (
		"Planning Audit Event",
		"Planning Release Consumption Record",
		"Package Review Decision",
		"Package Readiness Result",
		"Package Method Decision",
		"Procurement Package Line",
		"Procurement Package",
		"Procurement Plan",
	):
		_delete_if_table(dt)
	frappe.db.commit()
