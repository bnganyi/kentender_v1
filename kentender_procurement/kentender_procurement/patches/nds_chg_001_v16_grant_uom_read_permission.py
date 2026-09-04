# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.6 D6 — the three Departmental Needs business roles need read
access to ERPNext's native ``UOM`` doctype.

D6 retargets ``Departmental Need Version.unit`` from KenTender's own retired
``Unit Of Measure`` doctype to ERPNext's native ``UOM`` (NDS-504), and the need
editor (``DepartmentalNeeds.vue::loadUnits``) reads the catalogue directly via
``frappe.db.get_list("UOM", ...)`` — a client-side call that enforces UOM's own
DocPerm table, which carries only ERPNext's own inventory/sales roles (Item
Manager, Stock Manager, Stock User, Sales User, Sales Manager; confirmed by
reading ``erpnext/setup/doctype/uom/uom.json``). None of Departmental Needs'
own business roles held read access, so a real Departmental Author's "Create
need" flow always failed live with Frappe's own "Insufficient Permission for
UOM" dialog — and because that call sits inside the screen's one shared
``load()`` promise, the failure also left the editor's ``data-loading`` flag
stuck ``true`` forever (`DepartmentalNeeds.vue`'s `NeedEditorScreen` renders
regardless of `loading`, so the form looked fine underneath the dialog).

Confirmed live 2026-09-04 by driving the real create-need flow as a disposable
Departmental Author `User Responsibility Assignment` holder (Administrator's
own read-all bypasses every DocPerm, which is why Phase 5's own browser
verification — done as Administrator — never caught this). Not previously
caught by any Python test either: `require_create()`/`lifecycle.create_need()`
never touch `UOM` permissions themselves, since the server-side unit-eligibility
check (`UOM.enabled`) reads via `frappe.db.get_value`, which bypasses DocType
permissions entirely — only the client's own `frappe.db.get_list` call is
permission-checked.

UOM is non-sensitive reference/master data (unit labels such as "Each",
"Kilogram", "Litre"), so a plain read grant is the correct, minimal fix — a
``Custom DocPerm`` row per role, Frappe's own supported mechanism for
extending permissions on a doctype this app does not own (never edit
erpnext's own doctype JSON directly, per AGENTS.md §2/§4.1). Idempotent: skips
any role/doctype pair that already carries a read grant.
"""

from __future__ import annotations

import frappe

DOCTYPE = "UOM"
ROLES = ("Departmental Author", "Head of User Department", "Procurement Planner")


def execute():
	if not frappe.db.exists("DocType", DOCTYPE):
		return
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			continue
		if frappe.db.exists("Custom DocPerm", {"parent": DOCTYPE, "role": role, "read": 1}):
			continue
		frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": DOCTYPE,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": role,
				"permlevel": 0,
				"read": 1,
			}
		).insert(ignore_permissions=True)
	frappe.clear_cache(doctype=DOCTYPE)
