# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Drop the retired Tender Configurations site records (owner decision, 7 Oct 2026).

The legacy Tender Configurations module (the IT wizard, its publication pipeline and the
BWMF bidder-workspace-manifest framework) is permanently retired. Its code, doctype JSON,
Desk pages and assets are deleted from the repository, so a site that was migrated before
the deletion still carries the metadata and (empty) tables. This patch is the only place
the retired names remain.

Same shape as ``drop_retired_tm2_surface``:

* Nothing is deleted through ``frappe.delete_doc``. In developer mode that removes files
  under the app and fires document events; the files are already gone and the doctypes are
  no longer importable. Raw, existence-guarded deletes only.
* Idempotent: every statement is guarded, so a second run (or a run on a site where the
  records are already gone) changes nothing and raises nothing.
* Cheap: it never scans the big log tables (``Deleted Document``, ``Comment``, ``Version``;
  about a million rows on a long-lived site). Leftover deletion-log rows of the retired
  doctypes are inert.
* Data-safe: it refuses (shared ``require_empty_or_authorised`` guard, AUD-XC-127) to drop
  a table that holds rows, and unconditionally refuses to drop the content-addressed File
  folder when it holds files, so a site that unexpectedly carries records stops the
  migration for a human instead of losing them.
"""

from __future__ import annotations

import frappe

from kentender_core.utils.patch_guards import require_empty_or_authorised

RETIRED_MODULE = "Tender Configurations"

RETIRED_DOCTYPES: tuple[str, ...] = (
	"BWMF Addendum Impact Plan",
	"BWMF Approval Decision",
	"BWMF Artifact Resource Binding",
	"BWMF Audit Event",
	"BWMF Authority Reference",
	"BWMF Compile Artifact",
	"BWMF Compile Input Binding",
	"BWMF Compile Request",
	"BWMF Compile Run",
	"BWMF Compile Stage Trace",
	"BWMF Compiler Diagnostic",
	"BWMF Confirmation",
	"BWMF Content Object",
	"BWMF Dependency Snapshot",
	"BWMF Evidence Item",
	"BWMF Evidence Link",
	"BWMF Evidence Version",
	"BWMF Idempotency Record",
	"BWMF Invalidation Event",
	"BWMF Lifecycle Event",
	"BWMF Manifest Approval",
	"BWMF Manifest Publication",
	"BWMF Manifest Resource",
	"BWMF Manifest Resource Binding",
	"BWMF Manifest Version",
	"BWMF Materialization Report",
	"BWMF Publication Request",
	"BWMF Response Version",
	"BWMF Review Package",
	"BWMF Submission",
	"BWMF Submission Receipt",
	"BWMF Tender Publication State",
	"BWMF Validation Finding",
	"BWMF Validation Report",
	"BWMF Validation Snapshot",
	"BWMF Workspace",
	"BWMF Workspace Manifest Binding",
	"Confirmed Tender Document Package",
	"IT Tender Publication Record",
	"Tender Configuration",
)

RETIRED_PAGES: tuple[str, ...] = (
	"it-std-wizard-retired",
	"it-tender-configuration-dashboard",
	"it-tender-configuration-evaluation-setup",
	"it-tender-configuration-forms-and-evidence",
	"it-tender-configuration-implementation-schedule",
	"it-tender-configuration-it-requirements",
	"it-tender-configuration-overview",
	"it-tender-configuration-price-schedule",
	"it-tender-configuration-publication-readiness",
	"it-tender-configuration-render-preview",
	"it-tender-configuration-review-and-approval",
	"it-tender-configuration-scc",
	"it-tender-configuration-system-inventory",
	"it-tender-configuration-tds",
	"it-tender-configuration-tender-profile",
	"it-tender-configuration-validation-report",
	"it-tender-package-review",
	"publication-setup",
	"publications",
)

RETIRED_ROLES: tuple[str, ...] = (
	"BWMF Auditor",
	"BWMF Procurement Reviewer",
	"BWMF Publication Service",
	"BWMF Tender Approver",
	"BWMF Tender Configurator",
)

CAS_FOLDER = "Home/BWMF-CAS"

# Tables whose rows are keyed by the retired doctype's name.
_BY_PARENT = ("DocField", "DocPerm", "DocType Link", "DocType Action", "DocType State", "Custom DocPerm")


def execute() -> None:
	_refuse_if_rows_exist()
	for doctype in RETIRED_DOCTYPES:
		_drop_doctype(doctype)
	for page in RETIRED_PAGES:
		_drop_page(page)
	for role in RETIRED_ROLES:
		_drop_role_if_unused(role)
	_drop_cas_folder()
	if frappe.db.exists("Module Def", RETIRED_MODULE):
		frappe.db.delete("Module Def", {"name": RETIRED_MODULE})
	frappe.clear_cache()


def _refuse_if_rows_exist() -> None:
	require_empty_or_authorised("drop_retired_tender_configurations", RETIRED_DOCTYPES)
	if frappe.db.exists("File", {"folder": CAS_FOLDER}):
		frappe.throw(
			"The retired content-addressed store still holds files and was not dropped.",
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
	frappe.db.delete("Workspace Link", {"link_to": doctype})
	frappe.db.delete("Workspace Shortcut", {"link_to": doctype})
	frappe.db.delete("Workspace Sidebar Item", {"link_to": doctype})


def _drop_page(page: str) -> None:
	frappe.db.delete("Has Role", {"parent": page, "parenttype": "Page"})
	frappe.db.delete("Page", {"name": page})
	frappe.db.delete("Workspace Link", {"link_to": page})
	frappe.db.delete("Workspace Shortcut", {"link_to": page})
	frappe.db.delete("Workspace Sidebar Item", {"link_to": page})


def _drop_role_if_unused(role: str) -> None:
	if not frappe.db.exists("Role", role):
		return
	if frappe.db.exists("Has Role", {"role": role}):
		return  # somebody holds it: leave it for a human, do not strip access
	frappe.db.delete("Role", {"name": role})


def _drop_cas_folder() -> None:
	frappe.db.delete("File", {"name": CAS_FOLDER, "is_folder": 1})
