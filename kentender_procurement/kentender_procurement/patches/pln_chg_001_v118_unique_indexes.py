# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.10 — composite uniqueness the doctype JSONs cannot
declare (post_model_sync, idempotent; runs after `pln_chg_001_v118_plan_item_roots`
so every row already carries its stable link)."""

from __future__ import annotations

import frappe

INDEXES = (
	# §4.6: one content row per stable item per Plan Version
	("tabAnnual Plan Item", "pln_uniq_item_root_per_version", ("plan_item", "plan_version")),
	# §4.8: event uniqueness by producer + event id
	("tabMilestone Actual Event", "pln_uniq_actual_event", ("producer", "event_id")),
	# §4.9: one logical publication per approved snapshot and destination; attempts are a sequence
	("tabPlan Publication", "pln_uniq_publication", ("snapshot", "destination")),
	("tabPublication Attempt", "pln_uniq_attempt", ("publication", "attempt_number")),
	# §4.8: one coverage row per proceeding and allocation
	("tabProceeding Coverage", "pln_uniq_coverage", ("proceeding_type", "proceeding_id", "allocation")),
)
# `Plan Source Allocation` (plan_version, source_key) is deliberately NOT a DB
# unique: a Released allocation is historical and may be re-formed (§4.6), which
# a plain composite unique cannot express on MariaDB — the Annual Plan Version
# row lock in `plan_workbench` serialises formation instead (v1.12 precedent).


def execute() -> None:
	for table, index, columns in INDEXES:
		existing = frappe.db.sql(
			"""select 1 from information_schema.statistics
			where table_schema = database() and table_name = %s and index_name = %s limit 1""",
			(table, index),
		)
		if existing:
			continue
		cols = ", ".join(f"`{c}`" for c in columns)
		frappe.db.sql_ddl(f"alter table `{table}` add unique index `{index}` ({cols})")
