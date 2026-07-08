# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — legacy package → std_config projection tests."""

from __future__ import annotations

from types import SimpleNamespace

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.tender_management.services.std_config_legacy_projection import (
	effective_std_config_section,
	legacy_package_available,
	project_legacy_std_config,
	section_is_populated,
)
from kentender_procurement.tender_management.services.std_configurator_service import get_section
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	load_template_package,
)


class TestStdConfigLegacyProjectionUnit(UnitTestCase):
	def test_legacy_package_detection(self) -> None:
		package = load_template_package()
		self.assertTrue(legacy_package_available(package))

	def test_project_legacy_std_config_populates_core_sections(self) -> None:
		package = load_template_package()
		doc = SimpleNamespace(template_code=TEMPLATE_CODE, template_title="", lifecycle_status="Active")
		projected = project_legacy_std_config(package, doc)
		self.assertTrue(section_is_populated("metadata", projected.get("metadata")))
		self.assertIn("Building", projected["metadata"]["title"])
		self.assertGreaterEqual(len(projected.get("tender_fields", {}).get("fields") or []), 10)
		self.assertGreaterEqual(len(projected.get("supplier_requirements", {}).get("requirements") or []), 5)
		self.assertGreaterEqual(len(projected.get("forms_and_attachments", {}).get("forms") or []), 5)
		self.assertGreaterEqual(len(projected.get("rules", {}).get("rules") or []), 1)
		self.assertGreaterEqual(len(projected.get("contract_terms", {}).get("terms") or []), 1)


class TestStdConfigLegacyProjectionIntegration(IntegrationTestCase):
	def test_works_poc_get_section_returns_projected_metadata(self) -> None:
		if not frappe.db.exists("STD Template", TEMPLATE_CODE):
			self.skipTest("WORKS POC template not seeded")
		out = get_section(TEMPLATE_CODE, "metadata")
		self.assertTrue(out.get("ok"))
		data = out.get("data") or {}
		self.assertIn("Building", data.get("title") or "")
		self.assertTrue(data.get("procurement_category"))

	def test_works_poc_get_section_returns_projected_tender_fields(self) -> None:
		if not frappe.db.exists("STD Template", TEMPLATE_CODE):
			self.skipTest("WORKS POC template not seeded")
		out = get_section(TEMPLATE_CODE, "tender_fields")
		fields = (out.get("data") or {}).get("fields") or []
		self.assertGreaterEqual(len(fields), 10)
		self.assertTrue(any("TENDER" in str(f.get("code") or "") for f in fields))

	def test_effective_section_prefers_stored_std_config_when_populated(self) -> None:
		package = load_template_package()
		package["std_config"] = {
			"metadata": {
				"title": "Stored Title Override",
				"short_title": "X",
				"description": "Y",
				"authority": "PPRA",
				"document_family": "Works",
				"procurement_category": "Works",
				"procurement_method": "Open Tender",
				"version_label": "1",
				"effective_date": "",
				"owner": "",
				"status": "Draft",
				"change_summary": "",
				"funding_sources": {
					"gok_exchequer": False,
					"internal_revenue": False,
					"donor_funded": False,
					"mixed_funding": False,
				},
			}
		}
		data = effective_std_config_section(package, "metadata")
		self.assertEqual(data.get("title"), "Stored Title Override")
