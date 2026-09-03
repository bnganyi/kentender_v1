"""Durable notification effects for Departmental Needs (NDS-CHG-001 v1.1 §8.2).

Notifications are durable post-commit effects for submit, return, accept,
decline and withdrawal decisions — not separate business records or
user-entered messages (§8.2). Follows the established kentender_strategy /
kentender_budget facade pattern: a thin module wrapper over kentender_core's
idempotent Notification Log writer that never raises back into the command.

Recipients resolve from native roles and User Permission scope (§6). There is
no delegation lookup: an acting HoD holds the same Head of User Department role
with a time-bound User Permission (§1.1, NDS-AC-042).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_core.services.notification_service import emit_notification_log
from kentender_procurement.departmental_needs.constants import (
	ROLE_HEAD_OF_USER_DEPARTMENT,
	TASK_INITIAL_ACCEPTANCE,
	TASK_OPEN,
	TASK_SUCCESSOR_ACCEPTANCE,
	TASK_WITHDRAWAL,
)
from kentender_procurement.departmental_needs.services.permissions import in_scope

EVENT_SUBMITTED = "departmental_need_submitted"
EVENT_RETURNED = "departmental_need_returned"
EVENT_ACCEPTED = "departmental_need_accepted"
EVENT_DECLINED = "departmental_need_declined"
EVENT_WITHDRAWAL_REQUESTED = "departmental_need_withdrawal_requested"
EVENT_WITHDRAWAL_APPROVED = "departmental_need_withdrawal_approved"
EVENT_WITHDRAWAL_DECLINED = "departmental_need_withdrawal_declined"

_ACTION_EVENT = {
	"Submit": EVENT_SUBMITTED,
	"Resubmit": EVENT_SUBMITTED,
	"Submit successor": EVENT_SUBMITTED,
	"Return for correction": EVENT_RETURNED,
	"Return successor": EVENT_RETURNED,
	"Accept for planning": EVENT_ACCEPTED,
	"Accept successor": EVENT_ACCEPTED,
	"Do not take forward": EVENT_DECLINED,
	"Decline successor": EVENT_DECLINED,
	"Request withdrawal": EVENT_WITHDRAWAL_REQUESTED,
	"Approve withdrawal": EVENT_WITHDRAWAL_APPROVED,
	"Decline withdrawal": EVENT_WITHDRAWAL_DECLINED,
}

# Events addressed to the departmental reviewer rather than the author.
_REVIEWER_EVENTS = frozenset({EVENT_SUBMITTED, EVENT_WITHDRAWAL_REQUESTED})

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
	EVENT_WITHDRAWAL_REQUESTED: (
		_("Withdrawal requested for Departmental Need {0}"),
		_("{0} has an open withdrawal request awaiting departmental review."),
	),
	EVENT_WITHDRAWAL_APPROVED: (
		_("Departmental Need {0} withdrawn"),
		_("The withdrawal request for {0} was approved."),
	),
	EVENT_WITHDRAWAL_DECLINED: (
		_("Withdrawal declined for Departmental Need {0}"),
		_("The withdrawal request for {0} was declined; the accepted version remains current."),
	),
}


def _reviewers(need) -> list[str]:
	"""Users holding the HoD role within this Need's exact scope (§4.4)."""
	holders = frappe.get_all(
		"Has Role",
		filters={"role": ROLE_HEAD_OF_USER_DEPARTMENT, "parenttype": "User"},
		pluck="parent",
	)
	enabled = set(
		frappe.get_all(
			"User",
			filters={"name": ("in", list(set(holders)) or [""]), "enabled": 1},
			pluck="name",
		)
	)
	return sorted(
		user
		for user in enabled
		if in_scope(
			user,
			procuring_entity=need.procuring_entity,
			organisation_unit=need.organisation_unit,
			financial_year=need.financial_year,
		)
	)


def _recipients_for(event_type: str, need) -> list[str]:
	if event_type in _REVIEWER_EVENTS:
		return _reviewers(need)
	author = cstr(need.owner).strip()
	return [author] if author and author != "Guest" else []


def _open_task_route(need, event_type: str) -> str:
	"""Route of the open review task this event created, or "" if not found."""
	task_type = (
		TASK_WITHDRAWAL if event_type == EVENT_WITHDRAWAL_REQUESTED
		else ("in", [TASK_INITIAL_ACCEPTANCE, TASK_SUCCESSOR_ACCEPTANCE])
	)
	row = frappe.db.get_value(
		"Departmental Need Review Task",
		{"departmental_need": need.name, "status": TASK_OPEN, "task_type": task_type},
		["name", "task_type"],
		order_by="opened_at desc",
		as_dict=True,
	)
	if not row:
		return ""
	suffix = "/withdrawal" if row.task_type == TASK_WITHDRAWAL else ""
	return f"/app/departmental-needs/review/{row.name}{suffix}"


def notify_need_transition(need, *, action: str) -> list[str | None]:
	"""Emit Notification Log rows for a transition.

	Never raises: a notification failure must not roll back or fail the command
	whose state change already succeeded.
	"""
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
		route = f"/app/departmental-needs/{need.need_reference}"
		if event_type in _REVIEWER_EVENTS:
			# The reviewer's notification lands on the exact decision screen
			# (NDS-UI-05 / NDS-UI-07), not the record: My Work and notifications
			# are the reviewer's route to a decision — there is no queue menu.
			task_route = _open_task_route(need, event_type)
			if task_route:
				route = task_route
		token = f"{need.current_state}:{cstr(need.record_version)}"
		created: list[str | None] = []
		for user in recipients:
			key = f"kt-nds:{event_type}:{need.name}:{token}:{user}"
			created.append(
				emit_notification_log(
					for_user=user,
					subject=subject,
					message=message,
					document_type="Departmental Need",
					document_name=need.name,
					event_type=event_type,
					entity_scope=cstr(need.procuring_entity),
					route=route,
					correlation_key=key,
					from_user=frappe.session.user,
				)
			)
		return created
	except Exception:
		frappe.logger("kentender.notification").error(
			"notify_need_transition failed | action=%s", action, exc_info=True
		)
		return []
