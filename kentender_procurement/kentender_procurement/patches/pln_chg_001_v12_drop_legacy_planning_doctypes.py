# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 Phase 1 — drop the Demand-era Planning doctypes.

The v1.2 authority prohibits legacy compatibility and migrated records
(§1.1); the replacement model is a clean domain, so rows are dropped with
their tables. Runs pre_model_sync so the legacy tables are gone before the
new model syncs. Safe on fresh installs: every drop is existence-guarded.
"""

from __future__ import annotations

import frappe

LEGACY_DOCTYPES = (
	# dependents first, roots last
	"Plan Need Allocation",
	"Plan Validation Result",
	"Plan Decision",
	"Publication Event",
	"Planning Handoff Snapshot",
	"Procurement Plan Item Version",
	"Procurement Plan Item",
	"Procurement Plan Version",
	"Procurement Plan",
)


def execute() -> None:
	for doctype in LEGACY_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc(
				"DocType",
				doctype,
				force=True,
				ignore_missing=True,
				ignore_permissions=True,
				delete_permanently=True,
			)
		# delete_doc does not reliably drop the backing table; do it explicitly
		frappe.db.sql_ddl(f"drop table if exists `tab{doctype}`")
	frappe.db.commit()
