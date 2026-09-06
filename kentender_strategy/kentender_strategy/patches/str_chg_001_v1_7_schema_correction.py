# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 §16.1 / STR-AC-033 — physical schema correction.

CU-303 dropped `procuring_entity_id`, `pe_fy_context` and `owner_org_unit_id`
from the Strategic Plan *contract* but left the columns "until the removal
phase"; and CU-305 repointed `Performance Target.financial_year_id` at the
ERPNext Fiscal Year without renaming it to the spec's `fiscal_year`. This is
that removal phase:

- copy `financial_year_id` into the new `fiscal_year` column, then drop the
  old column;
- drop the three retired Strategic Plan columns.

Frappe's doctype sync only ever adds columns, so a site that synced the old
JSON keeps the retired columns forever unless something drops them — which
would let STR-AC-033's "no reference exists in schema" claim be true of the
JSON and false of the database.
"""

from __future__ import annotations

import frappe


def _drop(doctype: str, column: str) -> None:
	if frappe.db.has_column(doctype, column):
		frappe.db.sql_ddl(f"ALTER TABLE `tab{doctype}` DROP COLUMN `{column}`")


def execute() -> None:
	frappe.reload_doc("kentender_strategy", "doctype", "strategic_plan")
	frappe.reload_doc("kentender_strategy", "doctype", "performance_target")

	if frappe.db.has_column("Performance Target", "financial_year_id"):
		frappe.db.sql(
			"""
			UPDATE `tabPerformance Target`
			SET `fiscal_year` = `financial_year_id`
			WHERE IFNULL(`fiscal_year`, '') = '' AND IFNULL(`financial_year_id`, '') != ''
			"""
		)
		_drop("Performance Target", "financial_year_id")

	for column in ("procuring_entity_id", "pe_fy_context", "owner_org_unit_id"):
		_drop("Strategic Plan", column)
	frappe.db.commit()
