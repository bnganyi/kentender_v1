# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1300 — DB-backed safeguards for STD instance persistence rules."""

from __future__ import annotations

import frappe

RELEASED_STATUSES = ("Superseded", "Cancelled")


def _table_exists(table_name: str) -> bool:
	return bool(
		frappe.db.sql(
			"""
			select 1
			from information_schema.tables
			where table_schema = database()
			  and table_name = %s
			limit 1
			""",
			(table_name,),
		)
	)


def _column_exists(table_name: str, column_name: str) -> bool:
	return bool(
		frappe.db.sql(
			"""
			select 1
			from information_schema.columns
			where table_schema = database()
			  and table_name = %s
			  and column_name = %s
			limit 1
			""",
			(table_name, column_name),
		)
	)


def _index_exists(table_name: str, index_name: str) -> bool:
	return bool(
		frappe.db.sql(
			"""
			select 1
			from information_schema.statistics
			where table_schema = database()
			  and table_name = %s
			  and index_name = %s
			limit 1
			""",
			(table_name, index_name),
		)
	)


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


def _add_active_slot_column_and_unique_index() -> None:
	table = "tabTender STD Instance"
	if not _table_exists(table):
		return

	if not _column_exists(table, "active_tender_slot"):
		frappe.db.sql_ddl(
			"""
			alter table `tabTender STD Instance`
			add column `active_tender_slot` varchar(140) null
			"""
		)

	if _column_exists(table, "tm2_tender") and _column_exists(table, "procurement_tender"):
		_slot_sql = """
		update `tabTender STD Instance`
		set active_tender_slot = case
			when instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(coalesce(nullif(trim(`tm2_tender`), ''), nullif(trim(`procurement_tender`), ''))), '')
		end
		"""
	elif _column_exists(table, "tm2_tender"):
		_slot_sql = """
		update `tabTender STD Instance`
		set active_tender_slot = case
			when instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(`tm2_tender`), '')
		end
		"""
	elif _column_exists(table, "procurement_tender"):
		_slot_sql = """
		update `tabTender STD Instance`
		set active_tender_slot = case
			when instance_status in ('Superseded', 'Cancelled') then null
			else nullif(trim(`procurement_tender`), '')
		end
		"""
	else:
		_slot_sql = None
	if _slot_sql:
		frappe.db.sql(_slot_sql)

	duplicates = frappe.db.sql(
		"""
		select active_tender_slot, count(*)
		from `tabTender STD Instance`
		where active_tender_slot is not null and active_tender_slot != ''
		group by active_tender_slot
		having count(*) > 1
		"""
	)
	if duplicates:
		frappe.throw(
			"STDINST-1300 cannot add unique active-slot index; duplicate active STD Instances exist."
		)

	if not _index_exists(table, "uniq_stdinst_active_tender_slot"):
		frappe.db.sql_ddl(
			"""
			alter table `tabTender STD Instance`
			add unique key `uniq_stdinst_active_tender_slot` (`active_tender_slot`)
			"""
		)

	_drop_trigger_if_exists("trg_stdinst_active_slot_bi")
	_drop_trigger_if_exists("trg_stdinst_active_slot_bu")

	if _column_exists(table, "tm2_tender") and _column_exists(table, "procurement_tender"):
		_slot_expr = (
			"nullif(trim(coalesce(nullif(trim(new.`tm2_tender`), ''), "
			"nullif(trim(new.`procurement_tender`), ''))), '')"
		)
	elif _column_exists(table, "tm2_tender"):
		_slot_expr = "nullif(trim(new.`tm2_tender`), '')"
	elif _column_exists(table, "procurement_tender"):
		_slot_expr = "nullif(trim(new.`procurement_tender`), '')"
	else:
		_slot_expr = ""

	if _slot_expr:
		frappe.db.sql_ddl(
			f"""
			create trigger `trg_stdinst_active_slot_bi`
			before insert on `tabTender STD Instance`
			for each row
			set new.active_tender_slot = case
				when new.instance_status in ('Superseded', 'Cancelled') then null
				else {_slot_expr}
			end
			"""
		)
		frappe.db.sql_ddl(
			f"""
			create trigger `trg_stdinst_active_slot_bu`
			before update on `tabTender STD Instance`
			for each row
			set new.active_tender_slot = case
				when new.instance_status in ('Superseded', 'Cancelled') then null
				else {_slot_expr}
			end
			"""
		)


def _add_output_uniqueness_constraint() -> None:
	table = "tabTender STD Generated Output"
	if not _table_exists(table):
		return
	if not _index_exists(table, "uniq_stdout_instance_type_version"):
		frappe.db.sql_ddl(
			"""
			alter table `tabTender STD Generated Output`
			add unique key `uniq_stdout_instance_type_version`
			(`tender_std_instance`, `output_type`, `version_number`)
			"""
		)


def _add_attachment_uniqueness_constraints() -> None:
	table = "tabTender STD Instance Section Attachment"
	if not _table_exists(table):
		return
	if not _index_exists(table, "uniq_stdatt_parent_attachment_code"):
		frappe.db.sql_ddl(
			"""
			alter table `tabTender STD Instance Section Attachment`
			add unique key `uniq_stdatt_parent_attachment_code`
			(`parent`, `attachment_code`)
			"""
		)
	if not _index_exists(table, "uniq_stdatt_parent_supersedes_version"):
		frappe.db.sql_ddl(
			"""
			alter table `tabTender STD Instance Section Attachment`
			add unique key `uniq_stdatt_parent_supersedes_version`
			(`parent`, `supersedes_attachment_code`, `version_number`)
			"""
		)


def _add_generated_output_immutability_trigger() -> None:
	table = "tabTender STD Generated Output"
	if not _table_exists(table):
		return

	_drop_trigger_if_exists("trg_stdout_published_immutable_bu")
	frappe.db.sql_ddl(
		"""
		create trigger `trg_stdout_published_immutable_bu`
		before update on `tabTender STD Generated Output`
		for each row
		begin
			if old.output_status = 'Published' then
				if not (new.output_status in ('Published', 'Superseded', 'Stale')) then
					signal sqlstate '45000'
						set message_text = 'STDINST-1300: published output invalid status change';
				end if;

				if not (
					new.tender_std_instance <=> old.tender_std_instance and
					new.output_type <=> old.output_type and
					new.version_number <=> old.version_number and
					new.content_json <=> old.content_json and
					new.input_hash <=> old.input_hash and
					new.output_hash <=> old.output_hash and
					new.source_template_version_code <=> old.source_template_version_code and
					new.source_profile_code <=> old.source_profile_code and
					new.source_instance_snapshot_code <=> old.source_instance_snapshot_code and
					new.source_addendum_code <=> old.source_addendum_code and
					new.rendered_file_reference <=> old.rendered_file_reference and
					new.generated_by_job_code <=> old.generated_by_job_code
				) then
					signal sqlstate '45000'
						set message_text = 'STDINST-1300: published output immutable fields changed';
				end if;
			end if;
		end
		"""
	)


def _add_snapshot_append_only_trigger() -> None:
	table = "tabTender STD Instance Snapshot"
	if not _table_exists(table):
		return

	tender_checks: list[str] = []
	if _column_exists(table, "procurement_tender"):
		tender_checks.append("new.procurement_tender <=> old.procurement_tender")
	if _column_exists(table, "tm2_tender"):
		tender_checks.append("new.tm2_tender <=> old.tm2_tender")
	tender_clause = " and\n					".join(tender_checks) if tender_checks else "1"

	_drop_trigger_if_exists("trg_stdsnap_final_append_only_bu")
	frappe.db.sql_ddl(
		f"""
		create trigger `trg_stdsnap_final_append_only_bu`
		before update on `tabTender STD Instance Snapshot`
		for each row
		begin
			if old.snapshot_status = 'Final' then
				if not (new.snapshot_status in ('Final', 'Superseded', 'Archived')) then
					signal sqlstate '45000'
						set message_text = 'STDINST-1300: final snapshot invalid status change';
				end if;

				if not (
					new.tender_std_instance <=> old.tender_std_instance and
					{tender_clause} and
					new.snapshot_type <=> old.snapshot_type and
					new.snapshot_reason <=> old.snapshot_reason and
					new.source_template_version_code <=> old.source_template_version_code and
					new.source_addendum_code <=> old.source_addendum_code and
					new.ref_bundle_output <=> old.ref_bundle_output and
					new.ref_dsm_output <=> old.ref_dsm_output and
					new.ref_dom_output <=> old.ref_dom_output and
					new.ref_dem_output <=> old.ref_dem_output and
					new.ref_dcm_output <=> old.ref_dcm_output and
					new.parameter_values_hash <=> old.parameter_values_hash and
					new.works_requirements_hash <=> old.works_requirements_hash and
					new.attachments_hash <=> old.attachments_hash and
					new.boq_hash <=> old.boq_hash and
					new.complete_instance_hash <=> old.complete_instance_hash
				) then
					signal sqlstate '45000'
						set message_text = 'STDINST-1300: final snapshot evidence changed';
				end if;
			end if;
		end
		"""
	)


def execute() -> None:
	_add_active_slot_column_and_unique_index()
	_add_output_uniqueness_constraint()
	_add_attachment_uniqueness_constraints()
	_add_generated_output_immutability_trigger()
	_add_snapshot_append_only_trigger()
