# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Retire the UOM read grant that ``nds_chg_001_v16_grant_uom_read_permission`` added.

That grant existed only because the need editor read the unit catalogue in the
browser with ``frappe.db.get_list("UOM")``, which enforces UOM's own DocPerm
table. UAT issue #24 showed the approach is fragile: any signed-in author whose
Frappe role lacked the grant hit "Insufficient Permission for UOM" and an empty
Unit list. The editor now reads units through the ``list_need_units`` contract,
which runs on the server, so no Departmental Needs role needs access to ERPNext's
``UOM`` doctype any more.

Only the exact rows the earlier patch created are removed: the three business
roles, permission level 0, with read as the only data right. A row someone has since
widened (create, write, ...) is left alone.
"""

from __future__ import annotations

import frappe

DOCTYPE = "UOM"
ROLES = ("Departmental Author", "Head of User Department", "Procurement Planner")
# Frappe fills `export` (and similar) with its own default on every Custom
# DocPerm it inserts, so only rights that change data count as a widened row.
_OTHER_RIGHTS = ("write", "create", "delete", "submit", "cancel", "amend", "if_owner")


def execute():
	if not frappe.db.exists("DocType", DOCTYPE):
		return
	removed = False
	for row in frappe.get_all(
		"Custom DocPerm",
		filters={"parent": DOCTYPE, "role": ["in", ROLES], "permlevel": 0, "read": 1},
		fields=["name", *_OTHER_RIGHTS],
	):
		if any(row.get(right) for right in _OTHER_RIGHTS):
			continue
		frappe.delete_doc("Custom DocPerm", row.name, force=True, ignore_permissions=True)
		removed = True
	if removed:
		frappe.clear_cache(doctype=DOCTYPE)
