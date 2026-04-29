from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.instance_workbench import get_std_instance_workbench_shell
from kentender_procurement.std_engine.services.instance_workbench_service import (
	build_std_instance_workbench_shell,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1101InstanceWorkbenchShell(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_shell_ok_default_fixture(self):
		out = build_std_instance_workbench_shell(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("instance_code"), self.instance_code)
		self.assertIn("instance_status", out)
		self.assertIn("readiness_status", out)
		self.assertIn("read_only", out)
		self.assertIn("addendum_guidance", out)
		self.assertIn("tender_code", out)
		self.assertIn("template_version_code", out)
		self.assertIn("profile_code", out)

	def test_published_locked_read_only_and_addendum_guidance(self):
		name = frappe.db.get_value("STD Instance", {"instance_code": self.instance_code}, "name")
		frappe.db.set_value("STD Instance", name, "instance_status", "Published Locked")
		try:
			out = build_std_instance_workbench_shell(self.instance_code)
			self.assertTrue(out.get("ok"))
			self.assertTrue(out.get("read_only"))
			self.assertTrue(str(out.get("addendum_guidance") or "").strip())
		finally:
			frappe.db.set_value("STD Instance", name, "instance_status", "Draft")

	def test_draft_not_read_only_empty_addendum_by_default(self):
		name = frappe.db.get_value("STD Instance", {"instance_code": self.instance_code}, "name")
		frappe.db.set_value("STD Instance", name, "instance_status", "Draft")
		out = build_std_instance_workbench_shell(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertFalse(out.get("read_only"))
		self.assertFalse(str(out.get("addendum_guidance") or "").strip())

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_instance_workbench_shell, self.instance_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_for_admin(self):
		out = get_std_instance_workbench_shell(self.instance_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("instance_code"), self.instance_code)

	def test_not_found(self):
		out = build_std_instance_workbench_shell("NO-SUCH-INSTANCE-999")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_found")
