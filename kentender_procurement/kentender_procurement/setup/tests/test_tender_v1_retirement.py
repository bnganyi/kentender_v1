# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.setup.tender_v1_retirement import wipe_tender_v1_desk_artifacts


class TestTenderV1Retirement(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_wipe_tender_v1_desk_artifacts_runs_twice_without_error(self):
		wipe_tender_v1_desk_artifacts()
		wipe_tender_v1_desk_artifacts()
