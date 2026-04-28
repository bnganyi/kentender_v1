from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import frappe
from .authorization_service import check_std_permission


class STDTransitionDenied(frappe.ValidationError):
	def __init__(self, denial_code: str, message: str):
		super().__init__(message)
		self.denial_code = denial_code
		self.message = message


@dataclass(frozen=True)
class TransitionSpec:
	from_status: tuple[str, ...]
	to_status: str
	allowed_roles: tuple[str, ...]
	risk_level: str = "Medium"
	requires_reason: bool = False
	requires_confirmation: bool = False
	sod_no_owner: bool = False
	precondition: Callable[[object, dict | None], None] | None = None


OBJECTS = {
	"TEMPLATE_FAMILY": ("STD Template Family", "template_code", "family_status"),
	"TEMPLATE_VERSION": ("STD Template Version", "version_code", "version_status"),
	"APPLICABILITY_PROFILE": ("STD Applicability Profile", "profile_code", "profile_status"),
	"STD_INSTANCE": ("STD Instance", "instance_code", "instance_status"),
	"GENERATED_OUTPUT": ("STD Generated Output", "output_code", "status"),
	"GENERATION_JOB": ("STD Generation Job", "generation_job_code", "status"),
	"READINESS_RUN": ("STD Readiness Run", "readiness_run_code", "status"),
	"ADDENDUM_IMPACT": ("STD Addendum Impact Analysis", "impact_analysis_code", "status"),
}


def _require_version_reviews(doc, _context):
	if doc.legal_review_status != "Approved" or doc.policy_review_status != "Approved":
		raise STDTransitionDenied(
			"STD_PRECONDITION_REVIEW_REQUIRED",
			"Cannot activate because legal/policy review has not been cleared.",
		)
	if doc.structure_validation_status != "Pass":
		raise STDTransitionDenied(
			"STD_PRECONDITION_STRUCTURE_FAIL",
			"Cannot activate because structure validation has not passed.",
		)


def _require_profile_version_active(doc, _context):
	version_status = frappe.db.get_value("STD Template Version", {"version_code": doc.version_code}, "version_status")
	if version_status != "Active":
		raise STDTransitionDenied(
			"STD_PRECONDITION_VERSION_INACTIVE",
			"Cannot activate profile because linked template version is not Active.",
		)


def _require_instance_ready(doc, _context):
	if doc.readiness_status != "Ready":
		raise STDTransitionDenied(
			"STD_PRECONDITION_NOT_READY",
			"Cannot publish instance because readiness_status is not Ready.",
		)


TRANSITIONS: dict[str, TransitionSpec] = {
	"STD_FAMILY_SUBMIT_REVIEW": TransitionSpec(("Draft",), "Under Review", ("Administrator", "System Manager")),
	"STD_FAMILY_APPROVE": TransitionSpec(("Under Review",), "Approved", ("Administrator", "System Manager"), sod_no_owner=True),
	"STD_FAMILY_ACTIVATE": TransitionSpec(("Approved", "Suspended"), "Active", ("Administrator", "System Manager"), risk_level="High", requires_confirmation=True),
	"STD_FAMILY_SUSPEND": TransitionSpec(("Active",), "Suspended", ("Administrator", "System Manager"), risk_level="High", requires_reason=True),
	"STD_FAMILY_ARCHIVE": TransitionSpec(("Approved", "Suspended"), "Archived", ("Administrator", "System Manager"), risk_level="High", requires_reason=True),
	"STD_VERSION_APPROVE": TransitionSpec(("Validation Passed", "Legal Review Pending"), "Approved", ("Administrator", "System Manager"), sod_no_owner=True),
	"STD_VERSION_ACTIVATE": TransitionSpec(("Approved",), "Active", ("Administrator", "System Manager"), risk_level="High", requires_confirmation=True, precondition=_require_version_reviews),
	"STD_VERSION_SUSPEND": TransitionSpec(("Active",), "Suspended", ("Administrator", "System Manager"), risk_level="High", requires_reason=True),
	"STD_VERSION_RETIRE": TransitionSpec(("Suspended", "Superseded"), "Retired", ("Administrator", "System Manager"), risk_level="High", requires_reason=True),
	"STD_PROFILE_APPROVE": TransitionSpec(("Validation Blocked", "Draft"), "Approved", ("Administrator", "System Manager")),
	"STD_PROFILE_ACTIVATE": TransitionSpec(("Approved",), "Active", ("Administrator", "System Manager"), risk_level="High", precondition=_require_profile_version_active),
	"STD_PROFILE_SUSPEND": TransitionSpec(("Active",), "Suspended", ("Administrator", "System Manager"), risk_level="High", requires_reason=True),
	"STD_INSTANCE_PROGRESS": TransitionSpec(("Draft",), "In Progress", ("Administrator", "System Manager")),
	"STD_INSTANCE_READY_VALIDATE": TransitionSpec(("In Progress",), "Ready for Validation", ("Administrator", "System Manager")),
	"STD_INSTANCE_SET_READY": TransitionSpec(("Ready for Validation",), "Ready", ("Administrator", "System Manager")),
	"STD_INSTANCE_PUBLISH_LOCK": TransitionSpec(("Ready", "Locked Pre-Publication"), "Published Locked", ("Administrator", "System Manager"), risk_level="High", requires_confirmation=True, precondition=_require_instance_ready),
	"STD_OUTPUT_CURRENT": TransitionSpec(("Draft",), "Current", ("Administrator", "System Manager")),
	"STD_OUTPUT_PUBLISH": TransitionSpec(("Current",), "Published", ("Administrator", "System Manager"), risk_level="High", requires_confirmation=True),
	"STD_JOB_START": TransitionSpec(("Pending",), "Running", ("Administrator", "System Manager")),
	"STD_JOB_COMPLETE": TransitionSpec(("Running",), "Completed", ("Administrator", "System Manager")),
	"STD_READINESS_MARK_READY": TransitionSpec(("Not Run", "Incomplete", "Warning"), "Ready", ("Administrator", "System Manager")),
	"STD_ADDENDUM_ANALYZE": TransitionSpec(("Draft",), "Analysis Pending", ("Administrator", "System Manager")),
	"STD_ADDENDUM_COMPLETE_ANALYSIS": TransitionSpec(("Analysis Pending",), "Analysis Complete", ("Administrator", "System Manager")),
}


@frappe.whitelist()
def transition_std_object(
	object_type: str,
	object_code: str,
	action_code: str,
	actor: str,
	reason: str | None = None,
	context: dict | None = None,
) -> dict:
	object_type = object_type.strip().upper()
	if object_type not in OBJECTS:
		return _deny(action_code, "STD_TRANSITION_OBJECT_UNKNOWN", f"Unsupported object_type: {object_type}")
	if action_code not in TRANSITIONS:
		return _deny(action_code, "STD_TRANSITION_ACTION_UNKNOWN", f"Unsupported action_code: {action_code}")

	doctype, code_field, status_field = OBJECTS[object_type]
	spec = TRANSITIONS[action_code]
	docname = frappe.db.get_value(doctype, {code_field: object_code}, "name")
	if not docname:
		return _deny(action_code, "STD_TRANSITION_OBJECT_NOT_FOUND", f"{doctype} with code '{object_code}' not found.")
	doc = frappe.get_doc(doctype, docname)
	current_status = doc.get(status_field)

	try:
		_validate_transition(doc, actor, current_status, action_code, spec, reason, context)
	except STDTransitionDenied as exc:
		_emit_audit_event("STD_TRANSITION_DENIED", object_type, object_code, actor, action_code, exc.denial_code, exc.message)
		return _deny(action_code, exc.denial_code, exc.message, spec)

	frappe.flags.std_transition_service_context = True
	try:
		doc.set(status_field, spec.to_status)
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.std_transition_service_context = False

	_emit_audit_event("STD_TRANSITION_SUCCESS", object_type, object_code, actor, action_code, None, f"{current_status} -> {spec.to_status}")
	return {
		"allowed": True,
		"action_code": action_code,
		"denial_code": None,
		"message": "Allowed",
		"requires_reason": spec.requires_reason,
		"requires_confirmation": spec.requires_confirmation,
		"risk_level": spec.risk_level,
		"object_type": object_type,
		"object_code": object_code,
		"previous_state": current_status,
		"new_state": spec.to_status,
		"allowed_next_actions": _next_actions(spec.to_status),
	}


def _validate_transition(doc, actor: str, current_status: str, action_code: str, spec: TransitionSpec, reason, context):
	perm = check_std_permission(
		actor=actor,
		action_code=action_code,
		object_type=_object_type_for_doctype(doc.doctype),
		object_code=_object_code_for_doc(doc, doc.doctype),
		context={**(context or {}), "sod_no_owner": spec.sod_no_owner, "requires_reason": spec.requires_reason},
	)
	if not perm["allowed"]:
		code = "STD_SOD_SAME_ACTOR" if perm["denial_code"] == "STD_AUTH_SOD_BLOCKED" else perm["denial_code"]
		raise STDTransitionDenied(code, perm["message"])
	if current_status not in spec.from_status:
		raise STDTransitionDenied(
			"STD_TRANSITION_INVALID_STATE",
			f"Action {action_code} is not allowed from state {current_status}.",
		)
	roles = set(frappe.get_roles(actor))
	if not any(role in roles for role in spec.allowed_roles):
		raise STDTransitionDenied("STD_AUTH_ROLE_DENIED", f"Actor {actor} is not authorized for action {action_code}.")
	if spec.sod_no_owner and actor == doc.owner:
		raise STDTransitionDenied("STD_SOD_SAME_ACTOR", "Action denied by separation-of-duties policy.")
	if spec.requires_reason and not (reason and reason.strip()):
		raise STDTransitionDenied("STD_REASON_REQUIRED", f"Action {action_code} requires reason.")
	if spec.precondition:
		spec.precondition(doc, context or {})


def _object_type_for_doctype(doctype: str) -> str:
	for object_type, (dt, _, _) in OBJECTS.items():
		if dt == doctype:
			return object_type
	return doctype


def _object_code_for_doc(doc, doctype: str) -> str:
	for _, (dt, code_field, _) in OBJECTS.items():
		if dt == doctype and code_field in doc.as_dict():
			return doc.get(code_field)
	return doc.name


def _deny(action_code: str, code: str, message: str, spec: TransitionSpec | None = None) -> dict:
	return {
		"allowed": False,
		"action_code": action_code,
		"denial_code": code,
		"message": message,
		"requires_reason": bool(spec.requires_reason) if spec else False,
		"requires_confirmation": bool(spec.requires_confirmation) if spec else False,
		"risk_level": spec.risk_level if spec else "High",
	}


def _next_actions(new_state: str) -> list[str]:
	return [action for action, spec in TRANSITIONS.items() if new_state in spec.from_status]


def _emit_audit_event(
	event_type: str,
	object_type: str,
	object_code: str,
	actor: str,
	action_code: str,
	denial_code: str | None,
	message: str,
) -> None:
	if not frappe.db.exists("DocType", "STD Audit Event"):
		return
	frappe.get_doc(
		{
			"doctype": "STD Audit Event",
			"audit_event_code": f"AUD-{frappe.generate_hash(length=12).upper()}",
			"event_type": event_type,
			"object_type": object_type,
			"object_code": object_code,
			"timestamp": datetime.utcnow(),
		}
	).insert(ignore_permissions=True)
	frappe.logger("std_engine_audit").info(
		{
			"event_type": event_type,
			"object_type": object_type,
			"object_code": object_code,
			"actor": actor,
			"action_code": action_code,
			"denial_code": denial_code,
			"message": message,
		}
	)

