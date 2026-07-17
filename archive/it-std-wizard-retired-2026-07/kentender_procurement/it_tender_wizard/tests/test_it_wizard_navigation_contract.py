# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-NAV-001/002 — Canonical access paths for IT Wizard dashboard."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_instance_service import create_configuration
from kentender_procurement.it_tender_wizard.tests.std_test_fixtures import (
	ensure_canonical_it_std_active_for_tests,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID


def _procurement_sidebar_export_path() -> str:
	return os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"workspace_sidebar",
		"procurement.json",
	)


def _configuration_section_items(data: dict) -> list[dict]:
	items = data.get("items") or []
	start = next((i for i, row in enumerate(items) if row.get("label") == "Configuration"), None)
	if start is None:
		return []
	end = next(
		(
			i
			for i, row in enumerate(items[start + 1 :], start + 1)
			if row.get("type") == "Section Break"
		),
		len(items),
	)
	return items[start:end]


class TestItWizardNavigationContract(UnitTestCase):
	def test_std_library_subtree_has_no_it_wizard_link(self) -> None:
		with open(_procurement_sidebar_export_path(), encoding="utf-8") as handle:
			data = json.load(handle)
		section_items = _configuration_section_items(data)
		wizard_links = [
			row
			for row in section_items
			if row.get("type") == "Link"
			and (
				"wizard" in (row.get("label") or "").lower()
				or (row.get("link_to") or "").startswith("it-tender")
			)
		]
		self.assertEqual(wizard_links, [])

	def test_std_prod_engine_has_no_launch_it_wizard_cta(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"std_prod_engine.js",
		)
		source = open(path, encoding="utf-8").read().lower()
		self.assertNotIn("it-tender-configuration-dashboard", source)
		self.assertNotIn("launch_it_std_configuration", source)

	def test_tm_workbench_exports_launch_handoff(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"tender_management_v2_workbench_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("launch_it_std_configuration", source)
		self.assertIn("it-tender-configuration-dashboard", source)
		self.assertIn("tm2-launch-it-std-configuration", source)

	def test_it_wizard_engine_reads_route_context(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("read_route_context", source)
		self.assertIn("tender_id", source)
		self.assertIn("std_version_id", source)
		self.assertIn("plan_item_id", source)
		self.assertIn("configuration_id", source)

	def test_it_wizard_engine_registers_overview_route(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("ITW_REGISTERED_ROUTES", source)
		self.assertIn("it-tender-configuration-overview", source)
		self.assertIn("it-tender-configuration-tender-profile", source)
		self.assertIn("it-tender-configuration-tds", source)
		self.assertIn("it-tender-configuration-it-requirements", source)
		self.assertIn("it-tender-configuration-system-inventory", source)
		self.assertIn("navigate", source)
		self.assertIn("it-tender-configuration-overview", source)
		self.assertIn("STEP_ROUTE_MAP", source)
		self.assertIn('TDS: "it-tender-configuration-tds"', source)
		self.assertIn('IT_REQUIREMENTS: "it-tender-configuration-it-requirements"', source)
		self.assertIn('IMPLEMENTATION_SCHEDULE: "it-tender-configuration-implementation-schedule"', source)
		self.assertIn('SYSTEM_INVENTORY: "it-tender-configuration-system-inventory"', source)
		self.assertIn("sync_configuration_id_to_url", source)
		self.assertIn("clear_configuration_id_from_url", source)


class TestItWizardNavigationContractSite(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		ensure_canonical_it_std_active_for_tests()

	def test_create_from_planning_context_sets_initiation_source(self) -> None:
		result = create_configuration(
			{
				"std_template_version_id": CANONICAL_PACKAGE_ID,
				"title": "Planning Handoff Config",
				"tender_id": "TND-HANDOFF-001",
				"procurement_plan_item_id": "PPI-HANDOFF-001",
			}
		)
		summary = result["summary"]
		self.assertEqual(summary["initiation_source"], ws.INITIATION_PLANNING)
		code = summary["configuration_id"]
		docname = frappe.db.get_value("Tender STD Instance", {"instance_code": code})
		self.assertTrue(docname)
		frappe.delete_doc("Tender STD Instance", docname, force=1)
