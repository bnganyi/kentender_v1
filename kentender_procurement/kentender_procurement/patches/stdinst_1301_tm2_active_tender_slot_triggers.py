# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1301 — ``active_tender_slot`` triggers include **TM2 Tender** (TM2-only convergence).

``stdinst_1300_db_constraints`` installed triggers that only copied ``procurement_tender``, leaving
TM2-bound instances with a null slot. Recreate triggers using
``coalesce(nullif(trim(tm2_tender),''), nullif(trim(procurement_tender),''))`` and backfill rows.
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
	table = "tabTender STD Instance"
	_drop_trigger_if_exists("trg_stdinst_active_slot_bi")
	_drop_trigger_if_exists("trg_stdinst_active_slot_bu")

	frappe.db.sql(
		"""
		update `tabTender STD Instance`
		set active_tender_slot = case
			when instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(coalesce(nullif(trim(`tm2_tender`), ''), nullif(trim(`procurement_tender`), ''))), '')
		end
		"""
	)

	frappe.db.sql_ddl(
		"""
		create trigger `trg_stdinst_active_slot_bi`
		before insert on `tabTender STD Instance`
		for each row
		set new.active_tender_slot = case
			when new.instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(coalesce(nullif(trim(new.`tm2_tender`), ''), nullif(trim(new.`procurement_tender`), ''))), '')
		end
		"""
	)
	frappe.db.sql_ddl(
		"""
		create trigger `trg_stdinst_active_slot_bu`
		before update on `tabTender STD Instance`
		for each row
		set new.active_tender_slot = case
			when new.instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(coalesce(nullif(trim(new.`tm2_tender`), ''), nullif(trim(new.`procurement_tender`), ''))), '')
		end
		"""
	)
