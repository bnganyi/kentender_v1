from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event


def _get_instance(instance_code: str):
	name = frappe.db.get_value("STD Instance", {"instance_code": instance_code}, "name")
	if not name:
		frappe.throw(_("STD instance not found."), title=_("Invalid instance"))
	return frappe.get_doc("STD Instance", name)


def _runtime_row(instance_code: str, component_code: str):
	name = frappe.db.get_value(
		"STD Instance Works Requirement Component",
		{"instance_code": instance_code, "component_code": component_code},
		"name",
	)
	return frappe.get_doc("STD Instance Works Requirement Component", name) if name else None


@frappe.whitelist()
def get_works_requirement_components(instance_code: str) -> list[dict[str, Any]]:
	instance = _get_instance(instance_code)
	definitions = frappe.get_all(
		"STD Works Requirement Component Definition",
		filters={"version_code": instance.template_version_code},
		fields=[
			"component_code",
			"section_code",
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
		limit=1000,
	)
	rows = []
	for d in definitions:
		rt = _runtime_row(instance_code, d["component_code"])
		attachments = frappe.db.count(
			"STD Section Attachment",
			{"instance_code": instance_code, "component_code": d["component_code"], "status": ("!=", "Superseded")},
		)
		rows.append(
			{
				**d,
				"structured_text": (rt.structured_text if rt else None),
				"table_data": (json.loads(rt.table_data) if (rt and rt.table_data) else None),
				"completion_status": (rt.completion_status if rt else "Not Started"),
				"attachment_count": attachments,
			}
		)
	return rows


@frappe.whitelist()
def update_works_requirement_component(instance_code: str, component_code: str, payload: dict, actor: str) -> dict[str, Any]:
	instance = _get_instance(instance_code)
	if instance.instance_status in {"Published Locked", "Superseded", "Cancelled"}:
		frappe.throw(_("Works requirement edits are locked after publication."), title=_("Instance locked"))

	component = frappe.db.get_value(
		"STD Works Requirement Component Definition",
		{"component_code": component_code},
		["component_code", "version_code", "supports_structured_text", "supports_table_data", "drives_dsm", "drives_dem", "drives_dcm"],
		as_dict=True,
	)
	if not component or component.version_code != instance.template_version_code:
		frappe.throw(_("Component does not belong to instance template."), title=_("Invalid component"))

	rt = _runtime_row(instance_code, component_code)
	if not rt:
		rt = frappe.get_doc(
			{
				"doctype": "STD Instance Works Requirement Component",
				"instance_component_code": f"SWRC-{frappe.generate_hash(length=10).upper()}",
				"instance_code": instance_code,
				"component_code": component_code,
				"completion_status": "Not Started",
			}
		).insert(ignore_permissions=True)

	if "structured_text" in payload:
		if not int(component.supports_structured_text or 0):
			frappe.throw(_("Component does not support structured text."), title=_("Invalid payload"))
		rt.structured_text = payload.get("structured_text") or ""
	if "table_data" in payload:
		if not int(component.supports_table_data or 0):
			frappe.throw(_("Component does not support table data."), title=_("Invalid payload"))
		td = payload.get("table_data")
		rt.table_data = json.dumps(td) if td is not None else None

	if rt.structured_text or rt.table_data:
		rt.completion_status = "Complete"
	else:
		rt.completion_status = "In Progress"
	rt.updated_by = actor
	rt.save(ignore_permissions=True)

	frappe.flags.std_transition_service_context = True
	try:
		instance.readiness_status = "Invalidated"
		instance.save(ignore_permissions=True)
	finally:
		frappe.flags.std_transition_service_context = False
	invalidated_outputs: list[str] = []
	if int(component.drives_dsm or 0) or int(component.drives_dem or 0) or int(component.drives_dcm or 0):
		outputs = frappe.get_all(
			"STD Generated Output",
			filters={"instance_code": instance_code, "status": ("in", ["Current", "Published"])},
			fields=["name", "output_code"],
			limit=200,
		)
		for row in outputs:
			doc = frappe.get_doc("STD Generated Output", row["name"])
			frappe.flags.std_transition_service_context = True
			try:
				doc.status = "Draft"
				doc.save(ignore_permissions=True)
			finally:
				frappe.flags.std_transition_service_context = False
			invalidated_outputs.append(row["output_code"])

	record_std_audit_event(
		event_type="WORKS_REQUIREMENT_UPDATED",
		object_type="STD_INSTANCE",
		object_code=instance_code,
		actor=actor,
		metadata={"component_code": component_code, "completion_status": rt.completion_status},
	)
	return {
		"instance_code": instance_code,
		"component_code": component_code,
		"completion_status": rt.completion_status,
		"readiness_status": instance.readiness_status,
		"invalidated_outputs": invalidated_outputs,
	}


@frappe.whitelist()
def validate_works_requirements(instance_code: str, persist: bool = True) -> dict[str, Any]:
	instance = _get_instance(instance_code)
	definitions = frappe.get_all(
		"STD Works Requirement Component Definition",
		filters={"version_code": instance.template_version_code},
		fields=["component_code", "component_title", "section_code", "is_required", "attachment_required"],
		limit=1000,
	)
	blockers: list[dict[str, str]] = []
	for d in definitions:
		rt = _runtime_row(instance_code, d["component_code"])
		if int(d["is_required"] or 0) and (not rt or rt.completion_status != "Complete"):
			blockers.append({"component_code": d["component_code"], "reason": "REQUIRED_COMPONENT_INCOMPLETE"})
		if int(d["attachment_required"] or 0):
			has_attachment = frappe.db.exists(
				"STD Section Attachment",
				{
					"instance_code": instance_code,
					"component_code": d["component_code"],
					"section_code": d["section_code"],
					"status": ("!=", "Superseded"),
				},
			)
			if not has_attachment:
				blockers.append({"component_code": d["component_code"], "reason": "ATTACHMENT_REQUIRED"})

	ready = len(blockers) == 0
	new_status = "Ready" if ready else "Blocked"
	if persist:
		frappe.flags.std_transition_service_context = True
		try:
			instance.readiness_status = new_status
			instance.save(ignore_permissions=True)
		finally:
			frappe.flags.std_transition_service_context = False
	return {
		"instance_code": instance_code,
		"is_valid": ready,
		"blockers": blockers,
		"readiness_status": instance.readiness_status if persist else new_status,
	}

