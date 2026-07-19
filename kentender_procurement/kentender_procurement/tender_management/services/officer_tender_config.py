# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Thin compatibility shim for planning→tender handoff merge path.

Restores ``merge_officer_overlay_into_configuration`` expected by
``planning_tender_handoff_configuration`` after the full officer POC module
was archived. Delegates guided-field merge to ``officer_guided_field_registry``.
"""

from __future__ import annotations

from typing import Any


def merge_officer_overlay_into_configuration(
	existing: dict[str, Any], tender_doc: Any
) -> dict[str, Any]:
	"""Deep-merge officer-owned keys; preserve unknown ``configuration_json`` keys."""
	from kentender_procurement.tender_management.services.officer_guided_field_registry import (
		merge_registry_overlay_into_configuration,
	)

	merged = merge_registry_overlay_into_configuration(existing, tender_doc)
	merged["SYSTEM.TEMPLATE_CODE"] = getattr(tender_doc, "template_code", None) or merged.get(
		"SYSTEM.TEMPLATE_CODE", ""
	)
	merged["SYSTEM.PACKAGE_VERSION"] = getattr(tender_doc, "template_version", None) or merged.get(
		"SYSTEM.PACKAGE_VERSION", ""
	)
	merged["SYSTEM.PACKAGE_HASH"] = getattr(tender_doc, "package_hash", None) or merged.get(
		"SYSTEM.PACKAGE_HASH", ""
	)
	merged["SYSTEM.PROCUREMENT_CATEGORY"] = (
		getattr(tender_doc, "procurement_category", None)
		or merged.get("SYSTEM.PROCUREMENT_CATEGORY")
		or "WORKS"
	)
	return merged
