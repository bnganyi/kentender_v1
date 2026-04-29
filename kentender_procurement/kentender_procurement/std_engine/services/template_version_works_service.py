"""STD workbench: Template Version works configuration catalogue (STD-CURSOR-1011)."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


BOQ_WARNING = str(
	_(
		"Works BOQ quantities are controlled by the Procuring Entity. Suppliers enter rates only where permitted. Arithmetic correction must be generated into the Evaluation Model, not Submission or Opening."
	)
)
CONTRACT_PRICE_WARNING = str(
	_(
		"For Works BOQ procurement, contract price must source from the corrected evaluated BOQ total produced by Evaluation/Award."
	)
)


def _to_bool(value) -> bool:
	try:
		return bool(int(value or 0))
	except (TypeError, ValueError):
		return False


def build_std_template_version_works_configuration(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return Works profile rules + BOQ/readiness/evaluation/carry-forward references."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (version_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Version code is required."))}

	resolved = resolve_std_document("Template Version", code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": str(_("No document matches this version code.")),
			"version_code": code,
		}
	doctype, name, doc = resolved
	if doctype != "STD Template Version":
		return {"ok": False, "error": "invalid", "message": str(_("Not a template version."))}
	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	profiles = frappe.get_all(
		"STD Applicability Profile",
		filters={"version_code": code},
		fields=[
			"profile_code",
			"profile_title",
			"profile_status",
			"procurement_category",
			"works_profile_type",
			"requires_boq",
			"requires_drawings",
			"requires_specifications",
			"requires_site_information",
			"requires_hse_requirements",
			"requires_environmental_social_requirements",
		],
		order_by="profile_code asc",
	)
	works_profile = None
	if profiles:
		p = profiles[0]
		works_profile = {
			"profile_code": p.get("profile_code"),
			"profile_title": p.get("profile_title"),
			"profile_status": p.get("profile_status"),
			"procurement_category": p.get("procurement_category"),
			"works_profile_type": p.get("works_profile_type"),
			"requires_boq": _to_bool(p.get("requires_boq")),
			"requires_drawings": _to_bool(p.get("requires_drawings")),
			"requires_specifications": _to_bool(p.get("requires_specifications")),
			"requires_site_information": _to_bool(p.get("requires_site_information")),
			"requires_hse_requirements": _to_bool(p.get("requires_hse_requirements")),
			"requires_environmental_social_requirements": _to_bool(p.get("requires_environmental_social_requirements")),
		}

	works_components = frappe.get_all(
		"STD Works Requirement Component Definition",
		filters={"version_code": code},
		fields=[
			"component_code",
			"component_title",
			"component_type",
			"is_required",
			"supports_structured_text",
			"supports_table_data",
			"supports_attachments",
			"attachment_required",
			"drives_dsm",
			"drives_dem",
			"drives_dcm",
		],
		order_by="component_code asc",
	)
	for row in works_components:
		for f in (
			"is_required",
			"supports_structured_text",
			"supports_table_data",
			"supports_attachments",
			"attachment_required",
			"drives_dsm",
			"drives_dem",
			"drives_dcm",
		):
			row[f] = _to_bool(row.get(f))

	boq = frappe.get_all(
		"STD BOQ Definition",
		filters={"version_code": code},
		fields=[
			"boq_definition_code",
			"pricing_model",
			"quantity_owner",
			"supplier_input_mode",
			"arithmetic_correction_stage",
			"is_required_for_readiness",
		],
		order_by="boq_definition_code asc",
		limit=1,
	)
	boq_definition = boq[0] if boq else None
	if boq_definition:
		boq_definition["is_required_for_readiness"] = _to_bool(boq_definition.get("is_required_for_readiness"))

	evaluation_rules = frappe.get_all(
		"STD Extraction Mapping",
		filters={"version_code": code, "source_object_type": "Evaluation Rule"},
		fields=["mapping_code", "source_object_code", "target_model", "target_component_type", "mandatory"],
		order_by="mapping_code asc",
	)
	carry_forward = frappe.get_all(
		"STD Extraction Mapping",
		filters={"version_code": code, "target_model": "DCM"},
		fields=["mapping_code", "source_object_type", "source_object_code", "target_component_type", "mandatory"],
		order_by="mapping_code asc",
	)
	for row in evaluation_rules + carry_forward:
		row["mandatory"] = _to_bool(row.get("mandatory"))

	readiness_rules = [
		{
			"id": "works_profile_configured",
			"label": str(_("Works profile configured")),
			"status": bool(works_profile),
		},
		{
			"id": "boq_definition_present",
			"label": str(_("BOQ definition present")),
			"status": bool(boq_definition),
		},
		{
			"id": "works_components_present",
			"label": str(_("Works requirement components present")),
			"status": bool(works_components),
		},
	]

	return {
		"ok": True,
		"version_code": code,
		"works_profile": works_profile,
		"works_components": works_components,
		"boq_definition": boq_definition,
		"evaluation_rule_templates": evaluation_rules,
		"contract_carry_forward_templates": carry_forward,
		"readiness_rules": readiness_rules,
		"warnings": {
			"boq_warning": BOQ_WARNING,
			"contract_price_warning": CONTRACT_PRICE_WARNING,
		},
	}
