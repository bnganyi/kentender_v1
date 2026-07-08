# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — harmonized auxiliary tabs layout guard (rules, preview, approval, evidence, technical JSON)."""

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


class TestStdConfigAuxTabsLayoutGuard(UnitTestCase):
	def _tab_section(self, source: str, tab_key: str) -> str:
		for opener in (f'tabs["{tab_key}"]', f"tabs.{tab_key}"):
			if opener in source:
				return source.split(opener)[1].split("tabs[")[0].split("tabs.")[0]
		self.fail(f"Tab section not found: {tab_key}")

	def test_aux_tabs_use_tab_document_helpers_not_legacy_cards(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		tab_specs = (
			("rules-validations", "ui.rulesValidationsTabDocument", "kt-std-cfg-tab-stack"),
			("preview", "ui.previewTabDocument", "kt-std-cfg-tab-stack"),
			("approval", "ui.approvalTabDocument", "kt-std-cfg-tab-stack"),
			("evidence", "ui.evidenceTabDocument", "kt-std-cfg-tab-stack"),
			("technical-json", "ui.technicalJsonTabDocument", "kt-std-cfg-tab-stack"),
		)
		for tab_key, doc_helper, stack_class in tab_specs:
			section = self._tab_section(source, tab_key)
			self.assertIn(doc_helper, section, msg=tab_key)
			self.assertNotIn("ui.sectionCard", section, msg=tab_key)
			if tab_key == "evidence":
				self.assertNotIn("ui.dataTable", section, msg=tab_key)

	def test_aux_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"rulesValidationsTabDocument",
			"rulesValidationsRulesSection",
			"rulesValidationsValidationsSection",
			"previewTabDocument",
			"previewModeBar",
			"approvalTabDocument",
			"approvalGovernanceSection",
			"evidenceTabDocument",
			"evidenceInventorySection",
			"technicalJsonTabDocument",
			"auxSectionPanel",
			"auxReadonlyTable",
			'testid: "kt-std-cfg-rv-rules"',
			'data-testid="kt-std-cfg-preview-modes"',
			'testid: "kt-std-cfg-approval-governance"',
			'testid: "kt-std-cfg-evidence-inventory"',
			'testid: "kt-std-cfg-technical-json-panel"',
		):
			self.assertIn(marker, source, msg=marker)

	def test_aux_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-aux-layout",
			".kt-std-cfg-aux-panel",
			".kt-std-cfg-aux-rule-list",
			".kt-std-cfg-aux-preview-bar",
			".kt-std-cfg-aux-status-banner",
			".kt-std-cfg-aux-governance",
			".kt-std-cfg-aux-table",
			".kt-std-cfg-aux-code",
		):
			self.assertIn(selector, source, msg=selector)
