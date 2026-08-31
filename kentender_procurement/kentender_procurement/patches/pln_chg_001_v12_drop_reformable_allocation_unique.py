# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 Phase 6 — drop the over-strict allocation unique index.

`pln_chg_001_v12_planning_unique_indexes` originally added a plain composite
unique on (plan_version, dpp_entry). §4.10 requires a source whose allocation
was dissolved (allocation_state Released) to become available for
re-formation in the *same* Plan Version — MariaDB has no partial/filtered
unique index to exempt Released rows, so the plain composite unique blocked
every re-formation, found live by Phase 6's dissolve-then-re-form test. The
invariant it existed for is fully covered instead by `FormPlanItems` row-
locking the Annual Plan Version before creating any allocation
(services/plan_workbench.py) — every command that could double-allocate a
source already serialises on that lock.
"""

from __future__ import annotations

import frappe


def execute() -> None:
	existing = frappe.db.sql(
		"""select 1 from information_schema.statistics
		where table_schema = database() and table_name = %s and index_name = %s
		limit 1""",
		("tabPlan Source Allocation", "pln_uniq_entry_per_version"),
	)
	if existing:
		frappe.db.sql_ddl(
			"alter table `tabPlan Source Allocation` drop index `pln_uniq_entry_per_version`"
		)
