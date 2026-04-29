from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.stale_output_service import (
	infer_change_kind_from_attachment_classification,
	mark_std_outputs_stale,
)


def _sha256_text(value: str) -> str:
	return hashlib.sha256(value.encode("utf-8")).hexdigest()


@frappe.whitelist()
def add_std_section_attachment(
	instance_code: str,
	section_code: str,
	file_reference: str,
	classification: str,
	actor: str,
	component_code: str | None = None,
) -> dict[str, Any]:
	if not section_code:
		frappe.throw(_("Section code is required."), title=_("Invalid attachment"))
	if not classification:
		frappe.throw(_("Attachment classification is required."), title=_("Invalid attachment"))
	if classification not in {"Specification", "Drawing", "Supporting"}:
		frappe.throw(_("Invalid attachment classification."), title=_("Invalid attachment"))
	if not file_reference:
		frappe.throw(_("File reference is required."), title=_("Invalid attachment"))

	instance_name = frappe.db.get_value("STD Instance", {"instance_code": instance_code}, "name")
	if not instance_name:
		frappe.throw(_("STD instance not found."), title=_("Invalid attachment"))
	instance = frappe.get_doc("STD Instance", instance_name)
	if instance.instance_status in {"Published Locked", "Superseded", "Cancelled"}:
		frappe.throw(
			_("Published/locked instance cannot accept direct attachment replacement; use addendum path."),
			title=_("Instance locked"),
		)

	section = frappe.db.get_value(
		"STD Section Definition",
		{"section_code": section_code},
		["section_code", "version_code", "section_number", "section_title"],
		as_dict=True,
	)
	if not section:
		frappe.throw(_("Section code is invalid."), title=_("Invalid attachment"))
	if section.version_code != instance.template_version_code:
		frappe.throw(_("Unbound attachment: section does not belong to instance template."), title=_("Unbound attachment"))

	if component_code:
		component = frappe.db.get_value(
			"STD Works Requirement Component Definition",
			{"component_code": component_code},
			["component_code", "version_code", "section_code"],
			as_dict=True,
		)
		if not component:
			frappe.throw(_("Component code is invalid."), title=_("Invalid attachment"))
		if component.version_code != instance.template_version_code or component.section_code != section_code:
			frappe.throw(_("Component is not bound to this section/template."), title=_("Unbound attachment"))

	existing_published = frappe.db.get_value(
		"STD Section Attachment",
		{
			"instance_code": instance_code,
			"section_code": section_code,
			"classification": classification,
			"status": "Published",
		},
		["attachment_code"],
		as_dict=True,
	)
	if existing_published:
		frappe.throw(
			_("Published attachment cannot be overwritten directly; supersede via addendum path."),
			title=_("Supersession required"),
		)

	doc = frappe.get_doc(
		{
			"doctype": "STD Section Attachment",
			"attachment_code": f"SATT-{frappe.generate_hash(length=10).upper()}",
			"instance_code": instance_code,
			"section_code": section_code,
			"component_code": component_code,
			"classification": classification,
			"file_reference": file_reference,
			"file_hash": _sha256_text(file_reference),
			"status": "Draft",
			"supersedes_attachment_code": None,
		}
	).insert(ignore_permissions=True)

	mark_std_outputs_stale(instance_code, infer_change_kind_from_attachment_classification(classification), actor=actor)

	frappe.flags.std_transition_service_context = True
	try:
		instance.readiness_status = "Invalidated"
		instance.save(ignore_permissions=True)
	finally:
		frappe.flags.std_transition_service_context = False
	invalidated_outputs: list[str] = []
	output_rows = frappe.get_all(
		"STD Generated Output",
		filters={"instance_code": instance_code, "status": ("in", ["Current", "Published"])},
		fields=["name", "output_code"],
		limit=200,
	)
	for row in output_rows:
		out_doc = frappe.get_doc("STD Generated Output", row["name"])
		frappe.flags.std_transition_service_context = True
		try:
			out_doc.status = "Draft"
			out_doc.save(ignore_permissions=True)
		finally:
			frappe.flags.std_transition_service_context = False
		invalidated_outputs.append(row["output_code"])

	record_std_audit_event(
		event_type="SECTION_ATTACHMENT_ADDED",
		object_type="STD_INSTANCE",
		object_code=instance_code,
		actor=actor,
		previous_state=instance.instance_status,
		new_state=instance.instance_status,
		metadata={
			"attachment_code": doc.attachment_code,
			"section_code": section_code,
			"classification": classification,
			"component_code": component_code,
			"invalidated_outputs": invalidated_outputs,
		},
	)

	return {
		"attachment_code": doc.attachment_code,
		"instance_code": instance_code,
		"section_code": section_code,
		"classification": classification,
		"file_hash": doc.file_hash,
		"readiness_status": instance.readiness_status,
		"invalidated_outputs": invalidated_outputs,
	}

