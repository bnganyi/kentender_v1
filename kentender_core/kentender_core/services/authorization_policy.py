"""The retired AUTH-G04 authorization decision service (AUD-XC-026).

`evaluate_capability` is a stable denial; only the read helpers the migration inventory and the read-only
access pages use remain. Business authority is `kentender_core.services.authorization`."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from kentender_core.services.audit_event_service import log_audit_event

ALLOW = "ALLOW"
DENY_CAPABILITY = "CAPABILITY_NOT_ASSIGNED"
DENY_SCOPE = "RESOURCE_OUTSIDE_OPERATIONAL_SCOPE"
DENY_TASK = "TASK_NOT_ASSIGNED_TO_USER"
DENY_TASK_STATE = "TASK_NOT_CURRENT"
DENY_SOD = "SEPARATION_OF_DUTIES_BLOCKED"
DENY_RETIRED = "LEGACY_AUTHORIZATION_RETIRED"


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


def evaluate_capability(
	user: str,
	capability: str,
	resource: ResourceContext | dict[str, Any],
	*,
	task_id: str = "",
	requested_profile: str = "owner",
	at_time=None,
) -> AuthorizationDecision:
	"""The retired AUTH-G04 engine authorises nothing (AUD-XC-026).

	AUTH-ADR-001 §11.5: no production code may authorise from an Operational
	Scope Assignment, Capability Profile or Workflow Task. Every evaluation is
	a stable denial; business authority comes only from `User Responsibility
	Assignment` through `kentender_core.services.authorization`. The record
	readers above stay, for the migration inventory and the read-only access
	pages.
	"""
	return AuthorizationDecision(False, capability, "none", DENY_RETIRED)


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
