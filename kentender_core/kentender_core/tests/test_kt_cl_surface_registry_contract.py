# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract: kt_cl_surface_registry.js keeps the resolver and registers no retired surface.

The registry's only surfaces were the 19 screens of the legacy tender-configuration wizard
and its publication pages. That module was retired completely (RG-04 / RG-05 / AUD-XC-143),
so the registry is empty; the router still resolves routes through it.
"""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase


def _registry_source() -> str:
	return (
		Path(frappe.get_app_path("kentender_core"))
		/ "public"
		/ "js"
		/ "kt_cl_surface_registry.js"
	).read_text(encoding="utf-8")


class TestKtClSurfaceRegistryContract(IntegrationTestCase):
	def test_resolver_api_is_kept(self) -> None:
		source = _registry_source()
		for member in ("resolveFromRoute", "allIds", "get: function", "surfaces"):
			self.assertIn(member, source)

	def test_no_wizard_or_publication_surface_is_registered(self) -> None:
		source = _registry_source()
		self.assertNotRegex(source, r'"(UI|CFG|WF|PUB)-[A-Z0-9]+"\s*:')
		for route in ("it-tender-configuration", "it-tender-package-review", "publication-setup"):
			self.assertNotIn(route, source)
		self.assertNotIn('routePrefixes: ["publications"]', source)

	def test_registered_surfaces_are_none(self) -> None:
		source = _registry_source()
		body = re.search(r"var surfaces = \{(?P<body>.*?)\n\t\};", source, re.DOTALL)
		self.assertIsNotNone(body, msg="surfaces map not found")
		# only comments may live inside the map
		code = re.sub(r"/\*.*?\*/", "", body.group("body"), flags=re.DOTALL)
		code = re.sub(r"//[^\n]*", "", code)
		self.assertEqual(code.strip(), "")

	def test_retired_page_scripts_are_not_wired(self) -> None:
		page_js = frappe.get_hooks("page_js", app_name="kentender_procurement", default={})
		for route in page_js:
			self.assertFalse(str(route).startswith("it-tender-"), route)
		for route in ("publications", "publication-setup", "it-std-wizard-retired"):
			self.assertNotIn(route, page_js)
