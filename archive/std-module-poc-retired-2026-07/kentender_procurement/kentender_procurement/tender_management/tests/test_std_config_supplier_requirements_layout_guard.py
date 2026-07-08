# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — Supplier Requirements tab layout guard (pack matrix contract)."""

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


class TestStdConfigSupplierRequirementsLayoutGuard(UnitTestCase):
	def test_supplier_requirements_tab_markers_in_renderer(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		section = source.split('tabs["supplier-requirements"]')[1].split("tabs[")[0]
		for marker in (
			"ui.supplierRequirementsTabDocument",
			"ui.supplierRequirementsMatrix",
			"ui.supplierRequirementsGuidanceRow",
			"ui.requirementDetailDrawerBody",
			"requirement-detail-drawer",
			"data-kt-std-requirement-edit",
			"data-kt-std-requirement-delete",
		):
			self.assertIn(marker, source, msg=marker)
		self.assertNotIn("ui.dataTable", section)
		self.assertNotIn("ui.sectionCard", section)

	def test_supplier_requirements_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"SUPPLIER_REQUIREMENT_TYPE_OPTIONS",
			"supplierRequirementsTabDocument",
			"supplierRequirementsActionBar",
			"supplierRequirementsMatrix",
			"supplierRequirementsGuidanceRow",
			"requirementDetailDrawerBody",
			'data-testid="kt-std-cfg-supplier-requirements-matrix"',
			'data-testid="kt-std-cfg-sr-guidance"',
			"data-kt-std-add-requirement",
			"data-kt-std-add-requirement-here",
			"kt-std-cfg-sr-table",
			"kt-std-cfg-sr-row",
		):
			self.assertIn(marker, source, msg=marker)

	def test_supplier_requirements_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-sr-layout",
			".kt-std-cfg-sr-matrix",
			".kt-std-cfg-sr-matrix__head",
			".kt-std-cfg-sr-table",
			".kt-std-cfg-sr-row",
			".kt-std-cfg-sr-guidance",
			".kt-std-cfg-sr-guidance-card",
			".kt-std-cfg-sr-type",
			".kt-std-cfg-sr-flag",
		):
			self.assertIn(selector, source, msg=selector)
