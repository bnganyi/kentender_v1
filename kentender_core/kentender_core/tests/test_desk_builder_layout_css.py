# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestDeskBuilderLayoutCss(IntegrationTestCase):
	def test_builder_layout_css_registered_on_desk_hooks(self):
		"""Ensures shared builder width CSS ships with kentender_core (desk `app_include_css`)."""
		found = False
		for row in frappe.get_hooks("app_include_css", default=[]):
			items = row if isinstance(row, (list, tuple)) else [row]
			for path in items:
				if path and "kentender_desk_builder_layout.css" in str(path):
					found = True
					break
			if found:
				break
		self.assertTrue(found, "kentender_desk_builder_layout.css must be in app_include_css")

	def test_builder_layout_css_includes_route_fallback_for_procurement_planning_workspace(self):
		"""Regression: width rules must not depend solely on late-set kt-*-shell body classes."""
		from pathlib import Path

		css_path = (
			Path(frappe.get_app_path("kentender_core"))
			/ "public"
			/ "css"
			/ "kentender_desk_builder_layout.css"
		)
		text = css_path.read_text(encoding="utf-8")
		self.assertIn('body[data-route="Workspaces/Procurement Planning"]', text)
		self.assertIn("kt-ktsm-shell", text)
