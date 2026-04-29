from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.template_version_workbench import (
	get_std_template_version_parameter_catalogue,
)
from kentender_procurement.std_engine.services.template_version_parameters_service import (
	build_std_template_version_parameter_catalogue,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1009TemplateVersionParameterCatalogue(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, field, value in (
			("STD Parameter Dependency", "dependency_code", "STD-DEP-PH9-1"),
			("STD Parameter Definition", "parameter_code", "STD-PARAM-PH9-B"),
			("STD Parameter Definition", "parameter_code", "STD-PARAM-PH9-A"),
		):
			name = frappe.db.get_value(doctype, {field: value}, "name")
			if name:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		super().tearDown()

	def _insert_two_params_and_dep(self):
		frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": "STD-PARAM-PH9-A",
				"version_code": self.version_code,
				"section_code": self.section_code,
				"label": "Alpha Gate",
				"parameter_group": "Tender Security",
				"data_type": "Boolean",
				"required": 1,
				"drives_dsm": 1,
				"drives_dom": 0,
				"drives_dem": 0,
				"drives_dcm": 0,
				"drives_bundle": 0,
				"addendum_change_requires_acknowledgement": 0,
				"addendum_change_requires_deadline_review": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": "STD-PARAM-PH9-B",
				"version_code": self.version_code,
				"section_code": self.section_code,
				"label": "Beta Field",
				"parameter_group": "TDS",
				"data_type": "String",
				"required": 0,
				"drives_dsm": 0,
				"drives_dom": 0,
				"drives_dem": 0,
				"drives_dcm": 0,
				"drives_bundle": 0,
				"addendum_change_requires_acknowledgement": 0,
				"addendum_change_requires_deadline_review": 0,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Parameter Dependency",
				"dependency_code": "STD-DEP-PH9-1",
				"version_code": self.version_code,
				"trigger_parameter_code": "STD-PARAM-PH9-A",
				"trigger_operator": "=",
				"trigger_value": '{"value": true}',
				"dependent_parameter_code": "STD-PARAM-PH9-B",
				"effect": "Required",
				"condition_expression": "trigger=true",
			}
		).insert()

	def test_catalogue_groups_parameters_and_read_only(self):
		self._insert_two_params_and_dep()
		out = build_std_template_version_parameter_catalogue(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("read_only"))
		self.assertEqual(out.get("version_code"), self.version_code)
		groups = out.get("groups") or []
		self.assertTrue(groups)
		group_names = {g.get("group_name") for g in groups}
		self.assertIn("TDS", group_names)
		self.assertIn("Tender Security", group_names)
		flat = [p for g in groups for p in (g.get("parameters") or [])]
		codes = {p.get("parameter_code") for p in flat}
		self.assertIn("STD-PARAM-PH9-A", codes)
		self.assertIn("STD-PARAM-PH9-B", codes)
		a = next(p for p in flat if p.get("parameter_code") == "STD-PARAM-PH9-A")
		self.assertTrue((a.get("impact") or {}).get("drives_dsm"))
		b = next(p for p in flat if p.get("parameter_code") == "STD-PARAM-PH9-B")
		self.assertIn("section_title", b)
		incoming = b.get("incoming_dependencies") or []
		self.assertTrue(incoming)
		self.assertTrue(any("STD-PARAM-PH9-A" in s for s in incoming))
		self.assertTrue(any("Alpha Gate" in s for s in incoming))

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_parameter_catalogue, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_for_admin(self):
		out = get_std_template_version_parameter_catalogue(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("groups", out)

	def test_not_found(self):
		out = build_std_template_version_parameter_catalogue("NO-SUCH-VERSION-999")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_found")
