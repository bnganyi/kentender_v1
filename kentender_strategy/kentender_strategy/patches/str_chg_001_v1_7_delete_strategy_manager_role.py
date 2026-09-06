# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 — hard-delete the "Strategy Manager" Role.

v1.6 deleted Strategy Officer / Strategy Reviewer / Strategy Approval
Authority but deliberately spared this one, because kentender_procurement's
Procurement Lifecycle role matrix and DocPerm rows on Procurement Journey /
Procurement Handoff Card / Procuring Department / Procuring Entity still
granted read through it.

Those grants are now gone (removed alongside this patch), so the Role has no
remaining referent. It has carried no Strategy capability since the rebuild:
STR-CHG-001 v1.5 §14 defines exactly two Strategy roles, Strategy Author and
Strategy Approver, and "Strategy Manager" appears nowhere in that spec. What
survived was a name promising Strategy authority attached to nothing but a
handful of cross-app read grants — a holder was shown "STRATEGY MANAGER" in
the Desk header and then refused with AUTH_ROLE_REQUIRED on every Strategy
action.

Holders do not silently lose real access: read on those four doctypes still
comes from the other roles in the same matrix (Planning Authority,
Procurement Planner, Procurement Officer, Auditor, System Manager, …). Anyone
who held ONLY this role was, by construction, able to do nothing in Strategy
anyway; assign Strategy Author (plus the Procuring Entity User Permission that
role's pe_scoped classification requires) to grant real authoring rights.
"""

from __future__ import annotations

import frappe

ROLE = "Strategy Manager"


def execute() -> None:
	# Strip every grant first so nothing keeps a dangling child row. NOT
	# filtered by parenttype: `Has Role` also backs a Page's own `roles` table
	# (kt-procurement-home held one), and a User-only delete leaves those
	# pointing at a Role that no longer exists.
	frappe.db.delete("Has Role", {"role": ROLE})
	# DocPerm/Custom DocPerm rows are removed with their fixtures, but a site
	# that customised a doctype by hand can still hold one.
	for doctype in ("DocPerm", "Custom DocPerm"):
		if frappe.db.exists("DocType", doctype):
			frappe.db.delete(doctype, {"role": ROLE})
	if frappe.db.exists("Role", ROLE):
		frappe.delete_doc("Role", ROLE, force=True, ignore_permissions=True)
	frappe.db.commit()
