# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 Phase 1: retire the legacy bid-submission slice.

Drops what the new Supplier Portal and Electronic Bid Submission module
replaces (plan BDS-CHG-001 v0.8 Phase 1; `reconciliation/legacy_inventory.md`;
spec BDS01-IMP-090, BDS07-IMP-010):

- the three legacy bid DocTypes of the old tender-configuration module and every row in
  them. The Project Owner decided on 21 Sep 2026 that the old bid records
  are deleted outright, with no migration.
- the three legacy bidder/bid Desk Pages.

Every deletion is
exists-guarded, so the patch is idempotent and safe on a site that never had
these rows. Follows `std_tpl_imp_001_retire_std_configuration`.
"""

from __future__ import annotations

import frappe

from kentender_core.utils.patch_guards import require_empty_or_authorised

# Child before parent; the multi-pass loop absorbs residual ordering.
RETIRED_DOCTYPES: tuple[str, ...] = (
	"Electronic Bid Audit Event",
	"Electronic Bid Submission",
	"IT Bid Opening Record",
)

RETIRED_PAGES: tuple[str, ...] = (
	"bid-submissions",
	"it-electronic-bidder-workspace",
	"published-tender-overview",
)


def _delete_rows() -> None:
	for dt in RETIRED_DOCTYPES:
		if frappe.db.table_exists(dt):
			frappe.db.sql(f"DELETE FROM `tab{dt}`")


def _delete_permission_rows() -> None:
	ph = ", ".join(["%s"] * len(RETIRED_DOCTYPES))
	frappe.db.sql(f"DELETE FROM `tabCustom DocPerm` WHERE parent IN ({ph})", list(RETIRED_DOCTYPES))
	for dt in RETIRED_DOCTYPES:
		frappe.db.delete("Property Setter", {"doc_type": dt})
		frappe.db.delete("Custom Field", {"dt": dt})


def _delete_doctypes_multi_pass() -> None:
	remaining = list(RETIRED_DOCTYPES)
	for _ in range(4):
		if not remaining:
			break
		next_remaining: list[str] = []
		for dt in remaining:
			if not frappe.db.exists("DocType", dt):
				continue
			try:
				frappe.delete_doc("DocType", dt, force=True, ignore_permissions=True)
			except Exception:
				next_remaining.append(dt)
		remaining = next_remaining
	for dt in remaining:
		frappe.log_error(title=f"KenTender bds_chg_001_v08_retire_bid_slice: could not delete DocType {dt}", message=frappe.get_traceback())


def _drop_tables() -> None:
	"""Deleting a standard DocType row leaves its table; drop each one whose
	DocType is gone."""
	for dt in RETIRED_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			frappe.db.sql_ddl(f"drop table if exists `tab{dt}`")


def _delete_pages() -> None:
	for page in RETIRED_PAGES:
		if frappe.db.exists("Page", page):
			frappe.delete_doc("Page", page, force=True, ignore_permissions=True)


def execute() -> None:
	# AUD-XC-127: authorised for a site with no production data only.
	require_empty_or_authorised("bds_chg_001_v08_retire_bid_slice", RETIRED_DOCTYPES)
	_delete_rows()
	_delete_permission_rows()
	_delete_doctypes_multi_pass()
	_drop_tables()
	_delete_pages()
	frappe.clear_cache()
	frappe.db.commit()
