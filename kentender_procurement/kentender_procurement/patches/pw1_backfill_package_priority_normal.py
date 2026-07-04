# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW1: Procurement Package.package_priority options changed from
High/Medium/Low to Normal/High/Emergency (Package Creation Wizard spec).
Remap legacy Medium/Low rows to Normal; High stays High.
"""

from __future__ import annotations

import frappe


def execute():
	if not frappe.db.table_exists("Procurement Package"):
		return
	frappe.db.sql(
		"UPDATE `tabProcurement Package` SET `package_priority` = %s "
		"WHERE `package_priority` IN (%s, %s)",
		("Normal", "Medium", "Low"),
	)
