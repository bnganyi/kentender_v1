# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""D3 — ``get_pp_package_detail`` API smoke tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_detail import get_pp_package_detail


class TestPpPackageDetailApi(IntegrationTestCase):
	def test_guest_access_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_package_detail(package="some-nonexistent-id")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_empty_package_not_found(self) -> None:
		frappe.set_user("Administrator")
		out = get_pp_package_detail(package="")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_missing_package_not_found(self) -> None:
		frappe.set_user("Administrator")
		out = get_pp_package_detail(package="__no_such_procurement_package__")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")
