# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR FU-25 / BDS-CHG-001 v0.8 plan Phase 5 (Tenders tracker TND12-B05):
Bid Submission now registers `kt_tender_candidate_registry`, so the Tenders
stand-in candidate registry is retired. Its rows are deleted outright, not
migrated (owner decision carried from 21 Sep 2026: legacy bid records are
deleted, never migrated); the canonical seed registers the candidate again
through Start bid. Notices already sent keep their recorded destinations."""

from __future__ import annotations

import frappe

from kentender_core.utils.patch_guards import require_empty_or_authorised

STAND_IN = "Tender Candidate Registration"


def execute() -> None:
	# AUD-XC-127: authorised for a site with no production data only.
	require_empty_or_authorised("tpr_fu25_retire_candidate_stand_in", (STAND_IN,))
	if frappe.db.table_exists(STAND_IN):
		frappe.db.delete(STAND_IN)
	if frappe.db.exists("DocType", STAND_IN):
		frappe.delete_doc("DocType", STAND_IN, force=True, ignore_permissions=True, ignore_missing=True)
	frappe.db.sql_ddl(f"drop table if exists `tab{STAND_IN}`")
