"""Safe read-only authorization diagnostics and support authorization."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.authorization_administration import ADMIN_ROLES
from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability, resolve_effective_access


def _can_diagnose(actor: str, resource: ResourceContext) -> bool:
	return actor == "Administrator" or bool(ADMIN_ROLES.intersection(frappe.get_roles(actor))) or evaluate_capability(actor, "authorization.diagnostic.view", resource).allowed


def diagnose_access(*, tested_user: str, capability: str, resource: ResourceContext, task_id: str = "", actor: str | None = None, prior_actions=None) -> dict:
	viewer = actor or frappe.session.user
	if not _can_diagnose(viewer, resource):
		frappe.throw(_("You are not permitted to inspect authorization diagnostics."), frappe.PermissionError, title="AUTH_DIAGNOSTIC_PERMISSION_DENIED")
	task = frappe.db.get_value("Workflow Task", task_id, ["task_type", "state", "assignee_type", "assigned_user_id", "queue_id", "claimed_by", "financial_year_id", "routing_rule_id", "routing_rule_version"], as_dict=True) if task_id else None
	access = resolve_effective_access(tested_user, capability)
	scope = [row for row in access if row["procuring_entity_id"] == resource.procuring_entity_id]
	decision = evaluate_capability(tested_user, capability, ResourceContext(**{**resource.__dict__, "prior_actions": prior_actions or resource.prior_actions}), task_id=task_id)
	assignee = (task.claimed_by or task.assigned_user_id or task.queue_id) if task else ""
	task_match = not task or (task.assignee_type == "User" and task.assigned_user_id == tested_user) or (task.assignee_type == "Queue" and task.claimed_by == tested_user)
	checks = [
		{"check": "Capability", "required": capability, "actual": "Active capability assignment" if access else "Not assigned", "passed": bool(access)},
		{"check": "Procuring Entity scope", "required": resource.procuring_entity_id, "actual": "Active operational assignment" if scope else "No active operational assignment", "passed": bool(scope)},
		{"check": "Financial-year context", "required": f"{resource.financial_year_id} from task", "actual": "Available from task" if resource.financial_year_id else "Unavailable", "passed": bool(resource.financial_year_id)},
		{"check": "Current task assignment", "required": "Assigned user or claimed queue task", "actual": f"Assigned to {assignee}" if assignee else "No task supplied", "passed": task_match},
		{"check": "Task state", "required": "Open", "actual": task.state if task else "Not evaluated", "passed": not task or task.state == "Open"},
		{"check": "Separation of duties", "required": "No incompatible prior action", "actual": "No conflict found" if decision.reason_code != "SEPARATION_OF_DUTIES_BLOCKED" else "Conflict found", "passed": decision.reason_code != "SEPARATION_OF_DUTIES_BLOCKED"},
	]
	failed = [row["check"] for row in checks if not row["passed"]]
	return {"allowed": decision.allowed, "status": "Access allowed" if decision.allowed else "Access denied", "tested_user": tested_user, "capability": capability, "resource": resource.__dict__, "task_id": task_id, "task_assignee": assignee, "routing_rule_id": task.routing_rule_id if task else "", "routing_rule_version": task.routing_rule_version if task else 0, "checks": checks, "conclusion": "Access is allowed by the current governed assignment and task policy." if decision.allowed else f"This account cannot open the requested resource because these checks failed: {', '.join(failed)}.", "reason_code": decision.reason_code}


def authorize_support_record_view(*, user: str, resource: ResourceContext, purpose: str) -> None:
	decision = evaluate_capability(user, "support.record.view", resource, requested_profile="support")
	if not decision.allowed:
		frappe.throw(_("You can inspect access configuration, but you do not have support permission to view this record."), frappe.PermissionError, title="SUPPORT_RECORD_VIEW_NOT_ASSIGNED")
	log_audit_event(event_type="authorization.support_record_view", entity=resource.procuring_entity_id, document_type=resource.resource_type, document_name=resource.resource_id, action="support.record.view", performed_by=user, metadata={"purpose": purpose, "profile": "support", "financial_year_id": resource.financial_year_id})
