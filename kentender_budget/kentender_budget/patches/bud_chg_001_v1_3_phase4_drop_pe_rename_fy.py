# Copyright (c) 2026, KenTender and contributors
"""BUD-CHG-001 v1.3 Phase 4 (§4.1, §17.1) — drop `procuring_entity` and
rename `financial_year` to `fiscal_year` on `Procurement Budget`, repointed
at the real ERPNext `Fiscal Year`.

Must run in [pre_model_sync]: the app's own doctype JSON on disk already
carries the new shape (no `procuring_entity`, field named `fiscal_year`), so
by the time schema sync runs, `financial_year` would already look like a
column schema sync should drop and `fiscal_year` one it should create empty
— losing data. Renaming the column here, before sync, means sync finds
`fiscal_year` already in place and does nothing destructive to it.

The renamed column initially still holds the old KenTender `Financial Year`
docname, not a valid ERPNext `Fiscal Year` name — the second step below
remaps by matching start year, since that is the only correspondence
available between the two doctypes.

Frappe's schema sync does not drop a column on its own just because the
field was removed from the DocType JSON (confirmed directly: `procuring_entity`
survived a full `bench migrate` after the field was deleted from
`procurement_budget.json`, the same behaviour
`pln_chg_016_schema_cleanup.py` already works around) — the explicit `drop
column` below is required, not optional cleanup.
"""

from __future__ import annotations

import frappe

TABLE = "tabProcurement Budget"


def execute() -> None:
	if not frappe.db.table_exists("Procurement Budget"):
		return

	if frappe.db.has_column("Procurement Budget", "financial_year") and not frappe.db.has_column(
		"Procurement Budget", "fiscal_year"
	):
		frappe.db.sql_ddl(f"alter table `{TABLE}` change column `financial_year` `fiscal_year` varchar(140)")
		_clear_column_cache()

	if frappe.db.has_column("Procurement Budget", "fiscal_year"):
		_remap_financial_year_values_to_fiscal_year()

	if frappe.db.has_column("Procurement Budget", "procuring_entity"):
		frappe.db.sql_ddl(f"alter table `{TABLE}` drop column `procuring_entity`")
		_clear_column_cache()

	frappe.db.commit()


def _clear_column_cache() -> None:
	"""`frappe.db.has_column`/`get_table_columns` cache the DB column list in
	Redis (`table_columns::{table}`), keyed with no TTL — a raw DDL call like
	the ones above bypasses the normal schema-sync path that would otherwise
	clear it, so a later `has_column` check (in this same patch or anywhere
	else) would read a stale pre-DDL column list without this."""
	frappe.client_cache.delete_value(f"table_columns::{TABLE}")


def _remap_financial_year_values_to_fiscal_year() -> None:
	"""Best-effort remap of legacy `Financial Year` references to the ERPNext
	`Fiscal Year` with the same start year. Any row whose value cannot be
	resolved this way is cleared rather than left pointing at a Link target
	that no longer exists — there is no other correspondence to remap from."""
	if not (frappe.db.exists("DocType", "Financial Year") and frappe.db.table_exists("Financial Year")):
		# The old doctype is itself already gone: nothing to remap from, and
		# any lingering value is already an orphaned reference — clear it.
		frappe.db.sql(f"update `{TABLE}` set fiscal_year = NULL where fiscal_year is not null")
		return

	legacy_years = frappe.db.sql("select `name`, `start_year` from `tabFinancial Year`", as_dict=True)
	for legacy in legacy_years:
		match = frappe.db.sql(
			"select `name` from `tabFiscal Year` where year(`year_start_date`) = %s limit 1",
			(legacy.start_year,),
		)
		if not match:
			continue
		frappe.db.sql(
			f"update `{TABLE}` set fiscal_year = %s where fiscal_year = %s",
			(match[0][0], legacy.name),
		)

	# Anything left that isn't a real Fiscal Year name (no matching legacy
	# year, or a value that was never a Financial Year docname at all) is an
	# unresolvable reference — clear rather than leave dangling.
	frappe.db.sql(
		f"update `{TABLE}` set fiscal_year = NULL "
		"where fiscal_year is not null and fiscal_year not in (select `name` from `tabFiscal Year`)"
	)
