# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-FR-005 / PLN-GAP-FR-006 — PE-scoped Notification Log for Planning tasks."""

from __future__ import annotations

from typing import Any, Iterable

import frappe
from frappe.utils import cstr

from kentender_core.services.notification_service import emit_notification_log
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_BUDGET_OFFICER,
	ROLE_PLANNER,
	ROLE_REVIEWER,
)

EVENT_FINANCE_REQUESTED = "plan_item_finance_requested"
EVENT_PLAN_SUBMITTED = "plan_submitted_for_review"
EVENT_PLAN_RETURNED = "plan_returned_from_review"


def usa_users_for_role(*, role: str, procuring_entity: str) -> set[str]:
	pe = cstr(procuring_entity).strip()
	wanted = cstr(role).strip()
	if not pe or not wanted:
		return set()
	rows = frappe.get_all(
		"User Scope Assignment",
		filters={"role": wanted, "procuring_entity": pe},
		pluck="user",
	)
	users: set[str] = set()
	for u in rows:
		email = cstr(u).strip()
		if not email or email == "Guest":
			continue
		if frappe.db.get_value("User", email, "enabled"):
			users.add(email)
	return users


def _task_recipients(task_id: str) -> set[str]:
	if not task_id or not frappe.db.exists("Workflow Task", task_id):
		return set()
	task = frappe.get_doc("Workflow Task", task_id)
	if task.state != "Open":
		return set()
	if task.assignee_type == "User":
		return {cstr(task.assigned_user_id)} if task.assigned_user_id else set()
	return {
		cstr(user)
		for user in frappe.get_all(
			"Workflow Queue Membership",
			filters={"queue_id": task.queue_id, "status": "Active"},
			pluck="user_id",
		)
		if cstr(user)
	}


def notify_finance_requested(
	*,
	plan: Any,
	item: Any,
	iv: Any,
	actor: str,
) -> None:
	pe = cstr(getattr(plan, "procuring_entity", "") or "")
	task_id = cstr(getattr(iv, "finance_task_id", "") or "")
	recipients = _task_recipients(task_id)
	_emit_to(
		recipients,
		actor=actor,
		skip_actor_if_others=True,
		subject=f"Finance confirmation requested: {cstr(getattr(item, 'plan_item_code', '') or item.name)}",
		message="A Plan Item is awaiting Finance confirmation.",
		document_type="Procurement Plan",
		document_name=cstr(plan.name),
		event_type=EVENT_FINANCE_REQUESTED,
		entity_scope=pe,
		route=f"/desk/procurement-plan-builder?plan={plan.name}&finance_task={task_id}",
		correlation_key=f"pln-finance-request:{cstr(getattr(iv, 'finance_task_id', '') or iv.name)}",
	)


def notify_plan_submitted(*, plan: Any, version_name: str, actor: str) -> None:
	pe = cstr(getattr(plan, "procuring_entity", "") or "")
	row = frappe.db.get_value("Procurement Plan Version", version_name, ["review_task_id", "review_task_assignee"], as_dict=True)
	recipients = _task_recipients(cstr(row.review_task_id if row else ""))
	_emit_to(
		recipients,
		actor=actor,
		skip_actor_if_others=True,
		subject=f"Plan submitted for review: {cstr(getattr(plan, 'plan_code', '') or plan.name)}",
		message="A Procurement Plan version is ready for professional review.",
		document_type="Procurement Plan",
		document_name=cstr(plan.name),
		event_type=EVENT_PLAN_SUBMITTED,
		entity_scope=pe,
		route=f"/desk/procurement-plan-review?task={cstr(row.review_task_id if row else '')}",
		correlation_key=f"pln-submit-review:{cstr(row.review_task_id if row else version_name)}",
	)


def notify_plan_returned(*, plan: Any, version_name: str, actor: str) -> None:
	pe = cstr(getattr(plan, "procuring_entity", "") or "")
	owner = cstr(getattr(plan, "owner", "") or "")
	recipients = usa_users_for_role(role=ROLE_PLANNER, procuring_entity=pe)
	if owner:
		recipients.add(owner)
	_emit_to(
		recipients,
		actor=actor,
		skip_actor_if_others=True,
		subject=f"Plan returned: {cstr(getattr(plan, 'plan_code', '') or plan.name)}",
		message="A Procurement Plan version was returned from review.",
		document_type="Procurement Plan",
		document_name=cstr(plan.name),
		event_type=EVENT_PLAN_RETURNED,
		entity_scope=pe,
		route=f"/desk/procurement-plan-builder?plan={plan.name}",
		correlation_key=f"pln-return:{cstr(version_name)}:{cstr(actor)}",
	)


def _emit_to(
	recipients: Iterable[str],
	*,
	actor: str,
	skip_actor_if_others: bool,
	subject: str,
	message: str,
	document_type: str,
	document_name: str,
	event_type: str,
	entity_scope: str,
	route: str,
	correlation_key: str,
) -> None:
	try:
		users = {cstr(u).strip() for u in recipients if cstr(u).strip() and cstr(u) != "Guest"}
		act = cstr(actor).strip()
		if skip_actor_if_others and act in users and len(users) > 1:
			users.discard(act)
		for user in sorted(users):
			emit_notification_log(
				for_user=user,
				subject=subject,
				message=message,
				document_type=document_type,
				document_name=document_name,
				event_type=event_type,
				entity_scope=entity_scope,
				route=route,
				correlation_key=correlation_key,
				from_user=act or None,
			)
	except Exception:
		frappe.logger("kentender.planning.notification").error(
			"planning notification failed | event=%s | key=%s",
			event_type,
			correlation_key,
			exc_info=True,
		)
