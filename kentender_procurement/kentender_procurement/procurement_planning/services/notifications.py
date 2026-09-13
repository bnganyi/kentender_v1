# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1B / §8.3 / §10 — Planning notifications through
the shared KenTender surface (`kentender_core.services.notification_service`)
and the dedicated `Milestone Notice` shared-identity record (plan D11).

Notifications route work; they never authorise it (AUTH §5.5). The
Notification Log nudge stays deduplicated per item, milestone and day by the
shared service's correlation key (PLN-AC-130); `Milestone Notice` is the
separate, evolving record §5.5.1B itself describes — one row per (recipient,
stable item, proceeding if any, milestone), updated in place on every run
rather than duplicated, its `history` retaining every state it has carried.
Reading or acknowledging a notice never records completion; only
`clear_milestone_notice`, called from the actual-recording path, does.
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import cstr, formatdate, now_datetime

from kentender_core.services.notification_service import emit_notification_log
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER


def _planners() -> list[str]:
	from kentender_core.services.authorization import resolve_assignments

	users = frappe.get_all(
		"User Responsibility Assignment",
		filters={"business_role": ROLE_PROCUREMENT_PLANNER, "status": "Enabled"},
		pluck="user",
		distinct=True,
	)
	return sorted({u for u in users if resolve_assignments(u, ROLE_PROCUREMENT_PLANNER)})


def notify_approaching_milestone(item, milestone: str, forecast, days: int, today) -> list[str]:
	from kentender_procurement.procurement_planning.services.schedule import MILESTONE_LABELS

	label = MILESTONE_LABELS[milestone]
	when = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
	subject = f"{item.plan_item_id} — {label} due {when}"
	message = (
		f"{item.title}: the forecast {label.lower()} date is {formatdate(forecast, 'd MMM yyyy')}. "
		"Shift the schedule from that milestone if it will slip."
	)
	sent = []
	for user in _planners():
		result = emit_notification_log(
			for_user=user,
			subject=subject,
			message=message,
			document_type="Annual Plan Item",
			document_name=item.name,
			event_type="planning.milestone_approaching",
			entity_scope="site",
			route=f"/app/procurement-plan-item/{item.plan_item_id}",
			correlation_key=f"pln:milestone:{item.plan_item_id}:{milestone}:{cstr(forecast)}:{cstr(today)}",
		)
		if result:
			sent.append(result)
	return sent


def _notice_key(recipient: str, plan_item_id: str, proceeding_id: str, milestone: str) -> str:
	return f"{recipient}:{plan_item_id}:{cstr(proceeding_id)}:{milestone}"


def upsert_milestone_notice(*, item, milestone: str, proceeding_id: str, due_date, status: str, evaluated_at) -> list[str]:
	"""§5.5.1B `MilestoneNotice` — one evolving notice per (recipient, stable
	item, proceeding if any, milestone); a repeated run updates this same
	row (matched on `notification_key`) rather than creating another."""
	touched = []
	for recipient in _planners():
		key = _notice_key(recipient, item.plan_item_id, proceeding_id, milestone)
		existing = frappe.db.get_value("Milestone Notice", {"notification_key": key}, ["name", "history"], as_dict=True)
		entry = {"status": status, "due_date": cstr(due_date), "evaluated_at": cstr(evaluated_at)}
		if existing:
			history = json.loads(existing.history or "[]")
			if not history or history[-1].get("status") != status:
				history.append(entry)
			frappe.db.set_value(
				"Milestone Notice", existing.name,
				{"due_date": due_date, "notice_status": status, "last_evaluated_at": evaluated_at, "history": json.dumps(history)},
				update_modified=False,
			)
			touched.append(existing.name)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Milestone Notice", "recipient": recipient, "plan_item": item.plan_item, "plan_item_id": item.plan_item_id,
					"proceeding_id": cstr(proceeding_id), "milestone": milestone, "due_date": due_date, "notice_status": status,
					"notification_key": key, "last_evaluated_at": evaluated_at, "history": json.dumps([entry]),
					"fixture_namespace": cstr(item.fixture_namespace),
				}
			).insert(ignore_permissions=True)
			touched.append(doc.name)
	return touched


def clear_milestone_notice(*, plan_item_id: str, milestone: str, proceeding_id: str = "", evaluated_at=None) -> list[str]:
	"""§5.5.1B — "Actual received: resolve the corresponding notice." Called
	from `record_tender_milestone_actual`, never from a read."""
	evaluated_at = evaluated_at or now_datetime()
	cleared = []
	for name in frappe.get_all(
		"Milestone Notice",
		filters={"plan_item_id": plan_item_id, "proceeding_id": cstr(proceeding_id), "milestone": milestone, "notice_status": ("!=", "Cleared")},
		pluck="name",
	):
		history = json.loads(frappe.db.get_value("Milestone Notice", name, "history") or "[]")
		history.append({"status": "Cleared", "evaluated_at": cstr(evaluated_at)})
		frappe.db.set_value("Milestone Notice", name, {"notice_status": "Cleared", "last_evaluated_at": evaluated_at, "history": json.dumps(history)}, update_modified=False)
		cleared.append(name)
	return cleared


def notify_task(*, for_user: str, subject: str, message: str, document_type: str, document_name: str, event_type: str, route: str, correlation_key: str) -> str | None:
	return emit_notification_log(
		for_user=for_user,
		subject=subject,
		message=message,
		document_type=document_type,
		document_name=document_name,
		event_type=event_type,
		entity_scope="site",
		route=route,
		correlation_key=correlation_key,
	)
