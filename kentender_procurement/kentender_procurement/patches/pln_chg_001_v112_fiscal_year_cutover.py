# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §1.1 (v1.5 rows) — the Fiscal Year cutover (tracker D7).

Post model sync: the new `fiscal_year` columns exist. Carry each row's legacy
`financial_year` (KenTender `Financial Year`, named `FY-{start}-{end}`) onto
the ERPNext `Fiscal Year` of the same period (`{start}-{end}`), then drop the
retired columns (`pe_fy_context`, `procuring_entity`, `financial_year`, the
per-item Finance fields, the flat planned dates) and rekey the DPP-root unique
onto (`fiscal_year`, `organisation_unit`). Idempotent.
"""

from __future__ import annotations

import frappe

FY_TABLES = ("tabDepartmental Plan", "tabDepartmental Plan Validation Task", "tabAnnual Plan")

DROP_COLUMNS = {
	"tabDepartmental Plan": ("pe_fy_context", "procuring_entity", "financial_year"),
	"tabDepartmental Plan Validation Task": ("procuring_entity", "financial_year"),
	"tabAnnual Plan": ("pe_fy_context", "procuring_entity", "financial_year"),
	"tabAnnual Plan Item": (
		"finance_state", "invitation_date", "bid_opening_date", "evaluation_completion_date",
		"award_approval_date", "award_notification_date", "contract_signing_date",
		"delivery_completion_date",
	),
	"tabPlan Finance Task": ("plan_item", "plan_item_id", "procuring_entity", "source_set_hash", "required_amount"),
	"tabPlan Governance Task": ("procuring_entity",),
	"tabPlan Governance Decision": ("procuring_entity",),
}


def _has_column(table: str, column: str) -> bool:
	return bool(
		frappe.db.sql(
			"""select 1 from information_schema.columns
			where table_schema = database() and table_name = %s and column_name = %s""",
			(table, column),
		)
	)


def _drop_index(table: str, index: str) -> None:
	if frappe.db.sql(
		"""select 1 from information_schema.statistics
		where table_schema = database() and table_name = %s and index_name = %s limit 1""",
		(table, index),
	):
		frappe.db.sql_ddl(f"alter table `{table}` drop index `{index}`")


def execute() -> None:
	for table in FY_TABLES:
		if _has_column(table, "financial_year") and _has_column(table, "fiscal_year"):
			frappe.db.sql(
				f"""update `{table}` set fiscal_year = substring(financial_year, 4)
				where (fiscal_year is null or fiscal_year = '') and financial_year like 'FY-%%'"""
			)
	# the DPP-root unique was keyed on the retired context column
	_drop_index("tabDepartmental Plan", "pln_uniq_dpp_root")
	for table, columns in DROP_COLUMNS.items():
		for column in columns:
			if _has_column(table, column):
				frappe.db.sql_ddl(f"alter table `{table}` drop column `{column}`")
	if _has_column("tabDepartmental Plan", "fiscal_year") and not frappe.db.sql(
		"""select 1 from information_schema.statistics
		where table_schema = database() and table_name = 'tabDepartmental Plan' and index_name = 'pln_uniq_dpp_root' limit 1"""
	):
		frappe.db.sql_ddl(
			"alter table `tabDepartmental Plan` add unique index `pln_uniq_dpp_root` (`fiscal_year`, `organisation_unit`)"
		)
	frappe.db.commit()
