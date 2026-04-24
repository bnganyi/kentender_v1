# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""D2 — ``get_pp_package_list`` API smoke tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_list import get_pp_package_list


class TestPpPackageListApi(IntegrationTestCase):
	def test_invalid_queue_returns_error(self) -> None:
		frappe.set_user("Administrator")
		out = get_pp_package_list(plan=None, queue_id="not-a-real-queue-id")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "INVALID_QUEUE")

	def test_all_packages_queue_accepted(self) -> None:
		frappe.set_user("Administrator")
		out = get_pp_package_list(plan=None, queue_id="all_packages")
		if not out.get("ok"):
			self.assertIn(
				out.get("error_code"),
				("PP_ACCESS_DENIED", "NO_PACKAGE_PERMISSION"),
			)
			return
		self.assertEqual(out.get("queue_id"), "all_packages")
		self.assertIsInstance(out.get("rows"), list)

	def test_guest_access_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_package_list(plan=None, queue_id="draft_packages")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")
