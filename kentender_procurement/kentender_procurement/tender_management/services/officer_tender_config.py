# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — shared constants and helpers.

Planning corrections (2026): UX labels map to existing ``Procurement Tender.tender_status``
values without schema migration. See ``OFFICER_TENDER_STATUS_*`` and
``tender_status_to_officer_ux_label``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# POC template allowlist (planning correction §9)
OFFICER_POC_TEMPLATE_CODE: str = "KE-PPRA-WORKS-BLDG-2022-04-POC"

# Actual ``tender_status`` values on ``Procurement Tender`` (no migration this phase)
TENDER_STATUS_DRAFT: str = "Draft"
TENDER_STATUS_CONFIGURED: str = "Configured"
TENDER_STATUS_VALIDATION_FAILED: str = "Validation Failed"
TENDER_STATUS_VALIDATED: str = "Validated"
TENDER_STATUS_TENDER_PACK_GENERATED: str = "Tender Pack Generated"
TENDER_STATUS_POC_DEMONSTRATED: str = "POC Demonstrated"
TENDER_STATUS_CANCELLED: str = "Cancelled"

# Officer-facing UX labels (display only; storage uses ``tender_status`` above)
OFFICER_UX_DRAFT: str = "Draft"
OFFICER_UX_CONFIGURING: str = "Configuring"
OFFICER_UX_VALIDATION_FAILED: str = "Validation Failed"
OFFICER_UX_VALIDATED: str = "Validated"
OFFICER_UX_PREVIEW_GENERATED: str = "Preview Generated"
OFFICER_UX_READY_FOR_REVIEW: str = "Ready for Review"

# All non-cancelled statuses used in officer POC flows (ordered for dropdowns/tests)
OFFICER_FLOW_TENDER_STATUSES: tuple[str, ...] = (
	TENDER_STATUS_DRAFT,
	TENDER_STATUS_CONFIGURED,
	TENDER_STATUS_VALIDATION_FAILED,
	TENDER_STATUS_VALIDATED,
	TENDER_STATUS_TENDER_PACK_GENERATED,
	TENDER_STATUS_POC_DEMONSTRATED,
)


def tender_status_to_officer_ux_label(tender_status: str | None) -> str:
	"""Map stored ``tender_status`` to officer UX label (planning correction §1)."""
	if not tender_status:
		return OFFICER_UX_DRAFT
	m = {
		TENDER_STATUS_DRAFT: OFFICER_UX_DRAFT,
		TENDER_STATUS_CONFIGURED: OFFICER_UX_CONFIGURING,
		TENDER_STATUS_VALIDATION_FAILED: OFFICER_UX_VALIDATION_FAILED,
		TENDER_STATUS_VALIDATED: OFFICER_UX_VALIDATED,
		TENDER_STATUS_TENDER_PACK_GENERATED: OFFICER_UX_PREVIEW_GENERATED,
		TENDER_STATUS_POC_DEMONSTRATED: OFFICER_UX_READY_FOR_REVIEW,
		TENDER_STATUS_CANCELLED: "Cancelled",
	}
	return m.get(tender_status, tender_status)


def officer_ux_label_to_tender_status(ux_label: str | None) -> str | None:
	"""Map officer UX label back to ``tender_status`` (for tests / explicit transitions)."""
	if not ux_label:
		return None
	m = {
		OFFICER_UX_DRAFT: TENDER_STATUS_DRAFT,
		OFFICER_UX_CONFIGURING: TENDER_STATUS_CONFIGURED,
		OFFICER_UX_VALIDATION_FAILED: TENDER_STATUS_VALIDATION_FAILED,
		OFFICER_UX_VALIDATED: TENDER_STATUS_VALIDATED,
		OFFICER_UX_PREVIEW_GENERATED: TENDER_STATUS_TENDER_PACK_GENERATED,
		OFFICER_UX_READY_FOR_REVIEW: TENDER_STATUS_POC_DEMONSTRATED,
	}
	return m.get(ux_label)


# Cursor boundary prompt — forbidden capability phrases (scope doc §21); used in baseline tests
OFFICER_SCOPE_BOUNDARY_FORBIDDEN_PHRASES: tuple[str, ...] = (
	"Build template editor",
	"Build bidder portal",
	"Build tender publication workflow",
	"Build PDF generation",
	"Build production BoQ module",
)


def load_officer_fields_document(package_path: Path | None = None) -> dict[str, Any]:
	"""Load ``fields.json`` from the STD-WORKS-POC package (officer field model source)."""
	from kentender_procurement.tender_management.services.std_template_loader import (
		get_template_package_path,
		load_json_file,
	)

	root = package_path if package_path is not None else get_template_package_path()
	return load_json_file(root / "fields.json")


def build_officer_guided_field_model(fields_doc: dict[str, Any]) -> dict[str, Any]:
	"""Build grouped officer field model from a ``fields.json`` payload (doc 3 §6–§7)."""
	groups: dict[str, Any] = {g["group_code"]: {**g, "fields": []} for g in fields_doc.get("field_groups", [])}
	for field in fields_doc.get("fields", []):
		gc = field.get("group_code")
		if gc not in groups:
			continue
		required_mode = "Always" if field.get("required_by_default") else "Optional"
		if field.get("poc_required") and not field.get("required_by_default"):
			required_mode = "POC required"
		groups[gc]["fields"].append(
			{
				"field_code": field.get("field_code"),
				"label": field.get("label"),
				"field_type": field.get("field_type"),
				"required_mode": required_mode,
				"ordinary_user_editable": bool(field.get("ordinary_user_editable", True)),
				"help_text": field.get("help_text"),
			}
		)
	ordered = sorted(groups.values(), key=lambda g: int(g.get("render_order") or 999))
	return {"template_code": fields_doc.get("template_code"), "groups": ordered}


def get_officer_guided_field_model(package_path: Path | None = None) -> dict[str, Any]:
	"""Return grouped guided configuration model for the Works POC package."""
	fields_doc = load_officer_fields_document(package_path)
	return build_officer_guided_field_model(fields_doc)
