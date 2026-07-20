# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure KE-PPRA-IT-2022-04 is ACTIVE with full form locked legal text."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.std_engine.constants import (
	CANONICAL_FAMILY_CODE,
	CANONICAL_PACKAGE_ID,
)
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import (
	force_reset_package_state_for_tests,
)
from kentender_procurement.std_engine.paths import (
	default_official_pdf_path,
	default_seed_zip_path_v1_1,
)
from kentender_procurement.std_engine.services.activation_readiness_service import (
	sync_activation_flags,
)
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.form_locked_text import (
	assert_form_locked_text_complete,
	ensure_form_locked_clauses,
	inventory_form_locked_text,
)
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending


def ensure_active_canonical_ppra_it_std(*, force_reimport: bool = False) -> dict[str, Any]:
	"""Import (if needed), load form locked bodies, approve, and activate the PPRA IT STD.

	Safe for developer_mode / tests. Does not invent form legal text — uses
	``forms/form_locked_bodies.json`` extracted from the official STD PDF.
	"""
	package_id = CANONICAL_PACKAGE_ID
	lifecycle = ""
	if frappe.db.exists("STD Version", package_id):
		lifecycle = cstr(frappe.db.get_value("STD Version", package_id, "lifecycle_state"))

	inventory = (
		inventory_form_locked_text(package_id)
		if lifecycle == "ACTIVE" and not force_reimport
		else {"complete": False}
	)
	if lifecycle == "ACTIVE" and inventory.get("complete") and not force_reimport:
		return {
			"packageId": package_id,
			"lifecycleState": "ACTIVE",
			"reimported": False,
			"inventory": inventory,
		}

	# ACTIVE without form bodies (or force): demote + replace-draft import path.
	force_reset_package_state_for_tests(package_id, family_code=CANONICAL_FAMILY_CODE)
	CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()
	form_load = ensure_form_locked_clauses(package_id)
	approve_all_pending(package_id)
	sync_activation_flags(package_id)
	activation = activate_version(package_id)
	assert_form_locked_text_complete(package_id)
	return {
		"packageId": package_id,
		"lifecycleState": cstr(
			frappe.db.get_value("STD Version", package_id, "lifecycle_state")
		),
		"reimported": True,
		"formLoad": form_load,
		"activation": activation,
		"inventory": inventory_form_locked_text(package_id),
	}
