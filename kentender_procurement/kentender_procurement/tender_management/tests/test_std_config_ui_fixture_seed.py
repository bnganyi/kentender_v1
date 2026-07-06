# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — UI fixture seed smoke."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.seed_std_config_ui_fixture import (
	FIXTURE_TEMPLATE_CODE,
	ensure_std_config_ui_fixture_template,
)
from kentender_procurement.tender_management.services import std_configurator_service as svc


class TestStdConfigUiFixtureSeed(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_ensure_fixture_template_populates_std_config(self) -> None:
		out = ensure_std_config_ui_fixture_template()
		self.assertTrue(out.get("ok"))
		self.assertTrue(frappe.db.exists("STD Template", FIXTURE_TEMPLATE_CODE))
		meta = svc.get_section(FIXTURE_TEMPLATE_CODE, "metadata")
		self.assertIn("Building Works", meta["data"].get("title", ""))
		fields = svc.get_section(FIXTURE_TEMPLATE_CODE, "tender_fields")
		self.assertGreaterEqual(len(fields["data"].get("fields") or []), 1)

	def tearDown(self) -> None:
		frappe.set_user("Administrator")