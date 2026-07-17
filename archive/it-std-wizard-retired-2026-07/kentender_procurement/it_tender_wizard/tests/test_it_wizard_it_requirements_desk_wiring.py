# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-REQ-001/002 — Desk wiring for IT Requirements (native Screen 03)."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestItWizardItRequirementsDeskWiring(UnitTestCase):
	def test_hooks_register_it_requirements_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-it-requirements"),
			"public/js/it_wizard_it_requirements_page.js",
		)

	def test_it_requirements_page_js_uses_native_screen_module(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_it_requirements_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-it-requirements"]', source)
		self.assertIn("frappe.require", source)
		self.assertIn("screens/it_requirements.js", source)
		self.assertIn("kentender.it_wizard.screens.it_requirements", source)
		self.assertNotIn("mount_page", source)
		self.assertNotIn("it_wizard_it_requirements.html", source)

	def test_native_it_requirements_screen_module_wires_api(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard",
			"screens",
			"it_requirements.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("get_it_requirements_api", source)
		self.assertIn("save_it_requirements_api", source)
		self.assertIn('data-testid="it-wizard-it-requirements"', source)
		self.assertIn("data-itw-req-context", source)
		self.assertIn("data-itw-req-table-host", source)
		self.assertIn("data-itw-req-drawer", source)
		self.assertIn("data-itw-req-guidance", source)
		self.assertIn("data-itw-req-actions", source)
		self.assertIn("data-itw-field=", source)
		self.assertIn("Define what bidders must supply, deliver, integrate, support, or prove.", source)
		self.assertNotIn("Evidence Set", source)
		self.assertNotIn("Acceptance Set", source)
		self.assertNotIn("Edit in Evaluation Setup", source)

	def test_it_requirements_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_it_requirements_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-it-requirements-shell .page-head", source)
		self.assertIn("display: none !important", source)


class TestItWizardItRequirementsDeskWiringSite(IntegrationTestCase):
	def test_it_requirements_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-it-requirements"))
