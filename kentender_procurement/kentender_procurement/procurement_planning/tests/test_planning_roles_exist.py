# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-PERM-001 — Planning roles exist and DocType permission matrix covers them."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import MVP1_DOCTYPES
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ALL_PLANNING_ROLES,
	ROLE_DESIGNATED_APPROVER,
	ROLE_PLANNER,
	ensure_planning_roles,
)


class TestPlanningRolesExist(IntegrationTestCase):
	def test_ensure_planning_roles_creates_all(self) -> None:
		ensure_planning_roles()
		for role in ALL_PLANNING_ROLES:
			self.assertTrue(frappe.db.exists("Role", role), msg=role)
			desk = frappe.db.get_value("Role", role, "desk_access")
			self.assertEqual(int(desk or 0), 1, msg=role)

	def test_doctype_permissions_include_planning_roles(self) -> None:
		ensure_planning_roles()
		for dt in MVP1_DOCTYPES:
			meta = frappe.get_meta(dt)
			roles = {p.role for p in meta.permissions}
			self.assertIn("System Manager", roles, msg=dt)
			self.assertIn(ROLE_PLANNER, roles, msg=dt)
			self.assertIn(ROLE_DESIGNATED_APPROVER, roles, msg=dt)
			self.assertIn("Planning Viewer", roles, msg=dt)

	def test_designated_approver_no_write_on_items(self) -> None:
		ensure_planning_roles()
		for dt in (
			"Procurement Plan Item",
			"Procurement Plan Item Version",
			"Plan Demand Allocation",
		):
			meta = frappe.get_meta(dt)
			da = next(p for p in meta.permissions if p.role == ROLE_DESIGNATED_APPROVER)
			self.assertEqual(int(da.write or 0), 0, msg=dt)
			self.assertEqual(int(da.create or 0), 0, msg=dt)
			self.assertEqual(int(da.read or 0), 1, msg=dt)
