# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Regression: optional actor wrapper must not corrupt ``frappe.session.sid``."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.utils.session_actor import with_optional_user_actor


class TestSessionActor(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_with_optional_user_actor_none_actor_preserves_sid(self):
		sid_before = frappe.session.sid
		self.assertEqual(with_optional_user_actor(None, lambda: 99), 99)
		self.assertEqual(frappe.session.sid, sid_before)

	def test_with_optional_user_actor_switch_restores_sid(self):
		sid_before = frappe.session.sid
		with_optional_user_actor("Administrator", lambda: None)
		self.assertEqual(frappe.session.sid, sid_before)
		self.assertEqual(frappe.session.user, "Administrator")
