from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.authorization_service import check_std_permission


def _coerce_by_data_type(value: Any, data_type: str) -> Any:
	if data_type == "Boolean":
		if isinstance(value, bool):
			return value
		if isinstance(value, str):
			if value.lower() in {"true", "1", "yes"}:
				return True
			if value.lower() in {"false", "0", "no"}:
				return False
		raise frappe.ValidationError(_("Parameter expects Boolean value."))
	if data_type == "Int":
		if isinstance(value, bool):
			raise frappe.ValidationError(_("Parameter expects Int value."))
		return int(value)
	if data_type == "Float":
		if isinstance(value, bool):
			raise frappe.ValidationError(_("Parameter expects Float value."))
		return float(value)
	if data_type == "Date":
		if isinstance(value, date) and not isinstance(value, datetime):
			return value.isoformat()
		if isinstance(value, str):
			date.fromisoformat(value)
			return value
		raise frappe.ValidationError(_("Parameter expects ISO date string."))
	if data_type == "Datetime":
		if isinstance(value, datetime):
			return value.isoformat()
		if isinstance(value, str):
			datetime.fromisoformat(value)
			return value
		raise frappe.ValidationError(_("Parameter expects ISO datetime string."))
	if data_type == "JSON":
		if isinstance(value, (dict, list)):
			return value
		if isinstance(value, str):
			return json.loads(value)
		raise frappe.ValidationError(_("Parameter expects JSON object/array."))
	if data_type in {"Select", "String"}:
		return str(value)
	return value


def _parse_allowed_values(raw: Any) -> list[Any]:
	if not raw:
		return []
	if isinstance(raw, str):
		decoded = json.loads(raw)
		return decoded if isinstance(decoded, list) else []
	if isinstance(raw, list):
		return raw
	return []


@frappe.whitelist()
def set_std_parameter_value(instance_code: str, parameter_code: str, value: Any, actor: str) -> dict[str, Any]:
	instance_name = frappe.db.get_value("STD Instance", {"instance_code": instance_code}, "name")
	if not instance_name:
		frappe.throw(_("STD Instance not found."), title=_("Invalid instance"))
	instance = frappe.get_doc("STD Instance", instance_name)
	permission = check_std_permission(
		actor=actor,
		action_code="STD_PARAMETER_SET",
		object_type="STD_INSTANCE",
		object_code=instance_code,
	)
	if not permission["allowed"]:
		frappe.throw(_(permission["message"]), title=_("Permission denied"))

	if instance.instance_status in {"Published Locked", "Superseded", "Cancelled"}:
		frappe.throw(
			_("Instance is immutable in current state. Use addendum path for changes."),
			title=_("Instance locked"),
		)

	parameter = frappe.db.get_value(
		"STD Parameter Definition",
		{"parameter_code": parameter_code},
		["name", "parameter_code", "version_code", "data_type", "allowed_values", "required", "required_condition", "drives_dem", "drives_dcm"],
		as_dict=True,
	)
	if not parameter:
		frappe.throw(_("Parameter definition not found."), title=_("Invalid parameter"))
	if parameter.version_code != instance.template_version_code:
		frappe.throw(_("Parameter does not belong to instance template version."), title=_("Invalid parameter"))

	coerced = _coerce_by_data_type(value, parameter.data_type)
	allowed_values = _parse_allowed_values(parameter.allowed_values)
	if allowed_values and coerced not in allowed_values:
		frappe.throw(_("Value is not in allowed values."), title=_("Invalid value"))
	if int(parameter.required or 0) and coerced in ("", None, []):
		frappe.throw(_("Required parameter cannot be empty."), title=_("Invalid value"))

	record_name = frappe.db.get_value(
		"STD Instance Parameter Value",
		{"instance_code": instance_code, "parameter_code": parameter_code},
		"name",
	)
	payload_json = json.dumps(coerced)
	if record_name:
		rec = frappe.get_doc("STD Instance Parameter Value", record_name)
		rec.value_json = payload_json
		rec.is_stale = 0
		rec.save(ignore_permissions=True)
	else:
		rec = frappe.get_doc(
			{
				"doctype": "STD Instance Parameter Value",
				"instance_parameter_value_code": f"SPV-{frappe.generate_hash(length=10).upper()}",
				"instance_code": instance_code,
				"parameter_code": parameter_code,
				"value_json": payload_json,
				"is_stale": 0,
			}
		).insert(ignore_permissions=True)

	invalidated_outputs: list[str] = []
	if int(parameter.drives_dem or 0) or int(parameter.drives_dcm or 0):
		instance.readiness_status = "Invalidated"
		instance.save(ignore_permissions=True)
		output_rows = frappe.get_all(
			"STD Generated Output",
			filters={"instance_code": instance_code, "status": ("in", ["Current", "Published"])},
			fields=["name", "output_code", "status"],
			limit=200,
		)
		for row in output_rows:
			doc = frappe.get_doc("STD Generated Output", row["name"])
			frappe.flags.std_transition_service_context = True
			try:
				doc.status = "Draft"
				doc.save(ignore_permissions=True)
			finally:
				frappe.flags.std_transition_service_context = False
			invalidated_outputs.append(row["output_code"])

	record_std_audit_event(
		event_type="PARAMETER_VALUE_SET",
		object_type="STD_INSTANCE",
		object_code=instance_code,
		actor=actor,
		previous_state=instance.instance_status,
		new_state=instance.instance_status,
		metadata={
			"parameter_code": parameter_code,
			"invalidation": {"readiness_status": instance.readiness_status, "outputs": invalidated_outputs},
		},
	)
	return {
		"instance_code": instance_code,
		"parameter_code": parameter_code,
		"value_record_code": rec.instance_parameter_value_code,
		"readiness_status": instance.readiness_status,
		"invalidated_outputs": invalidated_outputs,
	}

