# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared base case for the Tender Preparation service tests (plan D15)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_preparation.tests import fixtures as fx


class TenderCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_full_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_all()
		fx.ensure_link_targets()
		self.addCleanup(frappe.set_user, "Administrator")
