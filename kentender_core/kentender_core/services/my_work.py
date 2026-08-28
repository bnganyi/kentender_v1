from __future__ import annotations

from collections import defaultdict
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, cstr, get_datetime, now_datetime

from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability
from kentender_core.services.workflow_tasks import claim_task

NO_ACTIVE_OPERATIONAL_ASSIGNMENT = "NO_ACTIVE_OPERATIONAL_ASSIGNMENT"

_PRESENTATION = {
	"plan.finance.confirm": ("Finance confirmation", "Confirm funding", "procurement-plan-item-editor"),
	"plan.review": ("Planning review", "Review Plan", "procurement-plan-review"),
	"plan.approve": ("Planning approval", "Approve Plan", "procurement-plan-review"),
	"budget.review": ("Budget review", "Review Budget", "budget-review"),
	"budget.approve": ("Budget approval", "Approve Budget", "budget-review"),
}


def _currently_active(rows: list[Any]) -> list[Any]:
	at = now_datetime()
	return [
		row for row in rows
		if row.status == "Active"
		and get_datetime(row.effective_from) <= at
		and (not row.effective_to or get_datetime(row.effective_to) >= at)
	]


def _assignments(user: str) -> list[Any]:
	return _currently_active(frappe.get_all(
		"Operational Scope Assignment",
		filters={"user_id": user, "status": "Active"},
		fields=["name", "assignment_id", "procuring_entity_id", "organisation_unit_id",
			"include_descendants", "resource_scope_type", "resource_scope_id",
			"effective_from", "effective_to", "status"],
		order_by="procuring_entity_id asc, organisation_unit_id asc",
	))


def _queue_ids(user: str) -> set[str]:
	rows = frappe.get_all(
		"Workflow Queue Membership",
		filters={"user_id": user, "status": "Active"},
		fields=["queue_id", "effective_from", "effective_to", "status"],
	)
	return {row.queue_id for row in _currently_active(rows) if row.queue_id}


def _resource(task) -> ResourceContext:
	return ResourceContext(
		resource_type=task.subject_type,
		resource_id=task.subject_id,
		procuring_entity_id=task.procuring_entity_id,
		financial_year_id=task.financial_year_id,
		organisation_unit_id=task.organisation_unit_id or "",
	)


def _authorized(task, user: str) -> bool:
	capability = cstr(frappe.db.get_value(
		"Workflow Routing Rule",
		{"routing_rule_id": task.routing_rule_id, "version": cint(task.routing_rule_version)},
		"required_capability",
	))
	return bool(capability and evaluate_capability(user, capability, _resource(task), task_id=task.name).allowed)


def _title(task) -> str:
	try:
		meta = frappe.get_meta(task.subject_type)
		return cstr(frappe.db.get_value(task.subject_type, task.subject_id, meta.title_field or "name") or task.subject_id)
	except Exception:
		return cstr(task.subject_id)


def _owner(task) -> str:
	if task.claimed_by:
		return cstr(frappe.utils.get_fullname(task.claimed_by) or task.claimed_by)
	if task.assigned_user_id:
		return cstr(frappe.utils.get_fullname(task.assigned_user_id) or task.assigned_user_id)
	if task.queue_id:
		return cstr(frappe.db.get_value("Workflow Queue", task.queue_id, "queue_name") or task.queue_id)
	return _("Unassigned")


def _row(task, bucket: str) -> dict[str, Any]:
	stage, action, page = _PRESENTATION.get(
		task.task_type,
		(task.task_type.replace(".", " ").title(), _("Open task"), "my-work"),
	)
	route = [page, cstr(task.subject_id)] if page != "my-work" else [page]
	return {
		"task_id": task.name,
		"task_type": task.task_type,
		"title": _title(task),
		"reference": cstr(task.subject_id),
		"module": task.module_name,
		"stage": stage,
		"procuring_entity": task.procuring_entity_id,
		"financial_year": task.financial_year_id,
		"organisation_unit": task.organisation_unit_id or "",
		"assignment": _owner(task),
		"status": _("Waiting") if bucket == "waiting" else _("Available") if bucket == "claimable" else _("Assigned"),
		"received_at": cstr(task.created_at),
		"due_at": cstr(task.due_at or ""),
		"action_label": "" if bucket == "waiting" else action,
		"route": [] if bucket == "waiting" else route,
		"route_options": {} if bucket == "waiting" else {"task_id": task.name},
		"concurrency_token": task.concurrency_token,
		"can_claim": bucket == "claimable",
		"can_open": bucket == "assigned",
	}


def _tasks(entity_ids: set[str]) -> list[Any]:
	if not entity_ids:
		return []
	return frappe.get_all(
		"Workflow Task",
		filters={"state": "Open", "procuring_entity_id": ["in", sorted(entity_ids)]},
		fields=["name", "task_type", "module_name", "subject_type", "subject_id",
			"procuring_entity_id", "financial_year_id", "organisation_unit_id",
			"routing_rule_id", "routing_rule_version", "assignee_type",
			"assigned_user_id", "queue_id", "claimed_by", "created_by_actor",
			"created_at", "due_at", "concurrency_token"],
		order_by="due_at asc, created_at asc",
	)


@frappe.whitelist()
def get_my_work() -> dict[str, Any]:
	user = frappe.session.user
	assignments = _assignments(user)
	empty = {"assigned": [], "claimable": [], "waiting": []}
	if not assignments:
		return {
			"state": "no_assignment",
			"reason_code": NO_ACTIVE_OPERATIONAL_ASSIGNMENT,
			"message": _("No active operational assignment is configured for {0}.").format(user),
			"account": user,
			"assignment_count": 0,
			"assignments": [],
			"counts": {key: 0 for key in empty},
			"buckets": empty,
		}

	entity_ids = {row.procuring_entity_id for row in assignments}
	queue_ids = _queue_ids(user)
	buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
	for task in _tasks(entity_ids):
		assigned = task.assigned_user_id == user or task.claimed_by == user
		claimable = task.assignee_type == "Queue" and task.queue_id in queue_ids and not task.claimed_by
		if assigned and _authorized(task, user):
			buckets["assigned"].append(_row(task, "assigned"))
		elif claimable and _authorized(task, user):
			buckets["claimable"].append(_row(task, "claimable"))
		elif task.created_by_actor == user and not assigned and not claimable:
			# Originator is an explicit workflow relationship. Waiting rows expose no decision action.
			buckets["waiting"].append(_row(task, "waiting"))
	for key in empty:
		buckets.setdefault(key, [])
	return {
		"state": "ready",
		"account": user,
		"assignment_count": len(assignments),
		"assignments": [{
			"assignment_id": row.assignment_id,
			"procuring_entity": row.procuring_entity_id,
			"organisation_unit": row.organisation_unit_id or "",
			"include_descendants": bool(row.include_descendants),
			"resource_scope_type": row.resource_scope_type or "",
			"resource_scope_id": row.resource_scope_id or "",
		} for row in assignments],
		"counts": {key: len(buckets[key]) for key in empty},
		"buckets": dict(buckets),
	}


@frappe.whitelist()
def claim_my_work_task(task_id: str, expected_token: str) -> dict[str, Any]:
	claim_task(task_id, user=frappe.session.user, expected_token=expected_token)
	result = get_my_work()
	result["claimed_task"] = next(
		(row for row in result["buckets"]["assigned"] if row["task_id"] == task_id),
		None,
	)
	return result


def patch_bootinfo_home(bootinfo) -> None:
	"""Use shared My Work as the role-neutral Desk entry for operational users."""
	user = frappe.session.user
	if user not in (None, "Guest", "Administrator") and _assignments(user):
		bootinfo.home_page = "my-work"
