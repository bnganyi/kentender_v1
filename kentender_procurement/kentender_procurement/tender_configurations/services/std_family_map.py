# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Map Procurement Package category fields → STD family key/label/codes."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.constants import (
	FIXTURE_STD_FAMILY_CODE,
	_FAMILY_ALIASES,
)


def normalize_category(raw: str | None) -> str:
	return cstr(raw or "").strip().lower()


def resolve_family_from_package(pkg: Any) -> dict[str, Any]:
	"""Return family_key, family_label, candidate_family_codes for a package."""
	candidates = [
		pkg.get("required_std_category") if hasattr(pkg, "get") else None,
		pkg.get("procurement_category") if hasattr(pkg, "get") else None,
	]
	# Document attribute access
	if not any(candidates):
		candidates = [
			getattr(pkg, "required_std_category", None),
			getattr(pkg, "procurement_category", None),
		]

	for raw in candidates:
		key = normalize_category(raw)
		if key in _FAMILY_ALIASES:
			family_key, label, codes = _FAMILY_ALIASES[key]
			return {
				"std_family_key": family_key,
				"std_family_label": label,
				"candidate_family_codes": list(codes),
			}

	# Fallback: look up STD Family by procurement_category match on DocType
	for raw in candidates:
		cat = cstr(raw or "").strip()
		if not cat:
			continue
		rows = frappe.get_all(
			"STD Family",
			filters={"procurement_category": cat},
			fields=["family_code", "family_name", "procurement_category"],
			limit=1,
		)
		if rows:
			row = rows[0]
			alias = _FAMILY_ALIASES.get(normalize_category(row.procurement_category))
			if alias:
				return {
					"std_family_key": alias[0],
					"std_family_label": alias[1],
					"candidate_family_codes": [row.family_code],
				}
			return {
				"std_family_key": cstr(row.family_code),
				"std_family_label": cstr(row.family_name),
				"candidate_family_codes": [row.family_code],
			}

	# Default IT when only Official Library IT family exists
	return {
		"std_family_key": "IT",
		"std_family_label": "Information Technology",
		"candidate_family_codes": [FIXTURE_STD_FAMILY_CODE],
	}


def resolve_procuring_entity_name(code: str | None) -> str:
	code = cstr(code or "").strip()
	if not code:
		return ""
	name = frappe.db.get_value("Procuring Entity", code, "entity_name")
	if name:
		return cstr(name)
	rows = frappe.get_all(
		"Procuring Entity",
		filters={"entity_code": code},
		fields=["entity_name"],
		limit=1,
	)
	if rows:
		return cstr(rows[0].entity_name)
	return code
