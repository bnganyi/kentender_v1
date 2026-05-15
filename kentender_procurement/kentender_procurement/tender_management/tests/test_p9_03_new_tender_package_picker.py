# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-03 — ``list_packages_for_new_tender`` package picker API (doc 9 §14.5 / §15.1).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_03_new_tender_package_picker
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import list_packages_for_new_tender
from kentender_procurement.tender_management.services.tm2_workbench_package_picker import (
	list_packages_for_new_tender as list_packages_for_new_tender_service,
)


class TestP903NewTenderPackagePicker(IntegrationTestCase):
	def test_p9_03_service_returns_packages_shape(self) -> None:
		frappe.set_user("Administrator")
		out = list_packages_for_new_tender_service("Administrator", None, limit=5)
		self.assertTrue(out.get("ok"))
		self.assertIsInstance(out.get("packages"), list)
		for row in out["packages"]:
			self.assertIn("package_code", row)
			self.assertIn("selectable", row)
			self.assertIn("status", row)
			if row.get("selectable"):
				self.assertIn("requires_std_wizard_choice", row)

	def test_p9_03_whitelist_matches_session_user(self) -> None:
		frappe.set_user("Administrator")
		api_out = list_packages_for_new_tender()
		svc_out = list_packages_for_new_tender_service("Administrator", None, limit=50)
		self.assertEqual(api_out.get("ok"), svc_out.get("ok"))
		self.assertEqual(len(api_out.get("packages") or []), len(svc_out.get("packages") or []))
