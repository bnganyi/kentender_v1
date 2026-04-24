# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase E1 — Procurement Planning permissions smoke tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.permissions import pp_policy
from kentender_procurement.procurement_planning.permissions import pp_record_permissions


class TestPpPermissionsE1(IntegrationTestCase):
	def test_guest_cannot_assert_apply_template(self) -> None:
		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, pp_policy.assert_may_apply_template_to_demands)

	def test_guest_plan_query_not_applied(self) -> None:
		"""Non-planning roles do not receive entity SQL (empty string)."""
		frappe.set_user("Guest")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			return
		sql = pp_record_permissions.get_permission_query_conditions_for_procurement_plan("Guest")
		self.assertEqual(sql, "")

	def test_administrator_plan_query_not_restricted(self) -> None:
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			return
		sql = pp_record_permissions.get_permission_query_conditions_for_procurement_plan("Administrator")
		self.assertEqual(sql, "")

	def test_package_detail_actions_officer_mark_ready_only_when_approved(self) -> None:
		from kentender_procurement.procurement_planning.api.package_detail import _actions_for_workbench

		a = _actions_for_workbench("Approved", "officer")
		self.assertFalse(a["edit"])
		self.assertTrue(a["mark_ready"])
		self.assertFalse(a["approve"])

		b = _actions_for_workbench("Draft", "authority")
		self.assertFalse(b["edit"])
		self.assertFalse(b["approve"])
