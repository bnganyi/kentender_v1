# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 §6 / STR-AC-031 — hard-delete the "Strategy Viewer" Role.

v1.7 keeps exactly two Strategy workflow responsibilities (Strategy Author,
Strategy Approver). Read access "is not a third Strategy workflow role": it
comes from the actor's assignments — the two governance roles themselves
and the registered Auditor business role (§6). "Strategy Viewer" was a bare
Frappe Role outside the AUTH-ADR-001 registry that could only ever be
granted by hand, and STR-AC-031 names it explicitly as a retired role no
metadata, permission or page may reference.

Same shape as the v1.7 "Strategy Manager" patch: strip every grant and
DocPerm first so no child row dangles, then delete the Role.
"""

from __future__ import annotations

import frappe

ROLE = "Strategy Viewer"


def execute() -> None:
	frappe.db.delete("Has Role", {"role": ROLE})
	for doctype in ("DocPerm", "Custom DocPerm"):
		if frappe.db.exists("DocType", doctype):
			frappe.db.delete(doctype, {"role": ROLE})
	if frappe.db.exists("Role", ROLE):
		frappe.delete_doc("Role", ROLE, force=True, ignore_permissions=True)
	frappe.db.commit()
