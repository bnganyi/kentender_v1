# Copyright (c) 2026, KenTender and contributors
"""REQ-CHG-001 v1.6 D1 — drop the unique index on
`Funding Reservation.plan_source_allocation`.

Procurement Requisitions is the module BUD-CHG-001 §8.2A always meant to
reserve for; unlike Procurement Planning's single non-mutating affordability
check, Requisitions revokes and later re-authorises (REQ-CHG-001 §7.4/§7.4A),
and a later, unrelated Requisition may draw the remaining balance of the same
Plan Source Allocation. A hard one-reservation-ever constraint on this column
made both cases impossible. Oversubscription is still prevented by the
locked, line-level position check in `reserve_funding` — this index was never
the only thing enforcing that.

The plain (non-unique) `plan_source_allocation_index` already covers lookup
performance, so nothing else changes.
"""

from __future__ import annotations

import frappe

TABLE = "tabFunding Reservation"
UNIQUE_INDEX = "plan_source_allocation"


def execute() -> None:
	if not frappe.db.table_exists("Funding Reservation"):
		return
	if frappe.db.has_index(TABLE, UNIQUE_INDEX):
		frappe.db.sql_ddl(f"alter table `{TABLE}` drop index `{UNIQUE_INDEX}`")
	frappe.db.commit()
