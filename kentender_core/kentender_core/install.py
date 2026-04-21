# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe


def after_migrate():
	_ensure_user_kt_scope_fields()
	_hide_auto_workspace_desktop_icon_duplicates()


def _ensure_user_kt_scope_fields():
	"""Custom fields on User for entity-scoped Strategy permissions (spec §3)."""
	fields = [
		{
			"fieldname": "kt_procuring_entity",
			"label": "Procuring Entity (KenTender)",
			"fieldtype": "Link",
			"options": "Procuring Entity",
			"insert_after": "username",
		},
		{
			"fieldname": "kt_primary_department",
			"label": "Primary Department (KenTender)",
			"fieldtype": "Link",
			"options": "Procuring Department",
			"insert_after": "kt_procuring_entity",
		},
	]
	for f in fields:
		if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": f["fieldname"]}):
			continue
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "User",
				"module": "Kentender Core",
				**f,
			}
		).insert()
	frappe.clear_cache(doctype="User")


def _hide_auto_workspace_desktop_icon_duplicates():
	"""Frappe creates Desktop Icons from public Workspaces (label = workspace name).

	KenTender also ships custom Desktop Icons with short labels (Strategy, Budget) that
	link to Workspace Sidebars. Without this, users see two tiles per domain
	(e.g. Strategy Management + Strategy). Hide the auto-generated *Management* tiles."""
	labels = ("Strategy Management", "Budget Management")
	for label in labels:
		name = frappe.db.get_value("Desktop Icon", {"label": label, "icon_type": "Link"}, "name")
		if not name:
			continue
		frappe.db.set_value("Desktop Icon", name, "hidden", 1)
	frappe.db.commit()
	frappe.clear_cache()
