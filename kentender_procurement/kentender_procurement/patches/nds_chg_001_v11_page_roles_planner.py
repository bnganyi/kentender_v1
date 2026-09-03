"""Admit the Procurement Planner to the one Departmental Needs Page.

`nds_chg_001_v11_page_roles` reconciled the Page roles in Phase 3, when the
module still had a Page per screen and each could carry its own list. §10
collapsed all eight NDS-UI routes onto `departmental-needs`, so that Page's
role list has to be the union of everyone §6 admits to any Needs surface.

It was not. The survivor kept the narrow landing list, which excluded the
Procurement Planner — so the Planner could not open the Page at all, and
therefore could not reach the intake window that NDS-AC-043 makes their
responsibility and §10 gives them a menu entry for. Found in Phase 9 by the
NDS-UI-08 browser spec, which logs in as the Planner: the Vue root never
mounted, because Frappe refused the Page before any of it ran.

Patches do not re-run, so the earlier one cannot be amended in place.

This widens who may *open* the Page. It grants no Departmental Needs authority:
§17 keeps that on the server, where `can_view` gives the Planner accepted
sources only and every command re-checks its own role.

Runs post-model-sync: it edits a Page record, not schema.
"""

import frappe

from kentender_procurement.setup.departmental_needs_page import generate


def execute():
	if not frappe.db.exists("Page", "departmental-needs"):
		return
	before = sorted({row.role for row in frappe.get_doc("Page", "departmental-needs").roles})
	generate()
	after = sorted({row.role for row in frappe.get_doc("Page", "departmental-needs").roles})
	if before != after:
		frappe.clear_cache()
		print(f"Departmental Needs page roles: {before} -> {after}")
