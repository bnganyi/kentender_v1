"""Deterministic governed routing for shared workflow tasks."""

from __future__ import annotations

from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability
from kentender_core.services.org_scope_access import descendant_org_units

ROUTING_NOT_CONFIGURED = "TASK_ROUTING_RULE_NOT_CONFIGURED"
ASSIGNEE_NOT_AVAILABLE = "TASK_ASSIGNEE_NOT_AVAILABLE"
ROUTING_AMBIGUOUS = "TASK_ROUTING_AMBIGUOUS"


class WorkflowRoutingError(frappe.ValidationError):
	def __init__(self, code: str):
		self.code = code
		messages = {
			ROUTING_NOT_CONFIGURED: _("This work could not be submitted because no active routing rule is configured for the next step."),
			ASSIGNEE_NOT_AVAILABLE: _("This work could not be submitted because the configured assignee is not currently eligible."),
			ROUTING_AMBIGUOUS: _("This work could not be submitted because more than one routing rule has the same priority."),
		}
		super().__init__(messages[code])


@dataclass(frozen=True)
class RoutingContext:
	module_name: str
	task_type: str
	procuring_entity_id: str
	financial_year_id: str
	organisation_unit_id: str = ""
	resource_scope_type: str = ""
	resource_scope_id: str = ""


@dataclass(frozen=True)
class ResolvedRoute:
	routing_rule_id: str
	version: int
	required_capability: str
	assignee_type: str
	assigned_user_id: str = ""
	queue_id: str = ""


def _active(row, at_time) -> bool:
	start = get_datetime(row.effective_from)
	end = get_datetime(row.effective_to) if row.effective_to else None
	return start <= at_time and (not end or at_time < end)


def _scope_matches(row, context: RoutingContext) -> bool:
	if row.organisation_unit_id:
		if not context.organisation_unit_id:
			return False
		units = descendant_org_units(row.organisation_unit_id) if int(row.include_descendants or 0) else {row.organisation_unit_id}
		if context.organisation_unit_id not in units:
			return False
	if row.resource_scope_type:
		return row.resource_scope_type == context.resource_scope_type and row.resource_scope_id == context.resource_scope_id
	return True


def _resource(context: RoutingContext) -> ResourceContext:
	return ResourceContext(
		resource_type=context.module_name,
		resource_id=context.task_type,
		procuring_entity_id=context.procuring_entity_id,
		financial_year_id=context.financial_year_id,
		organisation_unit_id=context.organisation_unit_id,
		resource_scope_type=context.resource_scope_type,
		resource_scope_id=context.resource_scope_id,
	)


def _eligible_members(queue_id: str, capability: str, context: RoutingContext, at_time) -> list[str]:
	queue = frappe.db.get_value("Workflow Queue", queue_id, ["status", "effective_from", "effective_to", "required_capability", "procuring_entity_id"], as_dict=True)
	if not queue or queue.status != "Active" or not _active(queue, at_time):
		return []
	if queue.required_capability != capability or queue.procuring_entity_id != context.procuring_entity_id:
		return []
	members = frappe.get_all("Workflow Queue Membership", filters={"queue_id": queue_id, "status": "Active"}, fields=["user_id", "effective_from", "effective_to"])
	return [row.user_id for row in members if _active(row, at_time) and evaluate_capability(row.user_id, capability, _resource(context), at_time=at_time).allowed]


def _resolve_assignee(row, context: RoutingContext, at_time) -> ResolvedRoute | None:
	if row.assignee_strategy == "Named user":
		enabled = frappe.db.get_value("User", row.assignee_user_id, "enabled")
		if not enabled or not evaluate_capability(row.assignee_user_id, row.required_capability, _resource(context), at_time=at_time).allowed:
			return None
		return ResolvedRoute(row.routing_rule_id, int(row.version), row.required_capability, "User", assigned_user_id=row.assignee_user_id)
	if not _eligible_members(row.queue_id, row.required_capability, context, at_time):
		return None
	return ResolvedRoute(row.routing_rule_id, int(row.version), row.required_capability, "Queue", queue_id=row.queue_id)


def _rules(context: RoutingContext, at_time):
	rows = frappe.get_all(
		"Workflow Routing Rule",
		filters={"module_name": context.module_name, "task_type": context.task_type, "procuring_entity_id": context.procuring_entity_id, "status": "Active"},
		fields=["name", "routing_rule_id", "version", "organisation_unit_id", "include_descendants", "resource_scope_type", "resource_scope_id", "required_capability", "assignee_strategy", "assignee_user_id", "queue_id", "priority", "effective_from", "effective_to", "fallback_rule_id"],
	)
	return [row for row in rows if _active(row, at_time) and _scope_matches(row, context)]


def resolve_routing(context: RoutingContext, *, at_time=None) -> ResolvedRoute:
	"""Resolve exactly one highest-priority route; smaller priority values win."""
	at = get_datetime(at_time) if at_time else now_datetime()
	candidates = _rules(context, at)
	if not candidates:
		raise WorkflowRoutingError(ROUTING_NOT_CONFIGURED)
	best_priority = min(int(row.priority) for row in candidates)
	best = [row for row in candidates if int(row.priority) == best_priority]
	if len(best) != 1:
		raise WorkflowRoutingError(ROUTING_AMBIGUOUS)
	row = best[0]
	resolved = _resolve_assignee(row, context, at)
	if resolved:
		return resolved
	if row.fallback_rule_id:
		fallbacks = [candidate for candidate in candidates if candidate.routing_rule_id == row.fallback_rule_id]
		if len(fallbacks) > 1:
			raise WorkflowRoutingError(ROUTING_AMBIGUOUS)
		if fallbacks:
			resolved = _resolve_assignee(fallbacks[0], context, at)
			if resolved:
				return resolved
	raise WorkflowRoutingError(ASSIGNEE_NOT_AVAILABLE)
