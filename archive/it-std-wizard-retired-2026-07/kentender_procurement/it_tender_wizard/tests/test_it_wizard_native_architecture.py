# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Structural guards for IT Wizard native Frappe Desk architecture."""

from __future__ import annotations

import os
import re

import frappe
from frappe.tests import UnitTestCase


def _public_path(*parts: str) -> str:
	return os.path.join(frappe.get_app_path("kentender_procurement"), "public", *parts)


def _read(path: str) -> str:
	return open(path, encoding="utf-8").read()


class TestItWizardNativeArchitecture(UnitTestCase):
	def test_hooks_include_shared_native_css(self) -> None:
		from kentender_procurement.hooks import app_include_css

		self.assertTrue(any("kt_it_wizard.css" in entry for entry in app_include_css))

	def test_hooks_include_shared_native_js_modules(self) -> None:
		from kentender_procurement.hooks import app_include_js

		joined = "\n".join(app_include_js)
		for module in (
			"it_wizard/it_wizard_api.js",
			"it_wizard/it_wizard_routes.js",
			"it_wizard/it_wizard_components.js",
			"it_wizard/it_wizard_shell.js",
		):
			self.assertIn(module, joined, module)

	def test_hooks_no_longer_include_overview_iframe_hydrator(self) -> None:
		from kentender_procurement.hooks import app_include_js

		joined = "\n".join(app_include_js)
		self.assertNotIn("it_wizard_overview.js", joined)

	def test_native_screen_registrars_do_not_mount_iframe(self) -> None:
		for name in (
			"it_wizard_dashboard_page.js",
			"it_wizard_overview_page.js",
			"it_wizard_it_requirements_page.js",
		):
			source = _read(_public_path("js", name))
			self.assertNotIn("mount_page", source, name)
			self.assertIn("frappe.require", source, name)
			self.assertIn("it_wizard/it_wizard_shell.js", source, name)

	def test_shared_js_tree_has_no_tailwind_cdn(self) -> None:
		js_root = _public_path("js", "it_wizard")
		for dirpath, _dirnames, filenames in os.walk(js_root):
			for filename in filenames:
				if not filename.endswith(".js"):
					continue
				source = open(os.path.join(dirpath, filename), encoding="utf-8").read()
				self.assertNotIn("cdn.tailwindcss.com", source, filename)

	def test_native_overview_css_does_not_hide_sidebar(self) -> None:
		css = _read(_public_path("css", "it_wizard_overview_page.css"))
		self.assertNotIn(".body-sidebar-container", css)

	def test_shared_css_documents_native_shell(self) -> None:
		css = _read(_public_path("css", "kt_it_wizard.css"))
		self.assertIn("body.it-wizard-native-shell", css)
		self.assertIn(".kt-itw-step-grid", css)
		import re as _re

		stripped = _re.sub(r"/\*.*?\*/", "", css, flags=_re.DOTALL)
		self.assertNotIn("http://", stripped)
		self.assertNotIn("https://", stripped)

	def test_dashboard_registrar_loads_screen_module(self) -> None:
		source = _read(_public_path("js", "it_wizard_dashboard_page.js"))
		self.assertIn("screens/dashboard.js", source)
		self.assertIn("kentender.it_wizard.screens.dashboard", source)

	def test_overview_registrar_loads_configuration_home_module(self) -> None:
		source = _read(_public_path("js", "it_wizard_overview_page.js"))
		self.assertIn("screens/configuration_home.js", source)
		self.assertIn("kentender.it_wizard.screens.configuration_home", source)

	def test_it_requirements_registrar_loads_native_screen_module(self) -> None:
		source = _read(_public_path("js", "it_wizard_it_requirements_page.js"))
		self.assertNotIn("mount_page", source)
		self.assertIn("screens/it_requirements.js", source)
		self.assertIn("kentender.it_wizard.screens.it_requirements", source)

	def test_deprecated_overview_hydrator_is_marked(self) -> None:
		source = _read(_public_path("js", "it_wizard_overview.js"))
		self.assertIn("@deprecated", source)
		self.assertIn("configuration_home.js", source)
