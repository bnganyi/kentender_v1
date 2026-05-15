# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6 / phase 6 — dev-only wipe of legacy ``Procurement Tender`` link columns + rows.

Runs **before** model sync removes the DocType from disk so migrate can drop tables/columns
without integrity surprises. Safe to re-run (no-op when columns / table are already gone).
"""

from __future__ import annotations

import frappe
from frappe.utils import get_table_name


def _trigger_exists(trigger_name: str) -> bool:
	return bool(
		frappe.db.sql(
			"""
			select 1
			from information_schema.triggers
			where trigger_schema = database()
			  and trigger_name = %s
			limit 1
			""",
			(trigger_name,),
		)
	)


def _drop_trigger_if_exists(trigger_name: str) -> None:
	if _trigger_exists(trigger_name):
		frappe.db.sql_ddl(f"drop trigger `{trigger_name}`")


def _null_link(doctype: str, fieldname: str) -> None:
	if not frappe.db.exists("DocType", doctype):
		return
	if not frappe.db.has_column(doctype, fieldname):
		return
	table = get_table_name(doctype)
	frappe.db.sql(
		f"update `{table}` set `{fieldname}` = NULL where `{fieldname}` is not null and `{fieldname}` != ''"
	)


def execute() -> None:
	# Must run before ALTER drops ``procurement_tender`` (STDINST triggers / snapshot guard reference it).
	_drop_trigger_if_exists("trg_stdinst_active_slot_bi")
	_drop_trigger_if_exists("trg_stdinst_active_slot_bu")
	_drop_trigger_if_exists("trg_stdsnap_final_append_only_bu")

	for dt, fn in (
		("Tender STD Instance", "procurement_tender"),
		("Tender STD Instance Snapshot", "procurement_tender"),
		("Tender Publication Snapshot", "procurement_tender"),
		("Tender Publication Approval Decision", "procurement_tender"),
	):
		_null_link(dt, fn)

	if frappe.db.table_exists("tabProcurement Tender"):
		frappe.db.sql("delete from `tabProcurement Tender`")

	frappe.db.commit()
