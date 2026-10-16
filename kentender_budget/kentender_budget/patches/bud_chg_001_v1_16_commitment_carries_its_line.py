# Copyright (c) 2026, KenTender and contributors
"""BUD-CHG-001 v1.16 §4.6 — a Procurement Commitment carries the Budget Line it is charged to (and its Budget), an origin, and an optional entry row and lineage.

Every commitment so far was made by converting a reservation, so its line and Budget are its reservation's, its origin is `Reservation conversion` and it has no entry row. The v1.12 key (contract, reservation)
stays: an existing-contract entry's commitment has no reservation, and a NULL does not collide. Each entry row funds one commitment, once: `entry_row` is unique (NULL for every conversion).
Idempotent; safe to run again."""

from __future__ import annotations

import frappe

TABLE = "tabProcurement Commitment"
ENTRY_ROW_KEY = "uq_commitment_entry_row"
CONVERSION_KEY = "uq_commitment_contract_reservation"  # the v1.12 key
SUPERSEDED_KEY = "uq_commitment_contract_reservation_row"  # an earlier draft of this change put the entry row inside the key; a NULL reservation would have let duplicates through


def execute() -> None:
	if not frappe.db.table_exists("Procurement Commitment"):
		return
	frappe.reload_doc("kentender_budget", "doctype", "procurement_commitment", force=True)
	frappe.db.sql(
		f"""update `{TABLE}` c join `tabFunding Reservation` r on r.name = c.reservation
		set c.budget_line = r.budget_line, c.budget = r.budget
		where c.reservation is not null and c.reservation != '' and (c.budget_line is null or c.budget_line = '' or c.budget is null or c.budget = '')"""
	)
	frappe.db.sql(f"update `{TABLE}` set origin = 'Reservation conversion' where origin is null or origin = ''")
	frappe.db.sql(f"update `{TABLE}` set entry_row = null where entry_row = ''")
	if frappe.db.has_index(TABLE, SUPERSEDED_KEY):
		frappe.db.sql_ddl(f"alter table `{TABLE}` drop index `{SUPERSEDED_KEY}`")
	if not frappe.db.has_index(TABLE, CONVERSION_KEY):
		frappe.db.sql_ddl(f"alter table `{TABLE}` add unique key `{CONVERSION_KEY}` (`contract`, `reservation`)")
	if not frappe.db.has_index(TABLE, ENTRY_ROW_KEY):
		frappe.db.sql_ddl(f"alter table `{TABLE}` add unique key `{ENTRY_ROW_KEY}` (`entry_row`)")
	frappe.db.commit()
