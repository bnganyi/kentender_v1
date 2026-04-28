from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.template_query_service import get_eligible_std_templates


def _ensure_no_duplicate_current_instance(tender_code: str, tender_context: dict) -> None:
	if tender_context.get("supersession_instance_code"):
		return
	existing = frappe.db.exists(
		"STD Instance",
		{
			"tender_code": tender_code,
			"instance_status": ("not in", ["Superseded", "Cancelled"]),
		},
	)
	if existing:
		frappe.throw(
			_("An active STD instance already exists for this tender; use supersession path."),
			title=_("Duplicate STD instance"),
		)


def _validate_active_version_and_profile(template_version_code: str, profile_code: str) -> tuple[dict, dict]:
	version = frappe.db.get_value(
		"STD Template Version",
		template_version_code,
		["version_code", "procurement_category", "works_profile_type", "version_status"],
		as_dict=True,
	)
	if not version or version.version_status != "Active":
		frappe.throw(_("Template version must be Active."), title=_("Invalid template version"))

	profile = frappe.db.get_value(
		"STD Applicability Profile",
		profile_code,
		[
			"profile_code",
			"version_code",
			"procurement_category",
			"works_profile_type",
			"profile_status",
			"requires_boq",
		],
		as_dict=True,
	)
	if not profile or profile.profile_status != "Active":
		frappe.throw(_("Applicability profile must be Active."), title=_("Invalid profile"))
	if profile.version_code != version.version_code:
		frappe.throw(_("Profile does not belong to template version."), title=_("Incompatible profile"))
	if profile.procurement_category != version.procurement_category:
		frappe.throw(
			_("Profile procurement category does not match template version."),
			title=_("Incompatible profile"),
		)
	return version, profile


def _validate_tender_context_compatibility(template_version_code: str, profile_code: str, tender_context: dict) -> None:
	procurement_category = tender_context.get("procurement_category")
	procurement_method = tender_context.get("procurement_method")
	if not procurement_category or not procurement_method:
		return
	query = get_eligible_std_templates(
		procurement_category=procurement_category,
		procurement_method=procurement_method,
		works_profile_type=tender_context.get("works_profile_type"),
		contract_type=tender_context.get("contract_type"),
	)
	eligible = {
		(row["template_version_code"], row["profile_code"])
		for row in query.get("eligible_templates", [])
	}
	if (template_version_code, profile_code) not in eligible:
		frappe.throw(_("Template/profile pair is not compatible with tender context."), title=_("Incompatible profile"))


def _build_placeholders(template_version_code: str, requires_boq: int) -> dict:
	section_placeholders = frappe.get_all(
		"STD Section Definition",
		filters={"version_code": template_version_code},
		fields=["section_code", "section_title", "editability"],
		limit=1000,
	)
	parameter_placeholders = frappe.get_all(
		"STD Parameter Definition",
		filters={"version_code": template_version_code},
		fields=["parameter_code", "label", "data_type", "required"],
		limit=1000,
	)
	works_requirement_placeholders = frappe.get_all(
		"STD Works Requirement Component Definition",
		filters={"version_code": template_version_code},
		fields=["component_code", "component_title", "component_type", "is_required"],
		limit=1000,
	)
	boq_placeholders: list[dict] = []
	if int(requires_boq):
		boq_placeholders = frappe.get_all(
			"STD BOQ Definition",
			filters={"version_code": template_version_code},
			fields=["boq_definition_code", "pricing_model", "supplier_input_mode"],
			limit=200,
		)
	return {
		"section_placeholders": section_placeholders,
		"parameter_placeholders": parameter_placeholders,
		"works_requirement_placeholders": works_requirement_placeholders,
		"boq_placeholders": boq_placeholders,
	}


@frappe.whitelist()
def create_std_instance(
	tender_code: str,
	template_version_code: str,
	profile_code: str,
	tender_context: dict | None,
	actor: str,
) -> dict:
	tender_context = tender_context or {}
	_ensure_no_duplicate_current_instance(tender_code, tender_context)
	_, profile = _validate_active_version_and_profile(template_version_code, profile_code)
	_validate_tender_context_compatibility(template_version_code, profile_code, tender_context)

	instance_code = f"STDINST-{frappe.generate_hash(length=10).upper()}"
	instance = frappe.get_doc(
		{
			"doctype": "STD Instance",
			"instance_code": instance_code,
			"tender_code": tender_code,
			"template_version_code": template_version_code,
			"profile_code": profile_code,
			"instance_status": "Draft",
			"readiness_status": "Not Run",
		}
	).insert(ignore_permissions=True)
	placeholders = _build_placeholders(template_version_code, int(profile.requires_boq or 0))

	record_std_audit_event(
		event_type="STD_INSTANCE_CREATED",
		object_type="STD_INSTANCE",
		object_code=instance.instance_code,
		actor=actor,
		new_state=instance.instance_status,
		reason="Created from active template/profile",
		metadata={
			"tender_code": tender_code,
			"template_version_code": template_version_code,
			"profile_code": profile_code,
			"placeholder_counts": {k: len(v) for k, v in placeholders.items()},
		},
	)
	return {"instance_code": instance.instance_code, **placeholders}

