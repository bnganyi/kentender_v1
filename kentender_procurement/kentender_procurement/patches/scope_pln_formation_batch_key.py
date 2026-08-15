"""Scope formation idempotency batches to their owning logical Plan."""

from __future__ import annotations

import frappe


def execute() -> None:
	index = frappe.db.sql(
		"show index from `tabProcurement Plan Item` where Key_name='uniq_pln_formation_batch'",
		as_dict=True,
	)
	columns = [row.Column_name for row in sorted(index, key=lambda row: row.Seq_in_index)]
	if columns == ["plan", "formation_idempotency_key", "formation_batch_index"]:
		return
	if index:
		frappe.db.sql_ddl(
			"alter table `tabProcurement Plan Item` drop index `uniq_pln_formation_batch`"
		)
	frappe.db.sql_ddl(
		"alter table `tabProcurement Plan Item` add unique index `uniq_pln_formation_batch` "
		"(`plan`, `formation_idempotency_key`, `formation_batch_index`)"
	)
