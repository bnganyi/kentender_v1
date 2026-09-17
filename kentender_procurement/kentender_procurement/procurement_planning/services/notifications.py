# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §10 — Planning task notifications through the shared
KenTender surface (`kentender_core.services.notification_service`).

Notifications route work; they never authorise it (AUTH §5.5). Only assigned
business work raises one: a Finance review to decide, a governance task to
adopt or approve. Planning raises no schedule-driven notification at all in
this MVP — see the note below.
"""

from __future__ import annotations

import frappe

from kentender_core.services.notification_service import emit_notification_log


# PLN-CHG-001 v1.23 §7.5 / §15.3 (PLN23-CHG-001): the milestone-notice
# producer and its approaching-milestone nudge are removed with the forecast
# facility. Planning raises no schedule-driven notification in this MVP. What
# remains below is the ordinary assigned-task notification, which belongs to
# Finance and governance work, not to a schedule.


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
