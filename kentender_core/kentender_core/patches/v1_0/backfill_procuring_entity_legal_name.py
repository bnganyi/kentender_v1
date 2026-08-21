# Copyright (c) 2026, KenTender and contributors

import frappe


def execute():
	if not frappe.db.has_column("Procuring Entity", "legal_name"):
		return
	for name, entity_name, legal_name, entity_code in frappe.db.sql(
		"select name, entity_name, legal_name, entity_code from `tabProcuring Entity`"
	):
		updates = {}
		if not (legal_name or "").strip() and (entity_name or "").strip():
			updates["legal_name"] = entity_name
		if frappe.db.has_column("Procuring Entity", "entity_reference"):
			eref = frappe.db.get_value("Procuring Entity", name, "entity_reference")
			if not (eref or "").strip():
				updates["entity_reference"] = f"PE-REF-{entity_code or name}"
		if frappe.db.has_column("Procuring Entity", "status"):
			st = frappe.db.get_value("Procuring Entity", name, "status")
			if not (st or "").strip():
				updates["status"] = "Active"
		if updates:
			frappe.db.set_value("Procuring Entity", name, updates, update_modified=False)
