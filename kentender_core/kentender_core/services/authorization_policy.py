"""Shared deny-by-default authorization decision service for KenTender."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.org_scope_access import descendant_org_units

ALLOW = "ALLOW"
DENY_CAPABILITY = "CAPABILITY_NOT_ASSIGNED"
DENY_SCOPE = "RESOURCE_OUTSIDE_OPERATIONAL_SCOPE"
DENY_TASK = "TASK_NOT_ASSIGNED_TO_USER"
DENY_TASK_STATE = "TASK_NOT_CURRENT"
DENY_SOD = "SEPARATION_OF_DUTIES_BLOCKED"


@dataclass(frozen=True)
class ResourceContext:
	resource_type: str
	resource_id: str
	procuring_entity_id: str
	financial_year_id: str = ""
	organisation_unit_id: str = ""
	resource_scope_type: str = ""
	resource_scope_id: str = ""
	state: str = ""
	relationships: dict[str, str] = field(default_factory=dict)
	prior_actions: list[dict[str, str]] = field(default_factory=list)
	pe_fy_context_id: str = ""


@dataclass(frozen=True)
class AuthorizationDecision:
	allowed: bool
	capability: str
	profile: str
	reason_code: str
	assignment_ids: tuple[str, ...] = ()
	delegation_ids: tuple[str, ...] = ()
	task_id: str = ""
	commands: tuple[str, ...] = ()

	def as_dict(self) -> dict[str, Any]:
		return asdict(self)


def _json(value, default):
	if value in (None, ""):
		return default
	if isinstance(value, (list, dict)):
		return value
	try:
		return json.loads(value)
	except (TypeError, ValueError):
		return default


def _active_filter(at_time) -> list[list[Any]]:
	return [
		["effective_from", "<=", at_time],
		["effective_to", "is", "not set"],
	]


def _time_active(row, at_time) -> bool:
	start = get_datetime(row.get("effective_from")) if row.get("effective_from") else None
	end = get_datetime(row.get("effective_to")) if row.get("effective_to") else None
	return bool((not start or start <= at_time) and (not end or at_time < end))


def _active_assignments(user: str, at_time) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Operational Scope Assignment",
		filters={"user_id": user, "status": "Active"},
		fields=["assignment_id", "capability_profile_id", "procuring_entity_id", "organisation_unit_id", "include_descendants", "resource_scope_type", "resource_scope_id", "effective_from", "effective_to"],
	)
	return [row for row in rows if _time_active(row, at_time)]


def _profile_capabilities(profile_id: str, at_time) -> set[str]:
	row = frappe.db.get_value("Capability Profile", profile_id, ["capabilities", "status", "effective_from", "effective_to"], as_dict=True)
	if not row or row.status != "Active" or not _time_active(row, at_time):
		return set()
	return {str(value).strip() for value in _json(row.capabilities, []) if str(value).strip()}


def _scope_matches(row, resource: ResourceContext) -> bool:
	if row.procuring_entity_id != resource.procuring_entity_id:
		return False
	assigned_ou = row.organisation_unit_id or ""
	if assigned_ou:
		if not resource.organisation_unit_id:
			return False
		units = descendant_org_units(assigned_ou) if int(row.include_descendants or 0) else {assigned_ou}
		if resource.organisation_unit_id not in units:
			return False
	if row.resource_scope_type:
		return bool(row.resource_scope_type == resource.resource_scope_type and row.resource_scope_id == resource.resource_scope_id)
	return True


def resolve_effective_access(user: str, capability: str | None = None, at_time=None) -> list[dict[str, Any]]:
	"""Return active governed assignments, optionally filtered by capability."""
	at = get_datetime(at_time) if at_time else now_datetime()
	out = []
	for row in _active_assignments(user, at):
		capabilities = _profile_capabilities(row.capability_profile_id, at)
		if capability and capability not in capabilities:
			continue
		entry = dict(row)
		entry["capabilities"] = sorted(capabilities)
		out.append(entry)
	return out


def _active_delegations(user: str, capability: str, resource: ResourceContext, at_time) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Authorization Delegation",
		filters={"delegate_user_id": user, "status": "Active", "procuring_entity_id": resource.procuring_entity_id},
		fields=["delegation_id", "delegator_user_id", "capability_profile_id", "organisation_unit_id", "effective_from", "effective_to"],
	)
	out = []
	for row in rows:
		if not _time_active(row, at_time) or capability not in _profile_capabilities(row.capability_profile_id, at_time):
			continue
		if row.organisation_unit_id and row.organisation_unit_id != resource.organisation_unit_id:
			continue
		out.append(row)
	return out


def _task_allows(user: str, task_id: str, delegations: list[dict[str, Any]], at_time) -> tuple[bool, str]:
	task = frappe.db.get_value("Workflow Task", task_id, ["task_id", "state", "assignee_type", "assigned_user_id", "queue_id", "claimed_by"], as_dict=True)
	if not task or task.state != "Open":
		return False, DENY_TASK_STATE
	delegators = {row.delegator_user_id for row in delegations}
	if task.assignee_type == "User":
		return (task.assigned_user_id == user or task.assigned_user_id in delegators, DENY_TASK)
	if task.claimed_by:
		return (task.claimed_by == user or task.claimed_by in delegators, DENY_TASK)
	memberships = frappe.get_all("Workflow Queue Membership", filters={"queue_id": task.queue_id, "user_id": user, "status": "Active"}, fields=["effective_from", "effective_to"])
	return (any(_time_active(row, at_time) for row in memberships), DENY_TASK)


def _sod_blocked(user: str, capability: str, resource: ResourceContext, at_time) -> bool:
	prior = {row.get("capability") for row in resource.prior_actions if row.get("user") == user}
	if not prior:
		return False
	rules = frappe.get_all("Separation of Duties Rule", filters={"status": "Active"}, fields=["first_capability", "second_capability", "effective_from", "effective_to"])
	for rule in rules:
		if not _time_active(rule, at_time):
			continue
		if capability == rule.first_capability and rule.second_capability in prior:
			return True
		if capability == rule.second_capability and rule.first_capability in prior:
			return True
	return False


def evaluate_capability(
	user: str,
	capability: str,
	resource: ResourceContext | dict[str, Any],
	*,
	task_id: str = "",
	requested_profile: str = "owner",
	at_time=None,
) -> AuthorizationDecision:
	"""Evaluate capability, scope, assignment, task state and SoD without side effects."""
	at = get_datetime(at_time) if at_time else now_datetime()
	ctx = resource if isinstance(resource, ResourceContext) else ResourceContext(**resource)
	if not user or user == "Guest":
		return AuthorizationDecision(False, capability, "none", DENY_CAPABILITY)
	assignments = resolve_effective_access(user, capability, at)
	matching = [row for row in assignments if _scope_matches(frappe._dict(row), ctx)]
	delegations = _active_delegations(user, capability, ctx, at)
	if not matching and not delegations:
		code = DENY_SCOPE if assignments else DENY_CAPABILITY
		return AuthorizationDecision(False, capability, "none", code)
	if task_id:
		allowed, reason = _task_allows(user, task_id, delegations, at)
		if not allowed:
			return AuthorizationDecision(False, capability, "none", reason, tuple(row["assignment_id"] for row in matching), tuple(row["delegation_id"] for row in delegations), task_id)
	if _sod_blocked(user, capability, ctx, at):
		return AuthorizationDecision(False, capability, "none", DENY_SOD, tuple(row["assignment_id"] for row in matching), tuple(row["delegation_id"] for row in delegations), task_id)
	return AuthorizationDecision(True, capability, requested_profile, ALLOW, tuple(row["assignment_id"] for row in matching), tuple(row["delegation_id"] for row in delegations), task_id, (capability,))


def require_capability(*args, correlation_id: str = "", **kwargs) -> AuthorizationDecision:
	decision = evaluate_capability(*args, **kwargs)
	if decision.allowed:
		return decision
	resource = args[2] if len(args) > 2 else kwargs.get("resource")
	ctx = resource if isinstance(resource, ResourceContext) else ResourceContext(**resource)
	log_audit_event(
		event_type="authorization.denied",
		entity=ctx.procuring_entity_id,
		document_type=ctx.resource_type,
		document_name=ctx.resource_id,
		action=decision.capability,
		performed_by=args[0] if args else kwargs.get("user"),
		metadata={"reason_code": decision.reason_code, "correlation_id": correlation_id, "task_id": decision.task_id},
	)
	messages = {
		DENY_TASK: _("You do not have access to this task."),
		DENY_TASK_STATE: _("This task is no longer current. Return to My work for the latest status."),
		DENY_SOD: _("You cannot perform this decision because you completed an incompatible earlier action."),
	}
	frappe.throw(messages.get(decision.reason_code, _("Not permitted for this action.")), frappe.PermissionError, title=decision.reason_code)
	return decision


def get_authorized_record_projection(user: str, resource: ResourceContext | dict[str, Any], capability: str, *, requested_profile: str = "owner") -> dict[str, Any]:
	decision = evaluate_capability(user, capability, resource, requested_profile=requested_profile)
	return {"allowed": decision.allowed, "profile": decision.profile, "reason_code": decision.reason_code, "available_actions": list(decision.commands)}


def get_available_actions(user: str, resource: ResourceContext | dict[str, Any], capabilities: list[str], *, task_id: str = "") -> list[dict[str, str]]:
	return [
		{"code": capability, "label": capability, "task_id": task_id}
		for capability in capabilities
		if evaluate_capability(user, capability, resource, task_id=task_id).allowed
	]
