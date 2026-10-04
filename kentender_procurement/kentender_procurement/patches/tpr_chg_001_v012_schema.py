# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 (plan D2′, W7) — the delta schema on the dev site.

- Tender Addendum: v0.8's `issued_by`/`issued_at` (the HOPF decision) become
  `issue_decided_by`/`issue_decided_at`; v0.8's `effective_at` (the latest
  channel availability) becomes `issued_at` (§4.8). Copied in that order,
  then the orphaned columns are dropped.
- Tender Channel Confirmation: subject type "Publication" is "Tender
  package" (§4.7), and (subject_type, subject_id, channel) is unique in the
  database, not only in application code.
- Tender Task: "Inquiry response" is "Clarification response".
- Tender Addendum Inquiry is removed (replaced by Tender Clarification; a
  free-text candidate identity cannot be mapped to a candidate registration,
  so rows are not migrated — the canonical world is reseeded).
"""

from __future__ import annotations

import frappe

ADDENDUM = "tabTender Addendum"
CONFIRMATION = "Tender Channel Confirmation"
RETIRED = "Tender Addendum Inquiry"


def execute() -> None:
	columns = set(frappe.db.get_table_columns("Tender Addendum"))
	if {"issued_by", "effective_at", "issue_decided_by", "issue_decided_at", "issued_at"} <= columns:
		# MariaDB evaluates single-table SET assignments left to right, so
		# issue_decided_at takes the old issued_at before issued_at is replaced.
		frappe.db.sql(
			f"update `{ADDENDUM}` set issue_decided_by = issued_by, issue_decided_at = issued_at, issued_at = effective_at where issue_decided_by is null"
		)
		for column in ("issued_by", "effective_at"):
			frappe.db.sql_ddl(f"alter table `{ADDENDUM}` drop column `{column}`")

	frappe.db.sql("update `tabTender Channel Confirmation` set subject_type = 'Tender package' where subject_type = 'Publication'")
	duplicates = frappe.db.sql(
		"select subject_type, subject_id, channel, count(*) from `tabTender Channel Confirmation` group by subject_type, subject_id, channel having count(*) > 1"
	)
	if duplicates:
		raise Exception(f"Duplicate channel confirmations must be resolved before the unique index can be added: {duplicates}")
	frappe.db.add_unique(CONFIRMATION, ["subject_type", "subject_id", "channel"], constraint_name="tender_channel_confirmation_subject_channel")

	frappe.db.sql("update `tabTender Task` set task_type = 'Clarification response' where task_type = 'Inquiry response'")

	if frappe.db.exists("DocType", RETIRED):
		frappe.delete_doc("DocType", RETIRED, force=True, ignore_permissions=True, delete_permanently=True)
	frappe.db.sql_ddl(f"drop table if exists `tab{RETIRED}`")
