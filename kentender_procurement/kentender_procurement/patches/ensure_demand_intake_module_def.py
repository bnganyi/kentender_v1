# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure ``Demand Intake`` exists in ``tabModule Def`` so Demand / Demand Item sync on migrate.

Sites that installed ``kentender_procurement`` before ``Demand Intake`` was added to
``modules.txt`` only received the first module row; DocTypes bound to *Demand Intake*
were never created, which breaks DIA landing until migrate creates the DocTypes.
"""

import frappe


def execute():
	if frappe.db.exists("Module Def", "Demand Intake"):
		return
	doc = frappe.new_doc("Module Def")
	doc.app_name = "kentender_procurement"
	doc.module_name = "Demand Intake"
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
