# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0100 — extend Published-output DB trigger for new metadata columns."""

from __future__ import annotations

import frappe


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
	table = "tabTender STD Generated Output"
	if not _table_exists(table):
		return
	if not _column_exists(table, "tender_code") or not _column_exists(table, "supersedes_output_code"):
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
					new.generated_by_job_code <=> old.generated_by_job_code and
					new.tender_code <=> old.tender_code and
					new.supersedes_output_code <=> old.supersedes_output_code
				) then
					signal sqlstate '45000'
						set message_text = 'STDINST-1300: published output immutable fields changed';
				end if;
			end if;
		end
		"""
	)
