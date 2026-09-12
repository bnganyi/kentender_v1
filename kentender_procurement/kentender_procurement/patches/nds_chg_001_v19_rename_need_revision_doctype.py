# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.9 — rename `Departmental Need Version` to `Departmental Need Revision`.

The Need's counter is a *revision* of one requirement (v1.10 §4.3), not a
"version" in the Planning/Requisitions sense, so the DocType and every field
that names the counter are renamed. This patch does the DocType half through
Frappe's native `frappe.rename_doc("DocType", ...)`, which cascades: the
`tabDocType` row, every Link field `options` referencing the old name across
the whole schema (including the Planning DocTypes that link to it), every
stored Link *value* pointing at it, and — via `DocType.after_rename` — the
physical table (`RENAME TABLE`). The field renames follow in
`nds_chg_001_v19_rename_need_revision_fields` (post_model_sync).

Runs in `pre_model_sync`, deliberately, on the same reasoning as
`kentender_budget.patches.bud_chg_001_v1_3_phase2_rename_budget_doctypes`:
the JSON on disk already declares the NEW name (folder, files and controller
class were git-mv'd in the same commit, so the old JSON is gone). Were this to
run post_model_sync, schema sync would first create a brand-new, empty
`Departmental Need Revision` from the new JSON and leave the live rows
orphaned under the old name. Running before model sync means `rename_doc`
finds the OLD DocType exactly as it still is in the database, renames it, and
only then does schema sync reconcile the (already-renamed) DocType against the
new JSON — an update, not a collision with a phantom duplicate.

`DocType.after_rename()` skips moving files/folders while
`frappe.flags.in_patch` is set, which is what's wanted: the files were already
moved by hand.

Record names keep their `-V{n:03d}` suffix (`services/lifecycle.py`): the
rename touches schema and metadata, never the stored identifiers.
"""

from __future__ import annotations

import frappe

OLD = "Departmental Need Version"
NEW = "Departmental Need Revision"


def execute() -> None:
	if not frappe.db.exists("DocType", OLD):
		# Fresh site: the app's JSON already ships under the new name, so
		# schema sync will create it directly — nothing to rename.
		return
	if frappe.db.exists("DocType", NEW):
		# Already renamed (patch re-run, or a prior manual rename) — idempotent
		# no-op rather than a duplicate-name throw.
		return
	frappe.rename_doc("DocType", OLD, NEW, force=True, show_alert=False)
	frappe.db.commit()
