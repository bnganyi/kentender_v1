import frappe


def execute():
	"""Rename Workspace Sidebar and Desktop Icon from Kentender * to short tile labels."""
	pairs = [
		("Kentender Strategy", "Strategy"),
		("Kentender Procurement", "Procurement"),
		("Kentender Budget", "Budget"),
	]
	for old, new in pairs:
		if frappe.db.exists("Workspace Sidebar", old) and not frappe.db.exists("Workspace Sidebar", new):
			frappe.rename_doc("Workspace Sidebar", old, new, force=True)
		if frappe.db.exists("Desktop Icon", old) and not frappe.db.exists("Desktop Icon", new):
			frappe.rename_doc("Desktop Icon", old, new, force=True)
