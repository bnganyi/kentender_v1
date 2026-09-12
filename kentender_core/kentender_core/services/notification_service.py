"""KenTender notifications.

`send_notification` remains Phase J log-only (Wave 0 contract).
`emit_notification_log` writes idempotent Desk Notification Log (Alert) records.
"""

from __future__ import annotations

import frappe

_LOGGER_NAME = "kentender.notification"


def send_notification(user: str, message: str) -> None:
	"""Record a notification intent for *user* with *message* (no delivery in Phase J)."""
	frappe.logger(_LOGGER_NAME).info("notification | user=%s | %s", user, message)


def emit_notification_log(
	*,
	for_user: str,
	subject: str,
	message: str,
	document_type: str,
	document_name: str,
	event_type: str,
	entity_scope: str,
	route: str,
	correlation_key: str,
	from_user: str | None = None,
) -> str | None:
	"""Insert an idempotent in-app Notification Log (Alert). Never raises.

	Returns the Notification Log name, or None when skipped/failed.
	Idempotency key is stored in ``email_header`` and matched with ``for_user``.
	"""
	try:
		user = (for_user or "").strip()
		key = (correlation_key or "").strip()
		if not user or user == "Guest" or not key:
			return None

		existing = frappe.db.get_value(
			"Notification Log",
			{"for_user": user, "email_header": key},
			"name",
		)
		if existing:
			return existing

		body_parts = [
			(message or "").strip(),
			f"Entity: {(entity_scope or '').strip() or '—'}",
			f"Event: {(event_type or '').strip() or '—'}",
		]
		email_content = "\n".join(p for p in body_parts if p)

		doc = frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"subject": (subject or "").strip() or event_type or "KenTender alert",
				"email_content": email_content,
				"type": "Alert",
				"document_type": document_type or "",
				"document_name": document_name or "",
				"link": (route or "").strip(),
				"email_header": key,
				"from_user": (from_user or frappe.session.user or "").strip() or None,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		frappe.logger(_LOGGER_NAME).error(
			"emit_notification_log failed | user=%s | key=%s | event=%s",
			for_user,
			correlation_key,
			event_type,
			exc_info=True,
		)
		return None


def upsert_notification_log(
	*,
	for_user: str,
	subject: str,
	message: str,
	document_type: str,
	document_name: str,
	event_type: str,
	entity_scope: str,
	route: str,
	correlation_key: str,
	from_user: str | None = None,
	active: bool = True,
) -> str | None:
	"""PLN-CHG-001 v1.18 §5.5.1B — one evolving notice per correlation key.

	Unlike `emit_notification_log`, an existing row with the same
	(`for_user`, `correlation_key`) is **updated in place** (subject, body,
	link, unread) rather than left untouched, so a daily check or a reforecast
	refreshes the same notice instead of creating another. `active=False`
	marks the notice read without deleting it (history retained). Never
	raises; returns the Notification Log name or None.
	"""
	try:
		user = (for_user or "").strip()
		key = (correlation_key or "").strip()
		if not user or user == "Guest" or not key:
			return None
		body_parts = [
			(message or "").strip(),
			f"Entity: {(entity_scope or '').strip() or '—'}",
			f"Event: {(event_type or '').strip() or '—'}",
		]
		email_content = "\n".join(p for p in body_parts if p)
		existing = frappe.db.get_value("Notification Log", {"for_user": user, "email_header": key}, "name")
		if existing:
			frappe.db.set_value(
				"Notification Log",
				existing,
				{
					"subject": (subject or "").strip() or event_type or "KenTender alert",
					"email_content": email_content,
					"link": (route or "").strip(),
					"document_type": document_type or "",
					"document_name": document_name or "",
					"read": 0 if active else 1,
				},
			)
			return existing
		if not active:
			return None
		doc = frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"subject": (subject or "").strip() or event_type or "KenTender alert",
				"email_content": email_content,
				"type": "Alert",
				"document_type": document_type or "",
				"document_name": document_name or "",
				"link": (route or "").strip(),
				"email_header": key,
				"from_user": (from_user or frappe.session.user or "").strip() or None,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		frappe.logger(_LOGGER_NAME).error(
			"upsert_notification_log failed | user=%s | key=%s | event=%s",
			for_user,
			correlation_key,
			event_type,
			exc_info=True,
		)
		return None
