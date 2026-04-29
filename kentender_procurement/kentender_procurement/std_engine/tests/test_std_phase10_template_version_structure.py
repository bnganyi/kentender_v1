from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.template_version_workbench import (
	get_std_template_version_structure_tree,
)
from kentender_procurement.std_engine.services.template_version_structure_service import (
	build_std_template_version_structure_tree,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1008TemplateVersionStructureTree(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_tree_returns_part_and_section(self):
		out = build_std_template_version_structure_tree(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("version_code"), self.version_code)
		parts = out.get("parts") or []
		self.assertTrue(parts)
		p0 = parts[0]
		self.assertEqual(p0.get("part_code"), self.part_code)
		secs = p0.get("sections") or []
		self.assertTrue(secs)
		self.assertEqual(secs[0].get("section_code"), self.section_code)
		self.assertIn("editability", secs[0])
		self.assertIn("itt_locked_hint", secs[0])
		self.assertIn("gcc_locked_hint", secs[0])

	def test_clause_nested_under_section(self):
		clause_code = "STD-CLAUSE-PH8-1"
		if frappe.db.exists("STD Clause Definition", {"clause_code": clause_code}):
			name = frappe.db.get_value("STD Clause Definition", {"clause_code": clause_code}, "name")
			frappe.delete_doc("STD Clause Definition", name, force=True, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "STD Clause Definition",
				"clause_code": clause_code,
				"section_code": self.section_code,
				"version_code": self.version_code,
				"clause_number": "V.1",
				"clause_title": "Test clause",
				"editability": "Locked",
				"instance_edit_allowed": 0,
				"is_mandatory": 0,
				"order_index": 1,
				"source_document_code": self.source_doc,
				"source_page_start": 1,
				"source_page_end": 2,
				"drives_dsm": 1,
				"drives_dem": 0,
			}
		).insert()
		try:
			out = build_std_template_version_structure_tree(self.version_code)
			self.assertTrue(out.get("ok"))
			secs = (out["parts"][0].get("sections") or [])
			sec = next(s for s in secs if s.get("section_code") == self.section_code)
			clauses = sec.get("clauses") or []
			self.assertTrue(any(c.get("clause_code") == clause_code for c in clauses))
			cl = next(c for c in clauses if c.get("clause_code") == clause_code)
			self.assertTrue((cl.get("impact") or {}).get("drives_dsm"))
			self.assertIn("source_document_title", cl)
		finally:
			cn = frappe.db.get_value("STD Clause Definition", {"clause_code": clause_code}, "name")
			if cn:
				frappe.delete_doc("STD Clause Definition", cn, force=True, ignore_permissions=True)

	def test_parameter_only_editability_in_payload(self):
		sec_name = frappe.db.get_value("STD Section Definition", {"section_code": self.section_code}, "name")
		prev = frappe.db.get_value("STD Section Definition", sec_name, "editability")
		frappe.db.set_value("STD Section Definition", sec_name, "editability", "Parameter Only")
		try:
			out = build_std_template_version_structure_tree(self.version_code)
			self.assertTrue(out.get("ok"))
			secs = (out["parts"][0].get("sections") or [])
			sec = next(s for s in secs if s.get("section_code") == self.section_code)
			self.assertEqual(sec.get("editability"), "Parameter Only")
		finally:
			frappe.db.set_value("STD Section Definition", sec_name, "editability", prev)

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_structure_tree, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_tree_for_admin(self):
		out = get_std_template_version_structure_tree(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("parts"))

	def test_not_found(self):
		out = build_std_template_version_structure_tree("NO-SUCH-VERSION-999")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_found")
