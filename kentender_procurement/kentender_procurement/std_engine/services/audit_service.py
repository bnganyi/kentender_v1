from __future__ import annotations

from datetime import datetime
import json
from typing import Any

import frappe


REQUIRED_EVENT_TYPES = {
	"SOURCE_DOCUMENT_REGISTERED",
	"TEMPLATE_FAMILY_CREATED",
	"TEMPLATE_VERSION_CREATED",
	"TEMPLATE_VERSION_VALIDATED",
	"TEMPLATE_VERSION_LEGAL_REVIEW_CLEARED",
	"TEMPLATE_VERSION_POLICY_REVIEW_CLEARED",
	"TEMPLATE_VERSION_APPROVED",
	"TEMPLATE_VERSION_ACTIVATED",
	"PROFILE_ACTIVATED",
	"STD_INSTANCE_CREATED",
	"PARAMETER_VALUE_SET",
	"WORKS_REQUIREMENT_UPDATED",
	"BOQ_UPDATED",
	"SECTION_ATTACHMENT_ADDED",
	"GENERATION_JOB_STARTED",
	"GENERATION_JOB_COMPLETED",
	"GENERATION_JOB_FAILED",
	"OUTPUT_GENERATED",
	"READINESS_RUN_CREATED",
	"ADDENDUM_IMPACT_ANALYZED",
	"OUTPUT_REGENERATED",
	"OUTPUT_SUPERSEDED",
	"LOCKED_EDIT_DENIED",
	"PERMISSION_DENIED",
	"EVIDENCE_EXPORTED",
	"SAFETY_CHECK_PROBE",
	"SAFETY_CHECK_RUN",
	"STD_TRANSITION_SUCCESS",
	"STD_TRANSITION_DENIED",
}

AUDIT_READ_ROLES = frozenset({"System Manager", "Administrator", "Auditor"})


@frappe.whitelist()
def record_std_audit_event(
	event_type: str,
	object_type: str,
	object_code: str,
	actor: str | None = None,
	previous_state: str | None = None,
	new_state: str | None = None,
	reason: str | None = None,
	denial_code: str | None = None,
	metadata: dict | None = None,
) -> dict[str, Any]:
	if event_type not in REQUIRED_EVENT_TYPES:
		frappe.throw(f"Unsupported audit event type: {event_type}")

	actor = actor or frappe.session.user
	roles = frappe.get_roles(actor)
	doc = frappe.get_doc(
		{
			"doctype": "STD Audit Event",
			"audit_event_code": f"AUD-{frappe.generate_hash(length=12).upper()}",
			"event_type": event_type,
			"object_type": object_type,
			"object_code": object_code,
			"actor": actor,
			"actor_roles": json.dumps(roles),
			"previous_state": previous_state,
			"new_state": new_state,
			"reason": reason,
			"denial_code": denial_code,
			"metadata": json.dumps(metadata or {}),
			"timestamp": datetime.utcnow(),
		}
	).insert(ignore_permissions=True)
	return {"audit_event_code": doc.audit_event_code, "event_type": event_type}


@frappe.whitelist()
def get_std_audit_events(
	object_type: str | None = None,
	object_code: str | None = None,
	limit: int = 50,
) -> list[dict[str, Any]]:
	user_roles = set(frappe.get_roles(frappe.session.user))
	if not (user_roles & AUDIT_READ_ROLES):
		frappe.throw("Not permitted to view STD audit events.", frappe.PermissionError)

	filters: dict[str, Any] = {}
	if object_type:
		filters["object_type"] = object_type
	if object_code:
		filters["object_code"] = object_code
	events = frappe.get_all(
		"STD Audit Event",
		filters=filters,
		fields=[
			"audit_event_code",
			"event_type",
			"object_type",
			"object_code",
			"actor",
			"actor_roles",
			"previous_state",
			"new_state",
			"reason",
			"denial_code",
			"metadata",
			"timestamp",
		],
		order_by="timestamp desc",
		limit=max(1, min(int(limit), 500)),
	)
	return events

