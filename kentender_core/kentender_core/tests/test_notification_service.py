"""Phase J — send_notification (log-based)."""

import unittest
from unittest.mock import MagicMock, patch

from kentender_core.services.notification_service import send_notification


class TestNotificationService(unittest.TestCase):
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
