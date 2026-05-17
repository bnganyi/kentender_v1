# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R6-005 / LV-R6-005-01 — Official STD Library shell keeps governance source copy.

Companion evidence:
docs/prompts/0. usability handoff/R6_005_std_admin_terminology_protection_evidence.md
"""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase


def _read_std_library_shell_js() -> str:
	path = os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"public/js/std_library/std_library_shell.js",
	)
	with open(path, encoding="utf-8") as f:
		return f.read()


class TestR6005StdAdminTerminologyProtection(IntegrationTestCase):
	def test_shell_js_retains_official_library_governance_strings(self):
		src = _read_std_library_shell_js()
		self.assertIn('__("Official STD Library")', src)
		self.assertIn(
			"Manage official standard tender documents available for tender preparation",
			src,
		)
		self.assertIn(
			"Official STDs are imported as structured packages",
			src,
		)
		self.assertIn("Active versions are immutable", src)
		self.assertIn('__("Import Official STD Package")', src)

	def test_shell_js_does_not_embed_business_readiness_component(self):
		"""Regression guard: R6 business readiness belongs on TM2 / package surfaces, not std-engine."""
		src = _read_std_library_shell_js()
		self.assertNotIn("plc-business-readiness-summary", src)
		self.assertNotIn("BusinessReadinessSummary", src)
		self.assertNotIn("Tender document readiness", src)
