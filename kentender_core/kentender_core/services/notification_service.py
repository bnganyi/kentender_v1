"""Lightweight notifications for KenTender (Phase J — log-based).

Uses Frappe logging only. Email, in-app records, and external channels are out of
scope for Wave 0.
"""

from __future__ import annotations

import frappe

_LOGGER_NAME = "kentender.notification"


def send_notification(user: str, message: str) -> None:
	"""Record a notification intent for *user* with *message* (no delivery in Phase J)."""
	frappe.logger(_LOGGER_NAME).info("notification | user=%s | %s", user, message)
