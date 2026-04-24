# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""D4 — ``package_line_edit`` API smoke tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_line_edit import (
	add_pp_package_line,
	get_pp_package_lines,
	list_pp_assignable_demands,
	remove_pp_package_line,
)


class TestPpPackageLineEditApi(IntegrationTestCase):
	def test_guest_list_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_package_lines(package="anything")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_guest_add_denied(self) -> None:
		frappe.set_user("Guest")
		out = add_pp_package_line(
			package="anything",
			demand_id="x",
			budget_line_id="y",
			amount=1,
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_list_missing_package(self) -> None:
		frappe.set_user("Administrator")
		out = get_pp_package_lines(package="__no_such_pkg__")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_add_missing_package(self) -> None:
		frappe.set_user("Administrator")
		out = add_pp_package_line(
			package="__no_such_pkg__",
			demand_id="x",
			budget_line_id="y",
			amount=100,
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")


	def test_guest_assignable_denied(self) -> None:
		frappe.set_user("Guest")
		out = list_pp_assignable_demands(package="anything")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_assignable_missing_package(self) -> None:
		frappe.set_user("Administrator")
		out = list_pp_assignable_demands(package="__no_such_pkg__")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_remove_missing_line(self) -> None:
		frappe.set_user("Administrator")
		out = remove_pp_package_line(line_name="__no_such_line__")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")
