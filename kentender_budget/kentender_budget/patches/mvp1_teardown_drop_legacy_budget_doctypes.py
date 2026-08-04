# Copyright (c) 2026, KenTender and contributors
"""Drop legacy Budget DocTypes removed in MVP-1 preparatory teardown.

Clears consumer Links, deletes rows in FK-safe order, force-deletes DocTypes
and Desk Pages, and keeps a minimal public Workspace named Budget Management
so Procurement rail links (Budget & Funding → Budget Management) do not break.
"""

from __future__ import annotations

import frappe

# MVP-1 reintroduced Budget + Budget Line — do not drop those here.
LEGACY_DOCTYPES = [
	"Budget Reservation",
	"Budget Allocation",
	"Funding Source",
	"Budget Navigation",
]

LEGACY_PAGES = ["budget-hub", "budget-workbench"]

CONSUMER_LINK_CLEARS = (
	("Demand", ("budget_line", "budget", "funding_source", "reservation_reference")),
	("Procurement Package", ("budget_line_id",)),
	("Procurement Package Line", ("budget_line_id",)),
	("Procurement Journey", ("budget_line_ref",)),
)


def _clear_consumer_links() -> None:
	for doctype, fields in CONSUMER_LINK_CLEARS:
		if not frappe.db.exists("DocType", doctype):
			continue
		meta_fields = {df.fieldname for df in frappe.get_meta(doctype).fields}
		for field in fields:
			if field not in meta_fields:
				continue
			try:
				frappe.db.sql(
					f"UPDATE `tab{doctype}` SET `{field}` = NULL WHERE `{field}` IS NOT NULL"
				)
			except Exception:
				frappe.db.sql(
					f"UPDATE `tab{doctype}` SET `{field}` = '' WHERE IFNULL(`{field}`, '') != ''"
				)


def _delete_all_rows(doctype: str) -> None:
	if not frappe.db.exists("DocType", doctype):
		return
	# DocType metadata can exist without a physical table (orphan / never synced).
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


def _ensure_placeholder_workspace() -> None:
	"""Minimal public Workspace so Procurement rail Budget & Funding links validate."""
	title = "Budget Management"
	if frappe.db.exists("Workspace", title):
		frappe.db.set_value(
			"Workspace",
			title,
			{
				"public": 1,
				"is_hidden": 0,
				"module": "Kentender Budget",
				"label": "Budget & Funding",
				"title": title,
			},
			update_modified=False,
		)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Workspace",
			"label": "Budget & Funding",
			"title": title,
			"module": "Kentender Budget",
			"app": "kentender_budget",
			"type": "Workspace",
			"content": "[]",
			"icon": "money-bill-wave",
			"public": 0,
			"is_hidden": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.set_value(
		"Workspace",
		title,
		{"public": 1, "is_hidden": 0, "label": "Budget & Funding"},
		update_modified=False,
	)


def execute() -> None:
	_clear_consumer_links()

	# Safe delete order (children before parents).
	for name in LEGACY_DOCTYPES:
		_delete_all_rows(name)

	for name in LEGACY_DOCTYPES:
		if not frappe.db.exists("DocType", name):
			continue
		try:
			frappe.delete_doc("DocType", name, force=1, ignore_permissions=True)
		except Exception:
			# Last resort: remove DocType row if linked rows block force-delete.
			frappe.db.delete("DocType", {"name": name})
			if frappe.db.table_exists(name):
				frappe.db.sql_ddl(f"DROP TABLE IF EXISTS `tab{name}`")

	for name in LEGACY_PAGES:
		if frappe.db.exists("Page", name):
			try:
				frappe.delete_doc("Page", name, force=1, ignore_permissions=True)
			except Exception:
				frappe.db.delete("Page", {"name": name})

	# Drop fat chrome that would reintroduce dead routes.
	for doctype, name in (
		("Workspace Sidebar", "Budget"),
		("Desktop Icon", "Budget"),
	):
		if frappe.db.exists(doctype, name):
			try:
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			except Exception:
				frappe.db.delete(doctype, {"name": name})

	# Drop leftover physical tables if DocType metadata is already gone.
	for name in LEGACY_DOCTYPES:
		if frappe.db.table_exists(name) and not frappe.db.exists("DocType", name):
			frappe.db.sql_ddl(f"DROP TABLE IF EXISTS `tab{name}`")

	_ensure_placeholder_workspace()
	frappe.db.commit()
