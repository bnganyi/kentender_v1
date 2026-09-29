# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Telling Opening access support about an incident (BOP-CHG-001 v0.10 §8
BOP_OPENING_PROFILE_UNAVAILABLE, §11 Notify support; plan D11).

The notice goes to the incident's holders as an in-app Notification Log,
never as a My Work item (§5). One incident has one correlation key, so a
retry after a failed delivery resends the same notice and never creates a
second incident or a duplicate (branch (6)). "Opening access support has been
told" is shown only when delivery is committed. Transports are found on the
`kt_bop_support_transports` hook, in order; the first that answers wins."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_bop_support_transports"
INCIDENT = "Opening Access Incident"


def holders() -> list[str]:
	"""The current Technical Operator holders (plan D11)."""
	return frappe.get_all("User Responsibility Assignment", filters={"business_role": "Technical Operator", "status": "Enabled"}, pluck="user", distinct=True)


def deliver(*, incident_id: str, subject: str, message: str, users: list[str]) -> dict[str, Any]:
	if not users:
		return {"delivered": False, "delivered_to": []}
	for path in frappe.get_hooks(HOOK) or []:
		result = frappe.get_attr(path)(incident_id=incident_id, subject=subject, message=message, users=list(users))
		if result is not None:
			return result
	return {"delivered": False, "delivered_to": []}


def notification_log(*, incident_id: str, subject: str, message: str, users: list[str]) -> dict[str, Any]:
	from kentender_core.services.notification_service import emit_notification_log

	delivered = [user for user in users if emit_notification_log(
		for_user=user, subject=subject, message=message, document_type=INCIDENT, document_name=incident_id, event_type="Opening access",
		entity_scope="Bid Opening", route=f"/app/opening-access-incident/{incident_id}", correlation_key=f"bop-incident:{incident_id}",
	)]
	return {"delivered": bool(delivered), "delivered_to": delivered}
