# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1303 — recreate Final snapshot append-only trigger without ``procurement_tender``.

``stdinst_1300`` installed a trigger comparing ``procurement_tender``; that column is removed in TM2-only
convergence. ``p6_clear_procurement_tender_dev`` drops this trigger pre-migrate; this patch reinstalls it.
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
	table = "tabTender STD Instance Snapshot"
	if not frappe.db.table_exists(table):
		return
	if not frappe.db.has_column("Tender STD Instance Snapshot", "tm2_tender"):
		return

	_drop_trigger_if_exists("trg_stdsnap_final_append_only_bu")

	frappe.db.sql_ddl(
		f"""
		create trigger `trg_stdsnap_final_append_only_bu`
		before update on `{table}`
		for each row
		begin
			if old.snapshot_status = 'Final' then
				if not (new.snapshot_status in ('Final', 'Superseded', 'Archived')) then
					signal sqlstate '45000'
						set message_text = 'STDINST-1300: final snapshot invalid status change';
				end if;

				if not (
					new.tender_std_instance <=> old.tender_std_instance and
					new.tm2_tender <=> old.tm2_tender and
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
