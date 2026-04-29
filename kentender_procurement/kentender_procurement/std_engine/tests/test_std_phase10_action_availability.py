from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.landing import get_std_action_availability
from kentender_procurement.std_engine.services.action_availability_service import (
	build_std_action_availability,
	resolve_std_document,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1006ActionAvailability(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_not_found_payload(self):
		out = build_std_action_availability("STD Instance", "NO-SUCH-CODE-999", "Administrator")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_found")
		self.assertTrue(str(out.get("message") or ""))

	def test_resolve_std_instance(self):
		res = resolve_std_document("STD Instance", self.instance_code)
		self.assertIsNotNone(res)
		dt, name, doc = res
		self.assertEqual(dt, "STD Instance")
		self.assertEqual(doc.instance_code, self.instance_code)

	def test_whitelist_returns_bundle_for_instance(self):
		out = get_std_action_availability(object_type="STD Instance", object_code=self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("doctype"), "STD Instance")
		self.assertTrue(out.get("name"))
		self.assertEqual(out.get("code"), self.instance_code)
		self.assertIsInstance(out.get("state_cards"), list)
		self.assertTrue(out["state_cards"])
		self.assertIsInstance(out.get("actions"), list)
		self.assertIsInstance(out.get("blockers"), list)
		self.assertIsInstance(out.get("warnings"), list)

		ids = [a.get("id") for a in out["actions"]]
		self.assertIn("open_in_desk", ids)
		self.assertIn("edit_in_desk", ids)
		open_a = next(a for a in out["actions"] if a.get("id") == "open_in_desk")
		self.assertTrue(open_a.get("allowed"))
		self.assertFalse(open_a.get("disabled"))
		self.assertIsInstance(open_a.get("route"), list)

	def test_denied_edit_includes_reason_for_guest_actor(self):
		"""Non-session actor override is restricted; build_* uses explicit user for permission bits."""
		out = build_std_action_availability("STD Instance", self.instance_code, actor="Guest")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_permitted")

	def test_template_version_open_and_state_cards(self):
		out = build_std_action_availability("Template Version", self.version_code, "Administrator")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("doctype"), "STD Template Version")
		codes = {c.get("id") for c in out.get("state_cards") or []}
		self.assertIn("version_status", codes)
		create = next((a for a in out["actions"] if a.get("id") == "create_std_instance"), None)
		self.assertIsNotNone(create)
		if not create.get("allowed"):
			self.assertTrue(str(create.get("reason") or "").strip())

	def test_disabled_actions_include_reason_field(self):
		out = build_std_action_availability("STD Instance", self.instance_code, "Administrator")
		self.assertTrue(out.get("ok"))
		for a in out.get("actions") or []:
			self.assertIn("reason", a)
			if a.get("disabled"):
				self.assertIsInstance(a.get("reason"), str)
