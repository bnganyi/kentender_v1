# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 — Procurement Requisitions API surface (§10.1 reads,
§10.2 commands).

Every endpoint keeps an explicit signature: a whitelisted `**kwargs` method
receives the whole `form_dict` (including `cmd`/`csrf_token`), which is how
NDS-914 once broke four commands over HTTP while every direct-service test
passed. A form field named `values` also shadows `frappe._dict.values()`, so
every JSON payload parameter is named for what it carries.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_requisitions.services import authorise, correction, draft_commands as cmd, lifecycle, read


def _parse_json(value, default):
	"""HTTP transports lists/dicts as JSON strings; direct callers pass values.
	`from __future__ import annotations` disables Frappe's own coercion."""
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


# --------------------------------------------------------------------------
# §10.1 Reads
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_requisition_workspace(workspace_filters=None) -> dict[str, Any]:
	return read.get_requisition_workspace(filters=_parse_json(workspace_filters, {}))


@frappe.whitelist()
def get_start_preview(plan_item_id: str) -> dict[str, Any]:
	return read.get_start_preview(plan_item_id=plan_item_id)


@frappe.whitelist()
def get_requisition_record(requisition: str, version: str | None = None) -> dict[str, Any]:
	return read.get_requisition_record(requisition=requisition, version=version or None)


@frappe.whitelist()
def get_department_approval_task(task: str) -> dict[str, Any]:
	return read.get_department_approval_task(task=task)


@frappe.whitelist()
def get_procurement_authorisation_task(task: str) -> dict[str, Any]:
	return read.get_procurement_authorisation_task(task=task)


@frappe.whitelist()
def get_authorised_requisition_handoff(requisition: str) -> dict[str, Any]:
	return read.get_authorised_requisition_handoff(requisition=requisition)


@frappe.whitelist()
def export_requisition(requisition: str, version: str | None = None) -> dict[str, Any]:
	return read.export_requisition(requisition=requisition, version=version or None)


@frappe.whitelist()
def get_requisition_history(requisition: str) -> dict[str, Any]:
	return read.get_requisition_history(requisition=requisition)


@frappe.whitelist()
def list_eligible_handoffs() -> list[dict[str, Any]]:
	return read.list_eligible_handoffs()


@frappe.whitelist()
def validate_requisition(requisition: str) -> dict[str, Any]:
	return cmd.validate_requisition(requisition=requisition)


# --------------------------------------------------------------------------
# §10.2 Draft commands
# --------------------------------------------------------------------------


@frappe.whitelist()
def prepare_it_equipment_requisition(plan_item_id: str, idempotency_key: str) -> dict[str, Any]:
	return cmd.prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_requisition_summary(requisition: str, summary_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.save_requisition_summary(requisition=requisition, values=_parse_json(summary_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_same_specification_items(requisition: str, shared_values, item_rows, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_same_specification_items(requisition=requisition, shared=_parse_json(shared_values, {}), rows=_parse_json(item_rows, []), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_shared_item_details(requisition: str, requisition_item_ids, shared_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_shared_item_details(requisition=requisition, requisition_item_ids=_parse_json(requisition_item_ids, []), shared=_parse_json(shared_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_requisition_item(requisition: str, requisition_item_id: str, item_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_requisition_item(requisition=requisition, requisition_item_id=requisition_item_id, values=_parse_json(item_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_requisition_item(requisition: str, requisition_item_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_requisition_item(requisition=requisition, requisition_item_id=requisition_item_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_requirement_proposal_draft(requisition: str, proposal_digest: str, technical_rows, acceptance_rows, support_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.save_requirement_proposal_draft(
		requisition=requisition, proposal_digest=proposal_digest, technical=_parse_json(technical_rows, []), acceptance=_parse_json(acceptance_rows, []),
		support=_parse_json(support_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def apply_selected_requirement_package(requisition: str, profile_key: str, profile_version: str, proposal_digest: str, technical_rows, acceptance_rows, support_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.apply_selected_requirement_package(
		requisition=requisition, profile_key=profile_key, profile_version=profile_version, proposal_digest=proposal_digest,
		technical=_parse_json(technical_rows, []), acceptance=_parse_json(acceptance_rows, []), support=_parse_json(support_values, {}),
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def reset_standard_values(requisition: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.reset_standard_values(requisition=requisition, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_warranty_and_support(requisition: str, warranty_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.save_warranty_and_support(requisition=requisition, values=_parse_json(warranty_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_technical_requirement(requisition: str, technical_requirement_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_technical_requirement(requisition=requisition, values=_parse_json(technical_requirement_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def customise_requirement_for_item(requisition: str, requirement_id: str, requisition_item_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.customise_requirement_for_item(requisition=requisition, requirement_id=requirement_id, requisition_item_id=requisition_item_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_technical_requirement(requisition: str, technical_requirement_id: str, technical_requirement_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_technical_requirement(requisition=requisition, technical_requirement_id=technical_requirement_id, values=_parse_json(technical_requirement_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_technical_requirement(requisition: str, technical_requirement_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_technical_requirement(requisition=requisition, technical_requirement_id=technical_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_related_service(requisition: str, service_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_related_service(requisition=requisition, values=_parse_json(service_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_related_service(requisition: str, service_requirement_id: str, service_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_related_service(requisition=requisition, service_requirement_id=service_requirement_id, values=_parse_json(service_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_related_service(requisition: str, service_requirement_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_related_service(requisition=requisition, service_requirement_id=service_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_acceptance_requirement(requisition: str, acceptance_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_acceptance_requirement(requisition=requisition, values=_parse_json(acceptance_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_acceptance_requirement(requisition: str, acceptance_requirement_id: str, acceptance_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_acceptance_requirement(requisition=requisition, acceptance_requirement_id=acceptance_requirement_id, values=_parse_json(acceptance_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_acceptance_requirement(requisition: str, acceptance_requirement_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_acceptance_requirement(requisition=requisition, acceptance_requirement_id=acceptance_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_supporting_material(requisition: str, material_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_supporting_material(requisition=requisition, values=_parse_json(material_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_supporting_material(requisition: str, supporting_material_id: str, material_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_supporting_material(requisition=requisition, supporting_material_id=supporting_material_id, values=_parse_json(material_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_supporting_material(requisition: str, supporting_material_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_supporting_material(requisition=requisition, supporting_material_id=supporting_material_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


# --------------------------------------------------------------------------
# §10.2 Lifecycle commands
# --------------------------------------------------------------------------


@frappe.whitelist()
def send_for_department_approval(requisition: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_requisition_to_procurement(requisition: str, expected_record_version, idempotency_key: str, task: str | None = None) -> dict[str, Any]:
	return lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=expected_record_version, idempotency_key=idempotency_key, task=task or None)


@frappe.whitelist()
def return_to_department_author(task: str, reason: str, expected_record_version, idempotency_key: str, affected_section: str | None = None) -> dict[str, Any]:
	return lifecycle.return_to_department_author(task=task, reason=reason, affected_section=affected_section or "", expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_requisition_to_department(task: str, reason: str, expected_record_version, idempotency_key: str, affected_section: str | None = None) -> dict[str, Any]:
	return lifecycle.return_requisition_to_department(task=task, reason=reason, affected_section=affected_section or "", expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def change_requisition_lead_department(task: str, new_lead_org_unit: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.change_requisition_lead_department(task=task, new_lead_org_unit=new_lead_org_unit, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def withdraw_requisition(requisition: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.withdraw_requisition(requisition=requisition, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def request_upstream_plan_correction(requisition: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.request_upstream_plan_correction(requisition=requisition, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def authorise_requisition(requisition: str, task: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return authorise.authorise_requisition(requisition=requisition, task=task, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def revoke_unconsumed_authorisation(requisition: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return authorise.revoke_unconsumed_authorisation(requisition=requisition, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def prepare_requisition_after_plan_correction(requisition: str, idempotency_key: str) -> dict[str, Any]:
	return correction.prepare_requisition_after_plan_correction(requisition=requisition, idempotency_key=idempotency_key)


@frappe.whitelist()
def create_requisition_correction_draft(requisition: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return correction.create_requisition_correction_draft(requisition=requisition, expected_record_version=expected_record_version, idempotency_key=idempotency_key)
