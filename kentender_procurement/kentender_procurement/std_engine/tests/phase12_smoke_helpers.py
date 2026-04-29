# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared helpers for Phase 12 (Smoke Contract) integration tests."""

from __future__ import annotations

import frappe

# Business codes from DOC 1 Works Building seed (Smoke Contract fixtures).
DOC1_SOURCE_DOCUMENT_CODE = "DOC1_WORKS_BUILDING_REV_APR_2022"
STD_WORKS_FAMILY_CODE = "STD-WORKS"
BUILDING_TEMPLATE_VERSION_CODE = "STDTV-WORKS-BUILDING-REV-APR-2022"
BUILDING_PROFILE_CODE = "WORKS-PROFILE-BUILDING-CIVIL-REV-APR-2022"


def doc1_building_seed_loaded() -> bool:
	"""True when the canonical Works Building seed is present (integration site)."""
	return bool(
		frappe.db.exists("Source Document Registry", {"source_document_code": DOC1_SOURCE_DOCUMENT_CODE})
		and frappe.db.exists("STD Template Family", {"template_code": STD_WORKS_FAMILY_CODE})
		and frappe.db.exists("STD Template Version", {"version_code": BUILDING_TEMPLATE_VERSION_CODE})
	)
