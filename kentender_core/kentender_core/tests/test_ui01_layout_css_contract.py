# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static guard: UI-01 layout pins that Bootstrap/Tailwind must not erode."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase


def _read(rel: str) -> str:
	root = Path(frappe.get_app_path("kentender_core"))
	return (root / rel).read_text(encoding="utf-8")


class TestUi01LayoutCssContract(FrappeTestCase):
	def test_next_action_pinned_row_nowrap(self):
		css = _read("public/css/kt_cl_code_layout.css")
		self.assertIn('[data-testid="kt-cl-ui01-next-action"]', css)
		self.assertIn("flex-wrap: nowrap", css)
		self.assertIn("flex-direction: row", css)
		self.assertIn("white-space: nowrap", css)

		import re

		spec = _read("public/js/kt_cl_code_spec.js")
		m = re.search(r'nextAction:\s*"([^"]+)"', spec)
		self.assertIsNotNone(m, msg="CONFIG_HOME.nextAction missing")
		self.assertNotIn("flex-col", m.group(1))
		self.assertIn("flex-nowrap", m.group(1))

	def test_handoff_header_pin_present(self):
		css = _read("public/css/kt_cl_code_layout.css")
		self.assertIn('[data-testid="kt-cl-ui01-handoff-header"]', css)
		self.assertIn("kt-cl-ui01-handoff-header-icon", css)
		comp = _read("public/js/kt_cl_components.js")
		self.assertIn('data-testid="kt-cl-ui01-handoff-header"', comp)
		self.assertIn("kt-cl-ui01-handoff-header-icon", comp)

	def test_context_strip_is_eight_cells(self):
		css = _read("public/css/kt_cl_code_layout.css")
		self.assertIn("repeat(8, minmax(0, 1fr))", css)
		comp = _read("public/js/kt_cl_components.js")
		self.assertIn('key: "std_document"', comp)
		self.assertIn("standard_tender_document_label", comp)
		self.assertIn("Standard Tender Document", comp)
		self.assertIn("Configuration Status", comp)
		self.assertIn("Procurement Method", comp)

	def test_trail_leaf_is_configuration_home(self):
		reg = _read("public/js/kt_cl_surface_registry.js")
		self.assertIn("trailUi01Home", reg)
		self.assertIn("Tender Configuration Home", reg)
