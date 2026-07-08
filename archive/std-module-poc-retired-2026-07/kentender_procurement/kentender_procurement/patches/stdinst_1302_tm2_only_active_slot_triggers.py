# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1302 — ``active_tender_slot`` triggers after ``procurement_tender`` column drop (TM2-only).

Replaces STDINST-1301 triggers that referenced ``procurement_tender``.
"""

from __future__ import annotations

import frappe


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


def execute() -> None:
	if not frappe.db.has_column("Tender STD Instance", "tm2_tender"):
		return

	table = "tabTender STD Instance"
	_drop_trigger_if_exists("trg_stdinst_active_slot_bi")
	_drop_trigger_if_exists("trg_stdinst_active_slot_bu")

	frappe.db.sql(
		f"""
		update `{table}`
		set active_tender_slot = case
			when instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(`tm2_tender`), '')
		end
		"""
	)

	frappe.db.sql_ddl(
		f"""
		create trigger `trg_stdinst_active_slot_bi`
		before insert on `{table}`
		for each row
		set new.active_tender_slot = case
			when new.instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(new.`tm2_tender`), '')
		end
		"""
	)
	frappe.db.sql_ddl(
		f"""
		create trigger `trg_stdinst_active_slot_bu`
		before update on `{table}`
		for each row
		set new.active_tender_slot = case
			when new.instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(new.`tm2_tender`), '')
		end
		"""
	)
