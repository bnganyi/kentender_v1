# Copyright (c) 2026, KenTender and contributors
"""BUD-CHG-001 v1.3 Phase 4 (BUD-BR-002, §17.1) — the database-level guard
that at most one `Procurement Budget Version` is Active per Budget (a Budget
already being at most one per Fiscal Year, via `fiscal_year`'s own unique
constraint). MariaDB has no native partial unique index, so this uses the
standard workaround: a STORED generated column that is NULL unless the row
is Active, made unique — MariaDB unique indexes treat NULL as distinct, so
only rows that are actually Active can ever collide.

Application-level checks (`_active_version`, `approve_budget_version`'s
prior-Active supersession) are not a substitute for this — "Serialization
alone is insufficient" (BUD-BR-002) is the reason this patch exists at all.
"""

from __future__ import annotations

import frappe

TABLE = "tabProcurement Budget Version"
COLUMN = "active_budget_marker"
INDEX = "uq_procurement_budget_version_active_budget"


def execute() -> None:
	if not frappe.db.table_exists("Procurement Budget Version"):
		return

	if not frappe.db.has_column("Procurement Budget Version", COLUMN):
		frappe.db.sql_ddl(
			f"alter table `{TABLE}` "
			f"add column `{COLUMN}` varchar(140) "
			f"generated always as (case when `status` = 'Active' then `budget` else null end) stored"
		)
		# Raw DDL bypasses the schema-sync path that would otherwise clear
		# `frappe.db.has_column`'s Redis-cached column list for this table.
		frappe.client_cache.delete_value(f"table_columns::{TABLE}")

	if not frappe.db.has_index(TABLE, INDEX):
		frappe.db.sql_ddl(f"alter table `{TABLE}` add unique key `{INDEX}` (`{COLUMN}`)")

	frappe.db.commit()
