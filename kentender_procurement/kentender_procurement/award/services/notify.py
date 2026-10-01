# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""In-app notices for Award work (the bell). Idempotent per key; a notice is
a courtesy, never the task itself — tasks come from `my_work_provider`."""

from __future__ import annotations

from frappe.utils import cstr


def tell(doc, users, *, subject: str, message: str = "", key: str, event_type: str = "Award") -> None:
	from kentender_core.services.notification_service import emit_notification_log

	for user in {u for u in users if u}:
		emit_notification_log(for_user=user, subject=cstr(subject), message=cstr(message or subject), document_type="Award Case", document_name=doc.name,
			event_type=event_type, entity_scope="Award", route=f"/app/award/{doc.name}", correlation_key=f"award:{key}:{user}")
