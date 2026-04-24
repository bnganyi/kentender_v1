# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""H3 — Parent plan must be Draft when inserting a package or changing plan_id (non-admin)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestProcurementPlanningH3PlanBootstrap(IntegrationTestCase):
	def test_new_package_rejected_when_parent_plan_not_draft(self) -> None:
		if not frappe.db.exists("DocType", "Procurement Plan"):
			return
		rows = frappe.get_all("Procurement Plan", fields=["name", "status"], limit=1)
		if not rows:
			return
		plan_name = rows[0].name
		orig_status = frappe.db.get_value("Procurement Plan", plan_name, "status")
		frappe.db.set_value("Procurement Plan", plan_name, "status", "Submitted", update_modified=False)
		frappe.db.commit()
		try:
			frappe.set_user("Administrator")
			# Bypass privilege: admin can still attach — use a non-admin if available
			planners = frappe.get_all(
				"Has Role",
				filters={"role": "Procurement Planner", "parenttype": "User"},
				pluck="parent",
				limit=1,
			)
			test_user = planners[0] if planners else None
			if not test_user:
				return
			frappe.set_user(test_user)
			pkg = frappe.new_doc("Procurement Package")
			pkg.plan_id = plan_name
			pkg.package_name = "H3 bootstrap test row"
			with self.assertRaises(frappe.ValidationError):
				pkg.insert(ignore_permissions=True)
		finally:
			frappe.set_user("Administrator")
			frappe.db.set_value("Procurement Plan", plan_name, "status", orig_status, update_modified=False)
			frappe.db.commit()
