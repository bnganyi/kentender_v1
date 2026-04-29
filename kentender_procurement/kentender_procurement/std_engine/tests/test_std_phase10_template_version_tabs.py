from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.template_version_workbench import (
	get_std_template_version_workbench_summary,
)
from kentender_procurement.std_engine.services.template_version_workbench_service import (
	build_std_template_version_workbench_summary,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1007TemplateVersionWorkbenchSummary(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_summary_active_immutable_is_read_only(self):
		out = build_std_template_version_workbench_summary(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("version_code"), self.version_code)
		self.assertEqual(out.get("version_status"), "Active")
		self.assertTrue(out.get("read_only"))
		self.assertEqual(int(out.get("immutable_after_activation") or 0), 1)
		self.assertIn("locked_section_count", out)
		self.assertIn("itt_locked", out)
		self.assertIn("gcc_locked", out)
		self.assertIsInstance(out.get("sample_locked_titles"), list)

	def test_read_only_false_when_not_active_or_not_immutable(self):
		name = frappe.db.get_value("STD Template Version", {"version_code": self.version_code}, "name")
		frappe.db.set_value("STD Template Version", name, "version_status", "Draft")
		frappe.db.set_value("STD Template Version", name, "immutable_after_activation", 0)
		try:
			out = build_std_template_version_workbench_summary(self.version_code)
			self.assertTrue(out.get("ok"))
			self.assertFalse(out.get("read_only"))
		finally:
			frappe.db.set_value("STD Template Version", name, "version_status", "Active")
			frappe.db.set_value("STD Template Version", name, "immutable_after_activation", 1)

	def test_itt_and_gcc_locked_heuristic(self):
		for code, title in (
			("STD-SEC-PH6-ITT-LOCK", "ITT Invitation Schedule"),
			("STD-SEC-PH6-GCC-LOCK", "General GCC Conditions"),
		):
			if not frappe.db.exists("STD Section Definition", {"section_code": code}):
				frappe.get_doc(
					{
						"doctype": "STD Section Definition",
						"section_code": code,
						"version_code": self.version_code,
						"part_code": self.part_code,
						"section_number": "X",
						"section_title": title,
						"section_classification": "Core",
						"editability": "Locked",
						"is_mandatory": 0,
						"is_supplier_facing": 0,
						"is_contract_facing": 0,
						"order_index": 99,
						"source_document_code": self.source_doc,
					}
				).insert()

		out = build_std_template_version_workbench_summary(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("itt_locked"))
		self.assertTrue(out.get("gcc_locked"))
		self.assertGreaterEqual(int(out.get("locked_section_count") or 0), 2)

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_workbench_summary, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_summary_for_admin(self):
		out = get_std_template_version_workbench_summary(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("version_code"), self.version_code)

	def test_not_found(self):
		out = build_std_template_version_workbench_summary("NO-SUCH-VERSION-999")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_found")
