# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""create_tender_configuration — happy path and UI-M01 validation messages."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_configurations import create_tender_configuration
from kentender_procurement.tender_configurations.constants import STATUS_IN_PROGRESS, UI_01_ROUTE
from kentender_procurement.tender_configurations.seed.ui00_seed import (
	clear_ui00_seed,
	seed_ui00_dashboard,
)


class TestCreateTenderConfiguration(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = seed_ui00_dashboard(clear=True)

	@classmethod
	def tearDownClass(cls) -> None:
		clear_ui00_seed()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		# Ensure a fresh ready package each test that needs create
		self.seed = seed_ui00_dashboard(clear=True)

	def test_happy_path(self) -> None:
		pkg = self.seed["ready_packages"][0]
		out = create_tender_configuration(package_id=pkg)
		self.assertTrue(out["configuration_ref"].startswith("TCFG-"))
		self.assertEqual(out["std_family_key"], "IT")
		self.assertIn(UI_01_ROUTE, out["redirect_route"])
		self.assertIn(out["configuration_id"], out["redirect_route"])
		doc = frappe.get_doc("Tender Configuration", out["configuration_id"])
		self.assertEqual(doc.status, STATUS_IN_PROGRESS)
		self.assertEqual(doc.procurement_package, pkg)

	def test_already_configured(self) -> None:
		pkg = self.seed["ready_packages"][0]
		create_tender_configuration(package_id=pkg)
		with self.assertRaises(frappe.ValidationError) as ctx:
			create_tender_configuration(package_id=pkg)
		self.assertIn("already has a tender configuration", str(ctx.exception))

	def test_missing_package(self) -> None:
		with self.assertRaises(frappe.ValidationError) as ctx:
			create_tender_configuration(package_id="")
		self.assertIn("Select an approved procurement package", str(ctx.exception))

	def test_draft_package_rejected(self) -> None:
		pkg = self.seed["ready_packages"][1]
		frappe.db.set_value("Procurement Package", pkg, "status", "Draft")
		with self.assertRaises(frappe.ValidationError) as ctx:
			create_tender_configuration(package_id=pkg)
		self.assertIn("Only approved procurement packages", str(ctx.exception))

	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			create_tender_configuration(package_id=self.seed["ready_packages"][0])
