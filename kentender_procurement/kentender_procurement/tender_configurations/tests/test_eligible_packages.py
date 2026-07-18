# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Eligible package list — excludes configured packages; requires ACTIVE STD."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_configurations import get_eligible_procurement_packages
from kentender_procurement.tender_configurations.seed.ui00_seed import (
	clear_ui00_seed,
	seed_ui00_dashboard,
)
from kentender_procurement.tender_configurations.services.create_configuration import (
	create_tender_configuration,
)


class TestEligiblePackages(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		clear_ui00_seed()
		cls.seed = seed_ui00_dashboard(clear=True)

	@classmethod
	def tearDownClass(cls) -> None:
		clear_ui00_seed()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)

	def test_lists_ready_packages_only(self) -> None:
		out = get_eligible_procurement_packages()
		refs = {p["planning_package_ref"] for p in out["packages"]}
		self.assertIn("TCFG-SEED-PKG-READY-001", refs)
		self.assertIn("TCFG-SEED-PKG-READY-002", refs)
		# Packages already linked to active configs must not appear
		self.assertNotIn("TCFG-SEED-PKG-CFG-IP", refs)
		self.assertNotIn("TCFG-SEED-PKG-CFG-NA", refs)

	def test_create_removes_from_eligible(self) -> None:
		pkg = self.seed["ready_packages"][0]
		before = {p["package_id"] for p in get_eligible_procurement_packages()["packages"]}
		self.assertIn(pkg, before)
		create_tender_configuration(package_id=pkg)
		after = {p["package_id"] for p in get_eligible_procurement_packages()["packages"]}
		self.assertNotIn(pkg, after)

	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_eligible_procurement_packages()
