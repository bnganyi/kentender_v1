# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — Applicability tab layout guard (3. applicability/code.html structure)."""

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


class TestStdConfigApplicabilityLayoutGuard(UnitTestCase):
	def test_applicability_tab_markers_in_renderer(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"ui.applicabilityTabDocument",
			"ui.navyBanner",
			"ui.conflictCheck",
			"ui.testApplicabilitySection",
			"ui.applicabilityLayout",
			"ui.applicabilityAppliesSection",
			"ui.fieldFundingCards",
			"ui.financialLimitsPanel",
			"ui.entityScopeBlock",
			'"contract_type"',
			'"works_subtype"',
			"entity_codes",
			"bindConflictCopy",
			"bindAppliesCopy",
		):
			self.assertIn(marker, source, msg=marker)
		self.assertNotIn('fieldText("funding_source"', source)

	def test_applicability_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"applicabilitySummaryLine",
			'data-testid="kt-std-cfg-applicability-banner-title"',
			"applicabilityTabDocument",
			"testApplicabilitySection",
			"applicabilityLayout",
			"applicabilityAppliesSection",
			"fieldFundingCards",
			"financialLimitsPanel",
			"entityScopeBlock",
			"bindConflictCopy",
			"CONTRACT_TYPE_OPTIONS",
			"WORKS_SUBTYPE_OPTIONS",
			"data-testid=\"kt-std-cfg-conflict-copy\"",
			"data-testid=\"kt-std-cfg-entity-picker\"",
			"data-testid=\"kt-std-cfg-applicability-applies-preview\"",
			'data-testid="kt-std-cfg-applicability"',
			"kt-std-cfg-tab-stack",
			"kt-std-cfg-lot-toggle",
		):
			self.assertIn(marker, source, msg=marker)

	def test_applicability_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-tab-stack",
			".kt-std-cfg-applicability-layout",
			".kt-std-cfg-navy-banner__body",
			".kt-std-cfg-test-section",
			".kt-std-cfg-funding-cards",
			".kt-std-cfg-entity-picker",
			".kt-std-cfg-financial-readout",
			".kt-std-cfg-lot-toggle",
			".kt-std-cfg-applies-panel",
			".kt-std-cfg-test-run-link",
		):
			self.assertIn(selector, source, msg=selector)
