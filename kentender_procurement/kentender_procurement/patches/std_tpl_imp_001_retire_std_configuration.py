# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 retirement (owner decision OD4, 25 Sep 2026).

Drops what the installed-release runtime (**STD Templates**) replaced:

- the editable **STD Configuration** module — its 27 ``STD Cfg *`` DocTypes,
  6 ``std-cfg-*`` Pages and Module Def (the source is archived under
  ``archive/std-configuration-retired-2026-09/``);
- the ``Supported Tender Template`` registry DocType (the old
  ``tender_templates`` package that wrote it is archived with it);
- the stale **Governance & Configuration** Workspace (and its sidebar), whose
  links named DocTypes and a Page that no longer exist;
- the nine STD roles no user holds and no live surface grants.

Every deletion is exists-guarded, so the patch is idempotent and safe on a
site that never had these rows. Follows ``retire_std_engine_v2_cleanup``.
"""

from __future__ import annotations

import frappe

RETIRED_MODULE = "STD Configuration"

# Children before parents; the multi-pass loop absorbs residual ordering.
RETIRED_DOCTYPES: tuple[str, ...] = (
	"STD Cfg Assistance Proposal Item",
	"STD Cfg Form Schema Field",
	"STD Cfg Reuse Register Item",
	"STD Cfg Tender Manifest Item",
	"STD Cfg Assistance Batch",
	"STD Cfg Command Journal",
	"STD Cfg Content Block",
	"STD Cfg Contract Schema",
	"STD Cfg Decision",
	"STD Cfg Draft",
	"STD Cfg Evaluation Schema",
	"STD Cfg Form Schema",
	"STD Cfg Inventory Schema",
	"STD Cfg Output Mapping",
	"STD Cfg Parameter Definition",
	"STD Cfg Price Schema",
	"STD Cfg Requirement Schema",
	"STD Cfg Reuse Run",
	"STD Cfg Review Task",
	"STD Cfg Runtime Manifest",
	"STD Cfg Schedule Schema",
	"STD Cfg Section",
	"STD Cfg Source Document",
	"STD Cfg Tender Manifest",
	"STD Cfg Validation Finding",
	"STD Cfg Package",
	"STD Cfg Version",
	"Supported Tender Template",
)

RETIRED_PAGES: tuple[str, ...] = (
	"std-cfg-area",
	"std-cfg-comparison",
	"std-cfg-documents",
	"std-cfg-package-home",
	"std-cfg-readiness",
	"std-cfg-review",
)

RETIRED_WORKSPACE = "Governance & Configuration"

RETIRED_ROLES: tuple[str, ...] = (
	"STD Template Administrator",
	"STD Template Importer",
	"STD Template Reviewer",
	"STD Template Approver",
	"STD Template Activator",
	"STD Template Auditor",
	"STD Technical Inspector",
	"STD Configurator",
	"STD Reviewer",
)


def _delete_permission_rows() -> None:
	ph = ", ".join(["%s"] * len(RETIRED_DOCTYPES))
	frappe.db.sql(f"DELETE FROM `tabCustom DocPerm` WHERE parent IN ({ph})", list(RETIRED_DOCTYPES))
	for dt in RETIRED_DOCTYPES:
		frappe.db.delete("Property Setter", {"doc_type": dt})
		frappe.db.delete("Custom Field", {"dt": dt})


def _delete_doctypes_multi_pass() -> None:
	remaining = list(RETIRED_DOCTYPES)
	for _ in range(6):
		if not remaining:
			break
		next_remaining: list[str] = []
		for dt in remaining:
			if not frappe.db.exists("DocType", dt):
				continue
			try:
				frappe.delete_doc("DocType", dt, force=True, ignore_permissions=True)
			except Exception:
				next_remaining.append(dt)
		remaining = next_remaining
	for dt in remaining:
		frappe.log_error(title=f"KenTender std_tpl_imp_001_retire_std_configuration: could not delete DocType {dt}", message=frappe.get_traceback())


def _drop_tables() -> None:
	"""Deleting a standard DocType row leaves its table; drop each one whose
	DocType is gone (the ``drop table if exists`` precedent of
	``tpr_chg_001_v08_retire_tender_preparation``)."""
	for dt in RETIRED_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			frappe.db.sql_ddl(f"drop table if exists `tab{dt}`")


def _delete_pages_and_workspace() -> None:
	for page in RETIRED_PAGES:
		if frappe.db.exists("Page", page):
			frappe.delete_doc("Page", page, force=True, ignore_permissions=True)
	for doctype in ("Workspace Sidebar", "Workspace"):
		if frappe.db.table_exists(doctype) and frappe.db.exists(doctype, RETIRED_WORKSPACE):
			frappe.delete_doc(doctype, RETIRED_WORKSPACE, force=True, ignore_permissions=True)


def _delete_roles() -> None:
	for role in RETIRED_ROLES:
		frappe.db.delete("Has Role", {"role": role})
		frappe.db.delete("DocPerm", {"role": role})
		frappe.db.delete("Custom DocPerm", {"role": role})
		if frappe.db.exists("Role", role):
			frappe.delete_doc("Role", role, force=True, ignore_permissions=True)


def _delete_module_def() -> None:
	if frappe.db.exists("Module Def", RETIRED_MODULE):
		frappe.delete_doc("Module Def", RETIRED_MODULE, force=True, ignore_permissions=True)


def execute() -> None:
	_delete_permission_rows()
	_delete_doctypes_multi_pass()
	_drop_tables()
	_delete_pages_and_workspace()
	_delete_roles()
	_delete_module_def()
	frappe.clear_cache()
	frappe.db.commit()
