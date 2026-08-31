# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 Phase 1 — composite DB uniqueness for invariants 2, 17 and 24.

Single-column uniques (Annual Plan per PE/FY context, one submission per DPP
Version) are declared in the doctype JSONs; the composite constraints below
cannot be, so they are created here (post_model_sync, idempotent).
"""

from __future__ import annotations

import frappe

INDEXES = (
	# invariant 2: one DPP root per PE/FY context + OU
	("tabDepartmental Plan", "pln_uniq_dpp_root", ("pe_fy_context", "organisation_unit")),
	# monotonic version sequences cannot collide
	("tabDepartmental Plan Version", "pln_uniq_dpp_version", ("departmental_plan", "version_number")),
	# stable entry ids are unique within one DPP Version; successor copies reuse them
	("tabDepartmental Plan Entry", "pln_uniq_entry_id_per_version", ("dpp_version", "entry_id")),
	("tabAnnual Plan Version", "pln_uniq_plan_version", ("annual_plan", "version_number")),
	# stable item / allocation ids are unique within one Plan Version
	("tabAnnual Plan Item", "pln_uniq_item_per_version", ("plan_version", "plan_item_id")),
	("tabPlan Source Allocation", "pln_uniq_alloc_per_version", ("plan_version", "allocation_id")),
)
# Invariant 7 (one accepted DPP entry allocated at most once per Plan Version)
# is deliberately NOT a DB unique on (plan_version, dpp_entry): §4.10 requires
# a Released allocation to stop blocking re-formation, and MariaDB has no
# partial/filtered unique index to exempt Released rows. `FormPlanItems`
# already row-locks the Annual Plan Version before creating any allocation
# (services/plan_workbench.py), which fully serialises every command that
# could double-allocate a source — the same guarantee a DB unique would add,
# without permanently barring a dissolved-then-released source. A plain
# composite unique here shipped in this patch's first version and was found
# live in Phase 6 blocking exactly that re-formation path; dropped by
# pln_chg_001_v12_drop_reformable_allocation_unique.


def execute() -> None:
	for table, index, columns in INDEXES:
		existing = frappe.db.sql(
			"""select 1 from information_schema.statistics
			where table_schema = database() and table_name = %s and index_name = %s
			limit 1""",
			(table, index),
		)
		if existing:
			continue
		cols = ", ".join(f"`{c}`" for c in columns)
		frappe.db.sql_ddl(f"alter table `{table}` add unique index `{index}` ({cols})")
