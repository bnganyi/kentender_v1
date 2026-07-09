# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Source Document & Traceability screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdSourceDocLayoutGuard(UnitTestCase):
	"""Deployed std_source_doc.html must match ui/4. source-doc/code.html verbatim."""

	def test_deployed_source_doc_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("04. source-doc"),
			deployed_asset_path("std_source_doc.html"),
		)

	def test_source_doc_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_source_doc.html"))
		self.assertIn(
			"<title>Source Document &amp; Traceability | KenTender STD Engine</title>",
			deployed,
		)
		self.assertIn("KE-PPRA-IT-2024-01 — Source Documents &amp; Traceability", deployed)
		self.assertIn("Source Document Summary", deployed)
		self.assertIn("Official Source Files", deployed)
		self.assertIn("Traceability Anchor Map", deployed)

	def test_source_doc_preserves_button_interaction_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_source_doc.html"))
		self.assertIn("btn.addEventListener('mousedown'", deployed)
		self.assertIn("opacity-80", deployed)
