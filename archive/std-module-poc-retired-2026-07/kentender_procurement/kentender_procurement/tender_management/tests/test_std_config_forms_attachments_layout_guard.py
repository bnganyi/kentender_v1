# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — Forms & Attachments tab layout guard (5. forms/code.html structure)."""

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


class TestStdConfigFormsAttachmentsLayoutGuard(UnitTestCase):
	def test_forms_attachments_tab_markers_in_renderer(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		section = source.split('tabs["forms-attachments"]')[1].split("tabs[")[0]
		for marker in (
			"ui.formsAttachmentsTabDocument",
			"ui.formsAttachmentsDocumentsSection",
			"ui.formsAttachmentsSupplierFormsSection",
			"ui.formsAttachmentsInfoRow",
			"ui.documentDetailDrawerBody",
			"document-detail-drawer",
			"data-kt-std-document-edit",
			"data-kt-std-fa-preview-mode",
		):
			self.assertIn(marker, source, msg=marker)
		self.assertNotIn("ui.dataTable", section)
		self.assertNotIn("ui.sectionCard", section)

	def test_forms_attachments_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"FORMS_PREVIEW_MODES",
			"formsAttachmentsTabDocument",
			"formsAttachmentsDocumentsSection",
			"formsAttachmentsSupplierFormsSection",
			"formsAttachmentsInfoRow",
			"documentDetailDrawerBody",
			'data-testid="kt-std-cfg-forms-documents"',
			'data-testid="kt-std-cfg-forms-supplier-forms"',
			'data-testid="kt-std-cfg-fa-info-row"',
			"kt-std-cfg-fa-table",
			"kt-std-cfg-fa-doc-row",
			"kt-std-cfg-fa-supplier-card",
		):
			self.assertIn(marker, source, msg=marker)

	def test_forms_attachments_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-fa-layout",
			".kt-std-cfg-fa-documents",
			".kt-std-cfg-fa-section-head",
			".kt-std-cfg-fa-preview-bar",
			".kt-std-cfg-fa-table",
			".kt-std-cfg-fa-doc-row",
			".kt-std-cfg-fa-supplier-forms",
			".kt-std-cfg-fa-supplier-grid",
			".kt-std-cfg-fa-supplier-card",
			".kt-std-cfg-fa-info-row",
			".kt-std-cfg-fa-info-card",
			".kt-std-cfg-fa-status",
		):
			self.assertIn(selector, source, msg=selector)
