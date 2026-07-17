# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared STD activation fixtures for IT Wizard integration tests."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import force_reset_package_state_for_tests
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.activation_readiness_service import sync_activation_flags
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending


def canonical_it_std_is_active() -> bool:
	if not frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
		return False
	return (
		frappe.db.get_value("STD Version", CANONICAL_PACKAGE_ID, "lifecycle_state") or ""
	).strip() == "ACTIVE"


def ensure_canonical_it_std_active_for_tests(*, force: bool = False) -> None:
	"""Ensure KE-PPRA-IT canonical STD is ACTIVE without redundant zip import."""
	if not force and canonical_it_std_is_active():
		frappe.set_user("Administrator")
		return

	force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
	CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()
	approve_all_pending(CANONICAL_PACKAGE_ID)
	sync_activation_flags(CANONICAL_PACKAGE_ID)
	activate_version(CANONICAL_PACKAGE_ID)
	frappe.set_user("Administrator")
