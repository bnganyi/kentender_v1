# Copyright (c) 2026, KenTender and contributors
"""Drop legacy Demand Intake DocTypes removed in Demands MVP-1 preparatory teardown.

Deletes Demand / Demand Item / Demand Value Treatment rows and DocTypes, Desk
Pages, Workspace chrome, and Module Def for Demand Intake. See
``docs/mvp-1/03_demands/05_Demands_Teardown_Dependency_Inventory.md``.
"""

from __future__ import annotations

import frappe

LEGACY_DOCTYPES = [
	"Demand Value Treatment",
	"Demand Item",
	"Demand",
]

LEGACY_PAGES = [
	"demand-hub",
	"demand-workbench",
	"create-demand",
]

LEGACY_WORKSPACES = [
	"Demand Intake and Approval",
]

LEGACY_SIDEBARS = [
	"Demand Intake",
]


def _delete_all_rows(doctype: str) -> None:
	if not frappe.db.exists("DocType", doctype):
		return
	if not frappe.db.table_exists(doctype):
		return
	try:
		names = frappe.get_all(doctype, pluck="name")
	except Exception:
		return
	for name in names:
		try:
			frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
		except Exception:
			try:
				frappe.db.delete(doctype, {"name": name})
			except Exception:
				pass


def execute() -> None:
	# Demands MVP-1 rebuild owns Demand DocTypes under Module Def "Demands".
	if frappe.db.exists("Module Def", "Demands"):
		return

	# Children before parents.
	for name in LEGACY_DOCTYPES:
		_delete_all_rows(name)

	for name in LEGACY_DOCTYPES:
		if not frappe.db.exists("DocType", name):
			continue
		try:
			frappe.delete_doc("DocType", name, force=1, ignore_permissions=True)
		except Exception:
			frappe.db.delete("DocType", {"name": name})
			if frappe.db.table_exists(name):
				frappe.db.sql_ddl(f"DROP TABLE IF EXISTS `tab{name}`")

	for name in LEGACY_PAGES:
		if frappe.db.exists("Page", name):
			try:
				frappe.delete_doc("Page", name, force=1, ignore_permissions=True)
			except Exception:
				frappe.db.delete("Page", {"name": name})

	for name in LEGACY_WORKSPACES:
		if frappe.db.exists("Workspace", name):
			try:
				frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)
			except Exception:
				frappe.db.delete("Workspace", {"name": name})

	for name in LEGACY_SIDEBARS:
		if frappe.db.exists("Workspace Sidebar", name):
			try:
				frappe.delete_doc("Workspace Sidebar", name, force=1, ignore_permissions=True)
			except Exception:
				frappe.db.delete("Workspace Sidebar", {"name": name})

	if frappe.db.exists("Module Def", "Demand Intake"):
		try:
			frappe.delete_doc("Module Def", "Demand Intake", force=1, ignore_permissions=True)
		except Exception:
			frappe.db.delete("Module Def", {"name": "Demand Intake"})

	frappe.clear_cache()
