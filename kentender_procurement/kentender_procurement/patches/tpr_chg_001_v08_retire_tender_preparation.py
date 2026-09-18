# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 — retire the v0.6 `Tender Preparation` module in full.

Owner instruction (18 September 2026): every prior Tender Preparation /
Tender Publication work item is retired and **no data migration** is
performed — the nine module-owned doctypes are deleted and their tables
dropped, the Page and Module Def are removed, and the one doctype the kept
`tender_templates` package still needs (`Supported Tender Template`) is
relocated to the new `Tenders` module. The canonical world is reseeded
afterwards (`make seed-canonical THROUGH=requisitions`), which is what
clears the handoff consumption the dropped Tender left behind.

Runs pre_model_sync so the rows and tables are gone before sync looks for
the deleted JSON (same shape as `pln_chg_001_v112_drop_retired_planning_doctypes`).
"""

from __future__ import annotations

import frappe

# Children before parents; the root last.
RETIRED_DOCTYPES: tuple[str, ...] = (
	"Tender Readiness Finding",
	"Tender Evidence Requirement",
	"Tender Preparation Task",
	"Tender Preparation Decision",
	"Tender Publication Handoff",
	"Tender Preparation Event",
	"Tender Preparation Command Journal",
	"Tender Preparation Version",
	"Prepared Tender",
)
RETIRED_MODULE = "Tender Preparation"
RETIRED_PAGE = "tender-preparation"
NEW_MODULE = "Tenders"
RELOCATED_DOCTYPE = "Supported Tender Template"


def _ensure_module_def() -> None:
	# `frappe-new-module-cache-gotcha`: a module first seen in modules.txt on
	# a running site gets mis-created with app_name=frappe on the first
	# migrate; creating it here, before sync, avoids that.
	if frappe.db.exists("Module Def", NEW_MODULE):
		frappe.db.set_value("Module Def", NEW_MODULE, "app_name", "kentender_procurement", update_modified=False)
		return
	frappe.get_doc({"doctype": "Module Def", "module_name": NEW_MODULE, "app_name": "kentender_procurement", "custom": 0}).insert(
		ignore_permissions=True
	)


def execute() -> None:
	_ensure_module_def()
	if frappe.db.exists("DocType", RELOCATED_DOCTYPE):
		frappe.db.set_value("DocType", RELOCATED_DOCTYPE, "module", NEW_MODULE, update_modified=False)
	for doctype in RETIRED_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True, delete_permanently=True)
		frappe.db.sql_ddl(f"drop table if exists `tab{doctype}`")
	if frappe.db.exists("DocType", "Workspace Sidebar Item"):
		frappe.db.delete("Workspace Sidebar Item", {"link_type": "Page", "link_to": RETIRED_PAGE})
	# Direct row deletes: `Page.on_trash` schedules an after-commit folder
	# cleanup that imports the (already deleted) module package, and
	# `Module Def.on_trash` walks the module folder — both would fail here.
	if frappe.db.exists("Page", RETIRED_PAGE):
		frappe.db.delete("Has Role", {"parent": RETIRED_PAGE, "parenttype": "Page"})
		frappe.db.delete("Custom Role", {"page": RETIRED_PAGE})
		frappe.db.delete("Page", {"name": RETIRED_PAGE})
	if frappe.db.exists("Module Def", RETIRED_MODULE):
		frappe.db.delete("Module Def", {"name": RETIRED_MODULE})
	frappe.db.commit()
	frappe.clear_cache()
