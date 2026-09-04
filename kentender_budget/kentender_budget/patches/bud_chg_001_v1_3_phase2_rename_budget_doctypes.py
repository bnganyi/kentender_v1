# Copyright (c) 2026, KenTender and contributors
"""BUD-CHG-001 v1.3 Phase 2 — rename the Budget DocType family.

`Budget`/`Budget Version`/`Budget Line`/`Budget Line Version` collide with
ERPNext's own `Budget` DocType (v1.3 §1.1), so this patch renames them to
`Procurement Budget`/`Procurement Budget Version`/`Procurement Budget Line`/
`Procurement Budget Line Version` using Frappe's native `frappe.rename_doc`
mechanism for DocType renames, which cascades: the `tabDocType` row itself,
every Link/Table field `options` referencing the old name across the whole
schema, every stored Link field *value* pointing at the renamed doctype, and
(via `DocType.after_rename`) the physical table itself (`RENAME TABLE`).

Runs in `pre_model_sync`, deliberately: this app's own JSON files under
`doctype/procurement_budget*` already declare the NEW names (the app-side
rename — folders, files, controller classes, and every quoted doctype-name
string in Python/JSON — landed in the same commit as this patch, git-mv'd
so the old JSON is gone from disk). If this patch ran in `post_model_sync`,
schema sync would already have tried to reconcile the DB against JSON files
it can no longer find under the old names, and would separately try to
*create* a brand-new, empty `Procurement Budget` DocType from the new JSON
before this patch ever ran — leaving the live data orphaned under the old
name instead of renamed. Running before model sync means `frappe.rename_doc`
finds the OLD DocType exactly as it still is in the database (metadata +
physical table, untouched), renames it there, and only then does schema sync
reconcile the (already-renamed) DocType against the new JSON — an update to
an existing DocType, not a collision with a phantom duplicate.

Order is arbitrary — `frappe.rename_doc("DocType", ...)` renames the Link
`options` cascade globally regardless of dependency direction — but Budget
before Budget Version before Budget Line before Budget Line Version mirrors
the domain hierarchy for readability.

`DocType.after_rename()` skips re-renaming files/folders while
`frappe.flags.in_patch` is set (true for every patch execution), which is
exactly what's wanted here: the files were already moved by hand, so the
framework's own rename must not try to move them a second time.
"""

from __future__ import annotations

import frappe

RENAMES: tuple[tuple[str, str], ...] = (
	("Budget", "Procurement Budget"),
	("Budget Version", "Procurement Budget Version"),
	("Budget Line", "Procurement Budget Line"),
	("Budget Line Version", "Procurement Budget Line Version"),
)


def execute() -> None:
	for old, new in RENAMES:
		if not frappe.db.exists("DocType", old):
			# Fresh site: the app's own JSON already ships under the new
			# name, so schema sync will create it directly — nothing to
			# rename. Not an error; a rename patch is only meaningful on a
			# site that already has data under the old name.
			continue
		if frappe.db.exists("DocType", new):
			# Already renamed (patch re-run, or a prior manual rename) —
			# idempotent no-op rather than a duplicate-name throw.
			continue
		frappe.rename_doc("DocType", old, new, force=True, show_alert=False)
	frappe.db.commit()
