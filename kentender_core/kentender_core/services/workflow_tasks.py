"""Transactional and concurrency-safe commands for shared Workflow Tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability, require_capability
from kentender_core.services.authorization_records import new_concurrency_token
from kentender_core.services.workflow_routing import ResolvedRoute, RoutingContext, resolve_routing

TASK_ALREADY_CLAIMED = "TASK_ALREADY_CLAIMED"
TASK_NOT_CURRENT = "TASK_NOT_CURRENT"
TASK_NOT_ASSIGNED = "TASK_NOT_ASSIGNED_TO_USER"
TASK_CONCURRENCY_CONFLICT = "TASK_CONCURRENCY_CONFLICT"
TASK_REASSIGNEE_NOT_ELIGIBLE = "TASK_REASSIGNEE_NOT_ELIGIBLE"

T = TypeVar("T")


class WorkflowTaskError(frappe.ValidationError):
	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


@dataclass(frozen=True)
class TaskSpec:
	routing: RoutingContext
	subject_type: str
	subject_id: str
	idempotency_key: str
	task_iteration: int = 1
	related_record_refs: list[dict[str, str]] = field(default_factory=list)
	resource_scopes: list[dict[str, str]] = field(default_factory=list)
	predecessor_task_id: str = ""
	due_at: Any = None
	task_id: str = ""


def _audit(task, event_type: str, action: str, actor: str, metadata=None) -> None:
	log_audit_event(
		event_type=event_type,
		entity=task.procuring_entity_id,
		document_type="Workflow Task",
		document_name=task.name,
		action=action,
		performed_by=actor,
		metadata={"routing_rule_id": task.routing_rule_id, "routing_rule_version": task.routing_rule_version, **(metadata or {})},
	)


def _insert_task(spec: TaskSpec, route: ResolvedRoute, actor: str):
	task = frappe.get_doc({
		"doctype": "Workflow Task",
		"task_id": spec.task_id or f"TSK-{uuid4().hex.upper()}",
		"task_iteration": spec.task_iteration,
		"module_name": spec.routing.module_name,
		"task_type": spec.routing.task_type,
		"subject_type": spec.subject_type,
		"subject_id": spec.subject_id,
		"related_record_refs": json.dumps(spec.related_record_refs),
		"procuring_entity_id": spec.routing.procuring_entity_id,
		"financial_year_id": spec.routing.financial_year_id,
		"organisation_unit_id": spec.routing.organisation_unit_id,
		"resource_scopes": json.dumps(spec.resource_scopes),
		"routing_rule_id": route.routing_rule_id,
		"routing_rule_version": route.version,
		"assignee_type": route.assignee_type,
		"assigned_user_id": route.assigned_user_id,
		"queue_id": route.queue_id,
		"state": "Open",
		"predecessor_task_id": spec.predecessor_task_id,
		"created_by_actor": actor,
		"created_at": now_datetime(),
		"due_at": spec.due_at,
		"concurrency_token": new_concurrency_token(),
		"idempotency_key": spec.idempotency_key,
	}).insert(ignore_permissions=True)
	_audit(task, "workflow.task.created", "create", actor)
	return task


def create_routed_task(spec: TaskSpec, *, actor: str | None = None):
	actor = actor or frappe.session.user
	existing = frappe.db.get_value("Workflow Task", {"idempotency_key": spec.idempotency_key}, "name")
	if existing:
		return frappe.get_doc("Workflow Task", existing)
	return _insert_task(spec, resolve_routing(spec.routing), actor)


def execute_routed_transition(spec: TaskSpec, transition: Callable[[], T], *, actor: str | None = None) -> tuple[T, Any]:
	"""Resolve before mutation, then execute transition and task insert in the caller's transaction."""
	actor = actor or frappe.session.user
	existing = frappe.db.get_value("Workflow Task", {"idempotency_key": spec.idempotency_key}, "name")
	if existing:
		return None, frappe.get_doc("Workflow Task", existing)
	route = resolve_routing(spec.routing)
	result = transition()
	return result, _insert_task(spec, route, actor)


def _locked_task(task_id: str, expected_token: str):
	rows = frappe.db.sql("select * from `tabWorkflow Task` where name=%s for update", task_id, as_dict=True)
	if not rows or rows[0].state != "Open":
		raise WorkflowTaskError(TASK_NOT_CURRENT, _("This task is no longer current. Return to My work for the latest status."))
	if rows[0].concurrency_token != expected_token:
		raise WorkflowTaskError(TASK_CONCURRENCY_CONFLICT, _("This task changed after you opened it. Reload and try again."))
	return frappe.get_doc("Workflow Task", task_id)


def _task_resource(task, *, prior_actions=None) -> ResourceContext:
	return ResourceContext(
		task.subject_type,
		task.subject_id,
		task.procuring_entity_id,
		task.financial_year_id,
		task.organisation_unit_id,
		prior_actions=prior_actions or [],
	)


def _required_capability(task) -> str:
	return frappe.db.get_value("Workflow Routing Rule", {"routing_rule_id": task.routing_rule_id, "version": task.routing_rule_version}, "required_capability") or task.task_type


def get_authorized_task(task_id: str, *, actor: str, capability: str | None = None):
	"""Return an Open task only after re-evaluating current assignment and scope."""
	task = frappe.get_doc("Workflow Task", task_id)
	if task.state != "Open":
		raise WorkflowTaskError(TASK_NOT_CURRENT, _("This task is no longer current. Return to My work for the latest status."))
	require_capability(
		actor,
		capability or _required_capability(task),
		_task_resource(task),
		task_id=task.name,
	)
	return task


def claim_task(task_id: str, *, user: str, expected_token: str):
	task = _locked_task(task_id, expected_token)
	if task.assignee_type != "Queue":
		raise WorkflowTaskError(TASK_NOT_ASSIGNED, _("You do not have access to this task."))
	if task.claimed_by:
		raise WorkflowTaskError(TASK_ALREADY_CLAIMED, _("This task has already been claimed by another authorised user."))
	require_capability(user, _required_capability(task), _task_resource(task), task_id=task.name)
	task.claimed_by = user
	task.claimed_at = now_datetime()
	task.concurrency_token = new_concurrency_token()
	task.save(ignore_permissions=True)
	_audit(task, "workflow.task.claimed", "claim", user, {"queue_id": task.queue_id})
	return task


def release_task(task_id: str, *, user: str, expected_token: str, reason: str):
	task = _locked_task(task_id, expected_token)
	if task.assignee_type != "Queue" or task.claimed_by != user:
		raise WorkflowTaskError(TASK_NOT_ASSIGNED, _("You do not have access to this task."))
	task.claimed_by = None
	task.claimed_at = None
	task.concurrency_token = new_concurrency_token()
	task.save(ignore_permissions=True)
	_audit(task, "workflow.task.released", "release", user, {"queue_id": task.queue_id, "reason": reason})
	return task


def reassign_task(task_id: str, *, actor: str, new_user: str, expected_token: str, reason: str, prior_actions=None):
	task = _locked_task(task_id, expected_token)
	require_capability(actor, "authorization.task.reassign", _task_resource(task))
	capability = _required_capability(task)
	if not frappe.db.get_value("User", new_user, "enabled") or not evaluate_capability(new_user, capability, _task_resource(task, prior_actions=prior_actions)).allowed:
		raise WorkflowTaskError(TASK_REASSIGNEE_NOT_ELIGIBLE, _("The selected user is not eligible for this task."))
	prior = task.claimed_by or task.assigned_user_id or task.queue_id
	task.assignee_type = "User"
	task.assigned_user_id = new_user
	task.queue_id = None
	task.claimed_by = None
	task.claimed_at = None
	task.concurrency_token = new_concurrency_token()
	task.save(ignore_permissions=True)
	_audit(task, "workflow.task.reassigned", "reassign", actor, {"prior_owner": prior, "new_user": new_user, "reason": reason})
	return task


def transition_task(task_id: str, *, actor: str, capability: str, target_state: str, expected_token: str, prior_actions=None):
	if target_state not in {"Completed", "Returned", "Cancelled", "Superseded", "Stale"}:
		raise WorkflowTaskError(TASK_NOT_CURRENT, _("This task is no longer current. Return to My work for the latest status."))
	task = _locked_task(task_id, expected_token)
	resource = _task_resource(task, prior_actions=prior_actions)
	require_capability(actor, capability, resource, task_id=task.name)
	task.state = target_state
	task.concurrency_token = new_concurrency_token()
	task.save(ignore_permissions=True)
	_audit(task, "workflow.task.transitioned", target_state.lower(), actor)
	return task


def invalidate_task(task_id: str, *, subject_type: str, subject_id: str, actor: str, target_state: str = "Cancelled", reason: str = ""):
	"""Invalidate an originating service's task after that service authorizes cancellation."""
	if target_state not in {"Cancelled", "Superseded", "Stale"}:
		raise WorkflowTaskError(TASK_NOT_CURRENT, _("This task cannot be invalidated to the requested state."))
	task = frappe.get_doc("Workflow Task", task_id)
	if task.subject_type != subject_type or task.subject_id != subject_id:
		raise WorkflowTaskError(TASK_NOT_ASSIGNED, _("The task does not belong to this record."))
	if task.state != "Open":
		return task
	task.state = target_state
	task.concurrency_token = new_concurrency_token()
	task.save(ignore_permissions=True)
	_audit(task, "workflow.task.invalidated", target_state.lower(), actor, {"reason": reason})
	return task
