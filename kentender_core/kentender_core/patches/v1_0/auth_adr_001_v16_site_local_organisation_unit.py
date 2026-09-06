"""AUTH-ADR-001 v1.6 §4.2 — the Organisation Unit becomes site-local.

Three normalisations, all idempotent:

1. `parent_org_unit` → `parent_organisation_unit` (the v1.6 parent-field
   name), carrying the stored values across before the tree is rebuilt.
2. Rebuild the nested-set ranges against the renamed parent field.
3. Normalise any pre-v1.6 stored User Responsibility Assignment status —
   `Draft` was never authorising and becomes `Enabled` (the stored vocabulary
   is now Enabled/Revoked only), `Expired` becomes `Enabled` because expiry is
   derived from `effective_to` at read time (§4.6).

The deprecated `procuring_entity`/`unit_type` columns are deliberately left in
place: pre-cutover module readers still select them (tracker D2). They are
dropped in the removal phase.
"""

from __future__ import annotations

import frappe
from frappe.model.utils.rename_field import rename_field
from frappe.utils.nestedset import rebuild_tree


def execute():
	frappe.reload_doc("kentender_core", "doctype", "organisation_unit")
	frappe.reload_doc("kentender_core", "doctype", "user_responsibility_assignment")

	if frappe.db.has_column("Organisation Unit", "parent_org_unit"):
		rename_field("Organisation Unit", "parent_org_unit", "parent_organisation_unit")

	if frappe.db.has_column("Organisation Unit", "lft"):
		rebuild_tree("Organisation Unit")

	if frappe.db.has_column("User Responsibility Assignment", "status"):
		frappe.db.sql(
			"""update `tabUser Responsibility Assignment`
			set status = 'Enabled' where status in ('Draft', 'Expired')"""
		)
