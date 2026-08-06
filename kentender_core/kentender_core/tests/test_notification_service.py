"""Phase J — send_notification (log-based) + emit_notification_log (Notification Log)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services.notification_service import (
	emit_notification_log,
	send_notification,
)


class TestSendNotification(unittest.TestCase):
	def test_send_notification_logs_via_frappe_logger(self):
		with patch("kentender_core.services.notification_service.frappe.logger") as mock_logger_fn:
			mock_log = MagicMock()
			mock_logger_fn.return_value = mock_log
			send_notification("Administrator", "hello from test")
			mock_logger_fn.assert_called_once_with("kentender.notification")
			mock_log.info.assert_called_once()
			args, _kwargs = mock_log.info.call_args
			self.assertEqual(args[0], "notification | user=%s | %s")
			self.assertEqual(args[1], "Administrator")
			self.assertEqual(args[2], "hello from test")


class TestEmitNotificationLog(FrappeTestCase):
	def _purge(self, key: str):
		for name in frappe.get_all(
			"Notification Log",
			filters={"email_header": key},
			pluck="name",
		):
			frappe.delete_doc("Notification Log", name, force=True, ignore_permissions=True)

	def test_emit_creates_alert(self):
		key = "kt-test:emit:create:Administrator"
		self._purge(key)
		name = emit_notification_log(
			for_user="Administrator",
			subject="Test subject",
			message="Concise body",
			document_type="User",
			document_name="Administrator",
			event_type="test_event",
			entity_scope="PE-TEST",
			route="/app/budget-funding",
			correlation_key=key,
		)
		self.assertTrue(name)
		row = frappe.get_doc("Notification Log", name)
		self.assertEqual(row.type, "Alert")
		self.assertEqual(row.for_user, "Administrator")
		self.assertEqual(row.subject, "Test subject")
		self.assertIn("Concise body", row.email_content or "")
		self.assertIn("Entity: PE-TEST", row.email_content or "")
		self.assertIn("Event: test_event", row.email_content or "")
		self.assertEqual(row.document_type, "User")
		self.assertEqual(row.document_name, "Administrator")
		self.assertEqual(row.link, "/app/budget-funding")
		self.assertEqual(row.email_header, key)

	def test_emit_idempotent_same_correlation(self):
		key = "kt-test:emit:idem:Administrator"
		self._purge(key)
		first = emit_notification_log(
			for_user="Administrator",
			subject="Once",
			message="Body",
			document_type="User",
			document_name="Administrator",
			event_type="test_idem",
			entity_scope="PE",
			route="/app/budget-funding",
			correlation_key=key,
		)
		second = emit_notification_log(
			for_user="Administrator",
			subject="Twice",
			message="Body2",
			document_type="User",
			document_name="Administrator",
			event_type="test_idem",
			entity_scope="PE",
			route="/app/budget-funding",
			correlation_key=key,
		)
		self.assertEqual(first, second)
		self.assertEqual(
			frappe.db.count("Notification Log", {"for_user": "Administrator", "email_header": key}),
			1,
		)

	def test_emit_swallows_insert_failure(self):
		with patch("kentender_core.services.notification_service.frappe.get_doc") as mock_get:
			mock_doc = MagicMock()
			mock_doc.insert.side_effect = RuntimeError("boom")
			mock_get.return_value = mock_doc
			# Force miss on exists path
			with patch(
				"kentender_core.services.notification_service.frappe.db.get_value",
				return_value=None,
			):
				result = emit_notification_log(
					for_user="Administrator",
					subject="Fail",
					message="x",
					document_type="User",
					document_name="Administrator",
					event_type="fail",
					entity_scope="PE",
					route="/app/x",
					correlation_key="kt-test:emit:fail:Administrator",
				)
		self.assertIsNone(result)
