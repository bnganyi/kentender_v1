# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — Contract Terms tab layout guard (7. contract-terms/code structure)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _tab_renderers_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_tab_renderers.js"
	)


def _shared_ui_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_shared_ui.js"
	)


def _mockup_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_configurator_mockup.css"
	)


class TestStdConfigContractTermsLayoutGuard(UnitTestCase):
	def test_contract_terms_tab_markers_in_renderer(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		section = source.split('tabs["contract-terms"]')[1].split("tabs[")[0]
		for marker in (
			"ui.contractTermsTabDocument",
			"ui.contractTermsContextBanner",
			"ui.contractTermsGoverningFormPanel",
			"ui.contractTermsMatrixSection",
			"ui.contractTermsReadinessSection",
			"ui.termDetailDrawerBody",
			"term-detail-drawer",
			"data-kt-std-term-edit",
			"data-kt-std-add-term",
		):
			self.assertIn(marker, source, msg=marker)
		self.assertNotIn("ui.sectionCard", section)
		self.assertNotIn("ui.dataTable", section)

	def test_contract_terms_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"GOVERNING_CONTRACT_FORM_OPTIONS",
			"contractTermsTabDocument",
			"contractTermsContextBanner",
			"contractTermsGoverningFormPanel",
			"contractTermsMatrixSection",
			"contractTermsReadinessSection",
			"termDetailDrawerBody",
			'data-testid="kt-std-cfg-ct-matrix"',
			'data-testid="kt-std-cfg-ct-readiness"',
			"kt-std-cfg-ct-table",
			"kt-std-cfg-ct-term-row",
		):
			self.assertIn(marker, source, msg=marker)

	def test_contract_terms_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-ct-layout",
			".kt-std-cfg-ct-context",
			".kt-std-cfg-ct-governing",
			".kt-std-cfg-ct-matrix",
			".kt-std-cfg-ct-table",
			".kt-std-cfg-ct-term-row",
			".kt-std-cfg-ct-type",
			".kt-std-cfg-ct-readiness",
			".kt-std-cfg-ct-readiness-item",
			".kt-std-cfg-ct-issues",
		):
			self.assertIn(selector, source, msg=selector)
