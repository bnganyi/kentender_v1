# Copyright (c) 2026, KenTender and contributors
"""BUD v1.12 §4.6 (AUD-BUD-004) — `Procurement Commitment.contract` was unique
table-wide, so one contract funded from two reservations (the document's own
two-department fixture, 20m + 30m) could not be converted in full. The rule is
"unique within the reservation lineage" and "one reservation may convert into
more than one commitment": the natural key is (contract, reservation).

Drops the table-wide unique index on `contract` and adds the unique
(contract, reservation) key. Idempotent; the plain `contract_index` stays for
lookups.
"""

from __future__ import annotations

import frappe

TABLE = "tabProcurement Commitment"
TABLE_WIDE_UNIQUE = "contract"
PER_RESERVATION_UNIQUE = "uq_commitment_contract_reservation"


def execute() -> None:
	if not frappe.db.table_exists("Procurement Commitment"):
		return
	if frappe.db.has_index(TABLE, TABLE_WIDE_UNIQUE):
		frappe.db.sql_ddl(f"alter table `{TABLE}` drop index `{TABLE_WIDE_UNIQUE}`")
	if not frappe.db.has_index(TABLE, PER_RESERVATION_UNIQUE):
		frappe.db.sql_ddl(f"alter table `{TABLE}` add unique key `{PER_RESERVATION_UNIQUE}` (`contract`, `reservation`)")
	frappe.db.commit()
