# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Desk wiring tests for Civic Ledger shell POC page."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestKtClShellPocDeskWiring(UnitTestCase):
	def test_hooks_register_poc_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("kt-cl-shell-poc"),
			"public/js/kt_cl_shell_poc_page.js",
		)

	def test_poc_page_js_uses_cl_shell(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"kt_cl_shell_poc_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["kt-cl-shell-poc"]', source)
		self.assertIn("kentender_core.cl_shell.enter", source)
		self.assertIn("kentender_core.cl_shell.mountPageChrome", source)
		self.assertIn("Procurement Home", source)
		self.assertIn("Export APP", source)
		self.assertIn("Submit Draft", source)
		# Content area is composed from the kentender_core.cl component library
		# (no hand-rolled markup), and supplies the curated mock IA.
		for call in ("comp.kpiCard", "comp.calendarWidget", "comp.dataTable", "civicLedgerIA"):
			self.assertIn(call, source)

	def test_poc_page_fixture_exists(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"kentender_procurement",
			"page",
			"kt_cl_shell_poc",
			"kt_cl_shell_poc.json",
		)
		self.assertTrue(os.path.isfile(path), path)


class TestKtClShellPocPageDoc(IntegrationTestCase):
	def test_poc_page_synced_on_site(self) -> None:
		if not frappe.db.exists("Page", "kt-cl-shell-poc"):
			self.skipTest("Page kt-cl-shell-poc not synced — run bench migrate")
		doc = frappe.get_doc("Page", "kt-cl-shell-poc")
		self.assertEqual(doc.title, "Civic Ledger Shell POC")
		self.assertEqual(doc.module, "Kentender Procurement")
