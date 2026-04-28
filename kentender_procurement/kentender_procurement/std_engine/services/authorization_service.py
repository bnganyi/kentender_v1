from __future__ import annotations

import frappe


ACTION_POLICY = {
	"STD_VERSION_ACTIVATE": {"risk_level": "High", "requires_confirmation": True, "roles": ("Administrator", "System Manager")},
	"STD_VERSION_EDIT_CONTENT": {"risk_level": "High", "requires_confirmation": False, "roles": ("Administrator", "System Manager")},
	"STD_INSTANCE_PUBLISH_LOCK": {"risk_level": "High", "requires_confirmation": True, "roles": ("Administrator", "System Manager")},
	"STD_INSTANCE_EDIT_CONTENT": {"risk_level": "High", "requires_confirmation": False, "roles": ("Administrator", "System Manager")},
	"STD_OUTPUT_EDIT_CONTENT": {"risk_level": "High", "requires_confirmation": False, "roles": ("Administrator", "System Manager")},
	"STD_AUDIT_EDIT": {"risk_level": "High", "requires_confirmation": False, "roles": ("Administrator", "System Manager")},
	"STD_INSTANCE_CREATE_FROM_TEMPLATE": {"risk_level": "Medium", "requires_confirmation": False, "roles": ("Administrator", "System Manager", "Procurement Planner")},
}

OBJECTS = {
	"TEMPLATE_FAMILY": ("STD Template Family", "template_code"),
	"TEMPLATE_VERSION": ("STD Template Version", "version_code"),
	"APPLICABILITY_PROFILE": ("STD Applicability Profile", "profile_code"),
	"STD_INSTANCE": ("STD Instance", "instance_code"),
	"GENERATED_OUTPUT": ("STD Generated Output", "output_code"),
	"GENERATION_JOB": ("STD Generation Job", "generation_job_code"),
	"READINESS_RUN": ("STD Readiness Run", "readiness_run_code"),
	"ADDENDUM_IMPACT": ("STD Addendum Impact Analysis", "impact_analysis_code"),
	"AUDIT_EVENT": ("STD Audit Event", "audit_event_code"),
}


@frappe.whitelist()
def check_std_permission(
	actor: str,
	action_code: str,
	object_type: str,
	object_code: str | None = None,
	context: dict | None = None,
) -> dict:
	context = context or {}
	policy = ACTION_POLICY.get(action_code, {"risk_level": "High", "requires_confirmation": False, "roles": ("Administrator", "System Manager")})
	result = {
		"allowed": True,
		"action_code": action_code,
		"denial_code": None,
		"message": "Allowed",
		"requires_reason": bool(context.get("requires_reason", False)),
		"requires_confirmation": bool(policy.get("requires_confirmation", False)),
		"risk_level": policy["risk_level"],
	}

	roles = set(frappe.get_roles(actor))
	if not any(r in roles for r in policy["roles"]):
		return _deny(result, "STD_AUTH_ROLE_DENIED", f"Actor {actor} is not authorized for action {action_code}.")

	doc = None
	if object_code and object_type:
		key = object_type.strip().upper()
		if key not in OBJECTS:
			return _deny(result, "STD_AUTH_OBJECT_UNKNOWN", f"Unsupported object_type: {object_type}")
		doctype, code_field = OBJECTS[key]
		name = frappe.db.get_value(doctype, {code_field: object_code}, "name")
		if not name:
			return _deny(result, "STD_AUTH_OBJECT_NOT_FOUND", f"{doctype} with code '{object_code}' not found.")
		doc = frappe.get_doc(doctype, name)

	if doc and actor == doc.owner and context.get("sod_no_owner"):
		return _deny(result, "STD_AUTH_SOD_BLOCKED", "Action denied by separation-of-duties policy.")

	if action_code == "STD_VERSION_EDIT_CONTENT" and doc:
		if doc.get("version_status") == "Active" and int(doc.get("immutable_after_activation") or 0):
			return _deny(result, "STD_AUTH_ACTIVE_IMMUTABLE", "Active immutable template version cannot be edited directly.")

	if action_code == "STD_INSTANCE_EDIT_CONTENT" and doc:
		if doc.get("instance_status") == "Published Locked":
			return _deny(result, "STD_AUTH_INSTANCE_IMMUTABLE", "Published instance is immutable.")

	if action_code == "STD_OUTPUT_EDIT_CONTENT" and doc:
		if doc.get("status") in {"Published", "Superseded", "Archived"}:
			return _deny(result, "STD_AUTH_OUTPUT_IMMUTABLE", "Generated output is immutable in current state.")

	if action_code == "STD_AUDIT_EDIT":
		return _deny(result, "STD_AUTH_AUDIT_IMMUTABLE", "Audit records are append-only.")

	if action_code == "STD_INSTANCE_CREATE_FROM_TEMPLATE":
		version_code = context.get("template_version_code")
		profile_code = context.get("profile_code")
		if version_code:
			version_status = frappe.db.get_value("STD Template Version", {"version_code": version_code}, "version_status")
			if version_status != "Active":
				return _deny(result, "STD_AUTH_TEMPLATE_INACTIVE", "Template version must be Active.")
		if profile_code:
			profile_status = frappe.db.get_value("STD Applicability Profile", {"profile_code": profile_code}, "profile_status")
			if profile_status != "Active":
				return _deny(result, "STD_AUTH_PROFILE_INACTIVE", "Applicability profile must be Active.")

	if action_code == "STD_INSTANCE_PUBLISH_LOCK":
		if context.get("requires_addendum") and not context.get("addendum_completed"):
			return _deny(result, "STD_AUTH_ADDENDUM_REQUIRED", "Cannot proceed until addendum impact requirements are satisfied.")
		if context.get("requires_generated_models") and not context.get("generated_models_ready"):
			return _deny(result, "STD_AUTH_MODEL_GENERATION_REQUIRED", "Cannot proceed until required generated models exist.")

	if context.get("source_of_truth_owner") and context.get("source_of_truth_owner") != actor:
		return _deny(result, "STD_AUTH_SOURCE_OF_TRUTH_VIOLATION", "Action denied: source-of-truth owner mismatch.")

	return result


def _deny(result: dict, denial_code: str, message: str) -> dict:
	result["allowed"] = False
	result["denial_code"] = denial_code
	result["message"] = message
	result["requires_confirmation"] = False
	return result

