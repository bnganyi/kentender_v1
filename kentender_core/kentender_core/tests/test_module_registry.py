# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE

from frappe.tests import IntegrationTestCase

from kentender_core.module_registry import KT_MODULES, get_module, get_route_sidebar_keys


class TestModuleRegistry(IntegrationTestCase):
	def test_modules_defined(self):
		self.assertIn("strategy", KT_MODULES)
		self.assertIn("budget", KT_MODULES)
		self.assertIn("dia", KT_MODULES)

	def test_get_module(self):
		mod = get_module("budget")
		self.assertIsNotNone(mod)
		self.assertEqual(mod["workspace_label"], "Budget Management")

	def test_route_sidebar_keys_include_builders(self):
		keys = get_route_sidebar_keys()
		self.assertIn("strategy-builder", keys)
		self.assertIn("budget-builder", keys)
		self.assertIn("form/demand", keys)
