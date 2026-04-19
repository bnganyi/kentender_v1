# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe


def after_migrate():
	_ensure_user_kt_scope_fields()


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
