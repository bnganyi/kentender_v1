# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.3 / §10 — Planning notifications through the shared
KenTender surface (`kentender_core.services.notification_service`).

Notifications route work; they never authorise it (AUTH §5.5). The daily
approaching-milestone nudge is deduplicated per item, milestone and day by
the shared service's correlation key, so a repeated run never duplicates an
unresolved notification (PLN-AC-130).
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr, formatdate

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
