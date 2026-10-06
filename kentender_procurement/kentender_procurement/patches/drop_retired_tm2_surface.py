# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Drop the retired Tender Management v2 (TM2) site records (owner decision D1, 6 Oct 2026).

TM2 is permanently retired. Its code, doctype JSON, Desk page and assets are deleted
from the repository, so a site that was migrated before the deletion still carries the
metadata and (empty) tables. This patch is the only place the retired names remain.

Safe by construction:

* Nothing is deleted through ``frappe.delete_doc``. In developer mode that removes
  files under the app and fires document events; the files are already gone and the
  doctypes are no longer importable. Raw, existence-guarded deletes only.
* Idempotent: every statement is guarded, so running it on a site where the records
  are already gone (or twice) changes nothing and raises nothing.
* Data-safe: it refuses to drop a table that holds rows, so a site that unexpectedly
  carries TM2 records stops the migration for a human instead of losing them.
"""

from __future__ import annotations

import frappe

RETIRED_PAGE = "tender-management-v2"

RETIRED_DOCTYPES: tuple[str, ...] = (
	"TM2 Addendum Acknowledgement",
	"TM2 Addendum Impact Record",
	"TM2 Addendum",
	"TM2 Bid Draft Metadata",
	"TM2 Bid Receipt",
	"TM2 Bid Submission Component",
	"TM2 Bid Submission",
	"TM2 Clarification Request",
	"TM2 Clarification Response",
	"TM2 Contract Handoff Reference",
	"TM2 Evaluation Handoff Record",
	"TM2 Late Submission Attempt",
	"TM2 Notification Record",
	"TM2 Opening Readiness Record",
	"TM2 Publication Readiness",
	"TM2 Publication Record",
	"TM2 Supplier Participation",
	"TM2 Tender Access Rule",
	"TM2 Tender Audit Event",
	"TM2 Tender Closing Record",
	"TM2 Tender Invitation",
	"TM2 Tender Timeline",
	"TM2 Tender",
	# Companion doctypes that only the retired module used.
	"Tender Publication Approval Decision",
	"Tender Publication Snapshot",
	"Security Role Permission",
	"Security Role",
	"Security Permission",
)

# Tables whose rows are keyed by the retired doctype's name.
_BY_PARENT = ("DocField", "DocPerm", "DocType Link", "DocType Action", "DocType State", "Custom DocPerm")


def execute() -> None:
	_refuse_if_rows_exist()
	for doctype in RETIRED_DOCTYPES:
		_drop_doctype(doctype)
	_drop_page(RETIRED_PAGE)
	frappe.clear_cache()


def _refuse_if_rows_exist() -> None:
	populated = []
	for doctype in RETIRED_DOCTYPES:
		if not frappe.db.table_exists(doctype):
			continue
		if frappe.db.sql(f"select 1 from `tab{doctype}` limit 1"):
			populated.append(doctype)
	if populated:
		frappe.throw(
			"Retired records still hold data and were not dropped: " + ", ".join(populated),
			title="RETIRED_TABLE_NOT_EMPTY",
		)


def _drop_doctype(doctype: str) -> None:
	for table in _BY_PARENT:
		frappe.db.delete(table, {"parent": doctype})
	frappe.db.delete("DocType Link", {"link_doctype": doctype})
	frappe.db.delete("Property Setter", {"doc_type": doctype})
	frappe.db.delete("Custom Field", {"dt": doctype})
	frappe.db.delete("DocType", {"name": doctype})
	frappe.db.sql_ddl(f"drop table if exists `tab{doctype}`")
	# Workspace entries pointing at the retired doctype, if any.
	frappe.db.delete("Workspace Link", {"link_to": doctype})
	frappe.db.delete("Workspace Shortcut", {"link_to": doctype})
	frappe.db.delete("Workspace Sidebar Item", {"link_to": doctype})


def _drop_page(page: str) -> None:
	frappe.db.delete("Has Role", {"parent": page, "parenttype": "Page"})
	frappe.db.delete("Page", {"name": page})
	frappe.db.delete("Workspace Link", {"link_to": page})
	frappe.db.delete("Workspace Shortcut", {"link_to": page})
	frappe.db.delete("Workspace Sidebar Item", {"link_to": page})
