# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — Procurement Requisitions API surface (§10.1 reads,
§10.2 commands).

Every endpoint keeps an explicit signature: the framework passes the whole
`form_dict` (including `cmd`/`csrf_token`) into a whitelisted method that
declares `**kwargs`, which is exactly how NDS-914 broke four commands over
HTTP while every direct-service test passed (`procurement_planning.api`'s
own docstring). A form-encoded field named `values` also shadows
`frappe._dict.values()` on `frappe.local.form_dict` — every JSON-payload
parameter here is therefore named for what it carries (`item_values`,
`technical_requirement_values`, ...), never bare `values`.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_requisitions.services import authorise, draft_commands as cmd, handoff, lifecycle, read


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
def get_requisition_workspace() -> dict[str, Any]:
	return read.get_requisition_workspace()


@frappe.whitelist()
def get_eligible_plan_item_detail(plan_item_id: str) -> dict[str, Any]:
	return read.get_eligible_plan_item_detail(plan_item_id=plan_item_id)


@frappe.whitelist()
def get_requisition_editor(requisition: str) -> dict[str, Any]:
	return read.get_requisition_editor(requisition=requisition)


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
def get_requisition_history(requisition: str) -> dict[str, Any]:
	return read.get_requisition_history(requisition=requisition)


# --------------------------------------------------------------------------
# §10.2 Commands — Draft stage
# --------------------------------------------------------------------------


@frappe.whitelist()
def prepare_it_equipment_requisition(plan_item_id: str, idempotency_key: str) -> dict[str, Any]:
	return cmd.prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_requisition_summary(requisition: str, summary_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.save_requisition_summary(requisition=requisition, values=_parse_json(summary_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_requisition_item(requisition: str, item_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_requisition_item(requisition=requisition, values=_parse_json(item_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_requisition_item(requisition: str, requisition_item_id: str, item_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_requisition_item(requisition=requisition, requisition_item_id=requisition_item_id, values=_parse_json(item_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_requisition_item(requisition: str, requisition_item_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_requisition_item(requisition=requisition, requisition_item_id=requisition_item_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_technical_requirement(requisition: str, technical_requirement_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_technical_requirement(requisition=requisition, values=_parse_json(technical_requirement_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_technical_requirement(requisition: str, technical_requirement_id: str, technical_requirement_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_technical_requirement(requisition=requisition, technical_requirement_id=technical_requirement_id, values=_parse_json(technical_requirement_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_technical_requirement(requisition: str, technical_requirement_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_technical_requirement(requisition=requisition, technical_requirement_id=technical_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def confirm_proposed_requirement(requisition: str, technical_requirement_id: str, expected_record_version, idempotency_key: str, confirmation_values=None) -> dict[str, Any]:
	# `confirmation_values` is one JSON-wrapped `{value, other_value}` object,
	# not two bare top-level kwargs — a bare `value` would arrive over HTTP
	# as an unparsed form string (e.g. "NVMe SSD" is not valid bare JSON),
	# the same transport pitfall every other structured argument in this
	# file avoids by always wrapping in one JSON string.
	parsed = _parse_json(confirmation_values, {}) or {}
	return cmd.confirm_proposed_requirement(requisition=requisition, technical_requirement_id=technical_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key, value=parsed.get("value"), other_value=parsed.get("other_value", ""))


@frappe.whitelist()
def save_warranty_and_support(requisition: str, warranty_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.save_warranty_and_support(requisition=requisition, values=_parse_json(warranty_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


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


@frappe.whitelist()
def validate_requisition(requisition: str) -> dict[str, Any]:
	return cmd.validate_requisition(requisition=requisition)


# --------------------------------------------------------------------------
# §10.2 Commands — Lifecycle
# --------------------------------------------------------------------------


@frappe.whitelist()
def send_for_department_approval(requisition: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_to_department_author(task: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.return_to_department_author(task=task, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_requisition_to_procurement(requisition: str, expected_record_version, idempotency_key: str, task: str | None = None) -> dict[str, Any]:
	return lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=expected_record_version, idempotency_key=idempotency_key, task=task or None)


@frappe.whitelist()
def return_requisition_to_department(task: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.return_requisition_to_department(task=task, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def withdraw_requisition(requisition: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.withdraw_requisition(requisition=requisition, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def request_upstream_plan_correction(requisition: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.request_upstream_plan_correction(requisition=requisition, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def change_lead_organisation_unit(requisition: str, new_lead_org_unit: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.change_lead_organisation_unit(requisition=requisition, new_lead_org_unit=new_lead_org_unit, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


# --------------------------------------------------------------------------
# §10.2 Commands — Authorisation, revocation and the Tender consumption seam
# --------------------------------------------------------------------------


@frappe.whitelist()
def authorise_requisition(requisition: str, task: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return authorise.authorise_requisition(requisition=requisition, task=task, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def revoke_unconsumed_authorisation(requisition: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return authorise.revoke_unconsumed_authorisation(requisition=requisition, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def record_handoff_consumption(handoff_name: str, tender: str, tender_version: str, template_key: str, template_version: str, idempotency_key: str) -> dict[str, Any]:
	# `handoff_name`, deliberately not `handoff`: this module's own `handoff`
	# service module is imported at module scope under that exact name.
	return handoff.record_handoff_consumption(handoff=handoff_name, tender=tender, tender_version=tender_version, template_key=template_key, template_version=template_version, idempotency_key=idempotency_key)
