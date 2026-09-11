# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.9 — rename every field that names the Need's counter.

Companion to `nds_chg_001_v19_rename_need_revision_doctype` (pre_model_sync).
By the time this runs, schema sync has already added the NEW columns from the
checked-in JSON (Frappe never drops the old ones), so each rename is a
`frappe.model.utils.rename_field.rename_field` — copy the old column into the
new one, then retarget saved reports, user settings and property setters —
guarded by `frappe.db.has_column(doctype, old)` so a fresh site, or a re-run,
is a no-op per field. `rename_field` reads the *new* field off the DocType
meta, hence the `reload_doctype` first (the precedent is
`kentender_core.patches.v1_0.auth_adr_001_v16_site_local_organisation_unit`).

The two Procurement Planning DocTypes are included here even though their
JSON is Planning's: a cross-module column rename must land in one migration,
and the Need's counter is Departmental Needs' concept to rename.

Left unchanged, on purpose: `Departmental Need.record_version` (optimistic
lock, not the counter) and `Need Withdrawal Request.planning_dependency_version`
(the Planning-dependency fingerprint). No `pln_uniq_*` composite index
(`pln_chg_001_v12_planning_unique_indexes`) keys on a renamed column, so no
index rebuild is required.
"""

from __future__ import annotations

import frappe
from frappe.model.utils.rename_field import rename_field

RENAMES: tuple[tuple[str, str, str], ...] = (
	("Departmental Need Revision", "need_version_id", "need_revision_id"),
	("Departmental Need Revision", "version_number", "revision_number"),
	("Departmental Need Revision", "based_on_version", "based_on_revision"),
	("Departmental Need Revision", "version_status", "revision_status"),
	("Departmental Need", "current_version", "current_revision"),
	("Departmental Need", "current_accepted_version", "current_accepted_revision"),
	("Departmental Need Event", "need_version", "need_revision"),
	("Departmental Need Event", "superseded_version", "superseded_revision"),
	("Departmental Need Decision", "need_version", "need_revision"),
	("Departmental Need Review Task", "need_version", "need_revision"),
	("Need Planning Usage Projection", "accepted_version", "accepted_revision"),
	("Need Withdrawal Request", "accepted_version", "accepted_revision"),
	# Procurement Planning's links to the renamed counter (PLN JSON renamed in
	# the same change).
	("Departmental Plan Entry", "need_version", "need_revision"),
	("Plan Source Allocation", "need_version", "need_revision"),
)


def execute() -> None:
	for doctype in dict.fromkeys(doctype for doctype, _old, _new in RENAMES):
		if frappe.db.exists("DocType", doctype):
			frappe.reload_doctype(doctype)

	for doctype, old, new in RENAMES:
		if not frappe.db.exists("DocType", doctype):
			continue
		if not frappe.db.has_column(doctype, old):
			# Fresh site, or already renamed on a re-run.
			continue
		rename_field(doctype, old, new)
	frappe.db.commit()
