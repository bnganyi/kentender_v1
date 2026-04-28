from __future__ import annotations

import json
from typing import Any

import frappe


def _as_list(raw_value: Any) -> list[str]:
	if raw_value in (None, ""):
		return []
	if isinstance(raw_value, list):
		return [str(v) for v in raw_value]
	if isinstance(raw_value, str):
		try:
			decoded = json.loads(raw_value)
		except Exception:
			return [raw_value]
		if isinstance(decoded, list):
			return [str(v) for v in decoded]
		return [str(decoded)]
	return [str(raw_value)]


@frappe.whitelist()
def get_eligible_std_templates(
	procurement_category: str,
	procurement_method: str,
	works_profile_type: str | None = None,
	contract_type: str | None = None,
) -> dict[str, Any]:
	version_rows = frappe.get_all(
		"STD Template Version",
		filters={"version_status": "Active", "procurement_category": procurement_category},
		fields=["version_code", "template_code", "version_label", "procurement_category", "works_profile_type"],
		limit=500,
	)
	if not version_rows:
		return {"eligible_templates": [], "blocking_reason": "NO_ACTIVE_TEMPLATE_VERSION"}

	family_codes = {row["template_code"] for row in version_rows}
	family_rows = frappe.get_all(
		"STD Template Family",
		filters={"template_code": ("in", list(family_codes))},
		fields=["template_code", "allowed_procurement_methods"],
		limit=500,
	)
	family_methods = {
		row["template_code"]: _as_list(row.get("allowed_procurement_methods")) for row in family_rows
	}
	filtered_versions = [
		row
		for row in version_rows
		if procurement_method in family_methods.get(row["template_code"], [])
	]
	if not filtered_versions:
		return {"eligible_templates": [], "blocking_reason": "NO_METHOD_COMPATIBLE_TEMPLATE_VERSION"}

	version_codes = [row["version_code"] for row in filtered_versions]
	profile_rows = frappe.get_all(
		"STD Applicability Profile",
		filters={
			"profile_status": "Active",
			"procurement_category": procurement_category,
			"version_code": ("in", version_codes),
		},
		fields=[
			"profile_code",
			"profile_title",
			"version_code",
			"works_profile_type",
			"allowed_methods",
			"allowed_contract_types",
		],
		limit=500,
	)

	eligible: list[dict[str, Any]] = []
	version_map = {row["version_code"]: row for row in filtered_versions}
	for profile in profile_rows:
		methods = _as_list(profile.get("allowed_methods"))
		if procurement_method not in methods:
			continue
		if procurement_category == "Works" and works_profile_type and profile.get("works_profile_type") != works_profile_type:
			continue
		allowed_contract_types = _as_list(profile.get("allowed_contract_types"))
		if contract_type and allowed_contract_types and contract_type not in allowed_contract_types:
			continue
		version = version_map.get(profile["version_code"])
		if not version:
			continue
		eligible.append(
			{
				"template_version_code": version["version_code"],
				"template_code": version["template_code"],
				"version_label": version["version_label"],
				"profile_code": profile["profile_code"],
				"profile_title": profile["profile_title"],
				"procurement_category": procurement_category,
				"works_profile_type": profile.get("works_profile_type"),
				"allowed_methods": methods,
				"allowed_contract_types": allowed_contract_types,
			}
		)

	if not eligible:
		return {"eligible_templates": [], "blocking_reason": "NO_ACTIVE_COMPATIBLE_PROFILE"}
	return {"eligible_templates": eligible, "blocking_reason": None}

