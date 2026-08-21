"""NDS-CHG-002 §5/NDS-FR-037 — durable in-app notification events for
submit, return, accept and decline. Follows the established
kentender_strategy/kentender_budget notification-facade pattern: a thin
module-specific wrapper over kentender_core's idempotent Notification Log
writer, never raising back into the calling command."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_core.services.notification_service import emit_notification_log
from kentender_procurement.departmental_needs.constants import TASK_DEPARTMENT_REVIEW

EVENT_SUBMITTED = "departmental_need_submitted"
EVENT_RETURNED = "departmental_need_returned"
EVENT_ACCEPTED = "departmental_need_accepted"
EVENT_DECLINED = "departmental_need_declined"

_ACTION_EVENT = {
	"Submit": EVENT_SUBMITTED,
	"Resubmit": EVENT_SUBMITTED,
	"Return for correction": EVENT_RETURNED,
	"Accept for planning": EVENT_ACCEPTED,
	"Do not take forward": EVENT_DECLINED,
}

_ROUTE = {
	EVENT_SUBMITTED: "departmental-needs-review",
	EVENT_RETURNED: "departmental-needs-edit",
	EVENT_ACCEPTED: "departmental-needs-detail",
	EVENT_DECLINED: "departmental-needs-detail",
}

_SUBJECT_MESSAGE = {
	EVENT_SUBMITTED: (
		_("Departmental Need {0} submitted for review"),
		_("{0} is awaiting departmental review."),
	),
	EVENT_RETURNED: (
		_("Departmental Need {0} returned"),
		_("{0} was returned for correction."),
	),
	EVENT_ACCEPTED: (
		_("Departmental Need {0} accepted for planning"),
		_("{0} was accepted for departmental procurement planning."),
	),
	EVENT_DECLINED: (
		_("Departmental Need {0} not taken forward"),
		_("{0} will not be taken forward."),
	),
}


def _review_recipients(need) -> list[str]:
	"""NDS-FR-030's "effective HoUD and eligible departmental delegates" —
	the same routing-rule assignee submit_need() dispatches the review task
	to, plus any user with an active delegation FROM that assignee for the
	same scope."""
	reviewer = frappe.db.get_value(
		"Workflow Routing Rule",
		{
			"module_name": "Departmental Needs", "task_type": TASK_DEPARTMENT_REVIEW,
			"procuring_entity_id": need.procuring_entity, "organisation_unit_id": need.organisation_unit, "status": "Active",
		},
		"assignee_user_id", order_by="version desc",
	)
	if not reviewer:
		return []
	users = {reviewer}
	delegates = frappe.get_all(
		"Authorization Delegation",
		filters={
			"delegator_user_id": reviewer, "procuring_entity_id": need.procuring_entity,
			"organisation_unit_id": need.organisation_unit, "status": "Active",
		},
		pluck="delegate_user_id",
	)
	users.update(u for u in delegates if u)
	return sorted(users)


def _recipients_for(event_type: str, need) -> list[str]:
	if event_type == EVENT_SUBMITTED:
		return _review_recipients(need)
	submitter = cstr(need.submitted_by).strip()
	return [submitter] if submitter and submitter != "Guest" else []


def notify_need_transition(need, *, action: str) -> list[str | None]:
	"""Emit Notification Log rows for a Departmental Need transition. Never
	raises — a notification failure must not roll back or fail the command
	that already committed the actual state change."""
	event_type = _ACTION_EVENT.get(action)
	if not event_type:
		return []
	try:
		recipients = _recipients_for(event_type, need)
		if not recipients:
			return []
		subject_tpl, message_tpl = _SUBJECT_MESSAGE[event_type]
		label = need.need_reference or need.name
		subject, message = subject_tpl.format(label), message_tpl.format(label)
		route = f"/app/{_ROUTE[event_type]}?need={need.name}"
		token = f"{need.status}:{cstr(need.modified)}"
		created: list[str | None] = []
		for user in recipients:
			key = f"kt-nds:{event_type}:{need.name}:{token}:{user}"
			created.append(emit_notification_log(
				for_user=user, subject=subject, message=message,
				document_type="Departmental Need", document_name=need.name,
				event_type=event_type, entity_scope=cstr(need.procuring_entity),
				route=route, correlation_key=key, from_user=frappe.session.user,
			))
		return created
	except Exception:
		frappe.logger("kentender.notification").error("notify_need_transition failed | action=%s", action, exc_info=True)
		return []
