# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — Tender Fields tab layout guard (4. tender-fields/code.html structure)."""

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


class TestStdConfigTenderFieldsLayoutGuard(UnitTestCase):
	def test_tender_fields_tab_markers_in_renderer(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"ui.tenderFieldsTabDocument",
			"ui.tenderFieldsMatrix",
			"ui.tenderFieldsGuidanceRow",
			"ui.fieldDetailDrawerBody",
			"field-detail-drawer",
			"data-kt-std-clone-template",
			"data-kt-std-field-edit",
		):
			self.assertIn(marker, source, msg=marker)
		self.assertNotIn("ui.groupTable", source.split('tabs["tender-fields"]')[1].split("tabs[")[0])

	def test_tender_fields_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"TENDER_FIELD_GROUPS",
			"tenderFieldsTabDocument",
			"tenderFieldsActionBar",
			"tenderFieldsMatrix",
			"tenderFieldsGuidanceRow",
			"fieldDetailDrawerBody",
			'data-testid="kt-std-cfg-tender-fields-matrix"',
			'data-testid="kt-std-cfg-tf-guidance"',
			"kt-std-cfg-tf-group-row",
			"kt-std-cfg-field-type",
			"kt-std-cfg-req-badge",
		):
			self.assertIn(marker, source, msg=marker)

	def test_tender_fields_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-tf-layout",
			".kt-std-cfg-tf-matrix",
			".kt-std-cfg-tf-matrix__head",
			".kt-std-cfg-tf-table",
			".kt-std-cfg-tf-group-row",
			".kt-std-cfg-tf-field-row",
			".kt-std-cfg-tf-add-row",
			".kt-std-cfg-tf-guidance",
			".kt-std-cfg-tf-guidance-card",
			".kt-std-cfg-field-type",
			".kt-std-cfg-req-badge",
		):
			self.assertIn(selector, source, msg=selector)
