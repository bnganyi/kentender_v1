# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Thin adapter over STD Engine read + bindability checks."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.services.read_service import get_std_version
from kentender_procurement.std_engine.services.tender_binding_service import (
	assert_version_is_bindable,
)


def resolve_std_version(std_template_version_id: str) -> dict[str, Any]:
	"""Return STD version metadata after bindability check."""
	package_id = (std_template_version_id or "").strip()
	assert_version_is_bindable(package_id, simulate_active_for_test=True)
	payload = get_std_version(package_id)
	version = payload.get("version") or {}
	return {
		"package_id": package_id,
		"family_code": version.get("familyCode") or version.get("family_code"),
		"version_code": version.get("versionCode") or version.get("version_code"),
		"version_label": version.get("versionLabel") or version.get("version_label"),
		"package_hash": version.get("packageSha256") or version.get("package_sha256"),
		"lifecycle_state": version.get("lifecycleState") or version.get("lifecycle_state"),
	}


def get_active_it_std_version_id() -> str | None:
	"""Return first ACTIVE KE-PPRA-IT STD version on site."""
	row = frappe.db.get_value(
		"STD Version",
		{"family_code": "KE-PPRA-IT", "lifecycle_state": "ACTIVE"},
		"name",
	)
	return row
