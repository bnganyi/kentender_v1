# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-PERM-002/003 — Admin deny, Planner create, approve role segregation."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_procurement_plan_for_test as create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_approve_plan,
	assert_can_create_plan,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	advance_draft_to_recommended,
	approve_plan_via_gate05,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	OU_MOH,
	PE_MOH,
	ensure_admin_only,
	ensure_moh_approver,
	ensure_moh_planner,
	ensure_org,
	ensure_user_with_roles,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)


class TestPlanningPermissionsMatrix(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def test_admin_only_cannot_create_plan(self) -> None:
		admin = ensure_admin_only()
		with self.assertRaises(frappe.PermissionError):
			create_procurement_plan(
				procuring_entity=PE_MOH,
				financial_year="2180/81",
				user=admin,
			)

	def test_admin_only_cannot_approve(self) -> None:
		admin = ensure_admin_only()
		with self.assertRaises(frappe.PermissionError):
			assert_can_approve_plan(admin)

	def test_planner_can_create(self) -> None:
		planner = ensure_moh_planner()
		assert_can_create_plan(planner)
		fy = unique_test_fy(base_year=2180, bucket=1)
		purge_pe_fy(fy)
		result = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=fy,
			user=planner,
		)
		self.assertTrue(result["ok"])

	def test_planner_cannot_final_approve(self) -> None:
		planner = ensure_moh_planner()
		with self.assertRaises(frappe.PermissionError):
			assert_can_approve_plan(planner)

		fy = unique_test_fy(base_year=2170, bucket=2)
		purge_pe_fy(fy)
		created = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=fy,
			user=planner,
		)
		demand = make_approved_demand(title="Planner approve deny demand")
		add_demand_to_plan(
			plan=created["plan"],
			demand=demand["demand"],
			user=planner,
		)
		advanced = advance_draft_to_recommended(
			plan=created["plan"], version=created["version"]
		)
		token = frappe.db.get_value(
			"Procurement Plan Version", advanced["version"], "concurrency_token"
		)
		with self.assertRaises(frappe.PermissionError):
			approve_plan_version(
				version=advanced["version"],
				concurrency_token=token,
				user=planner,
			)

	def test_designated_approver_can_approve(self) -> None:
		planner = ensure_moh_planner()
		approver = ensure_moh_approver()
		fy = unique_test_fy(base_year=2160, bucket=3)
		purge_pe_fy(fy)
		created = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=fy,
			user=planner,
		)
		demand = make_approved_demand(title="Approver OK demand")
		add_demand_to_plan(
			plan=created["plan"],
			demand=demand["demand"],
			user=planner,
		)
		result = approve_plan_via_gate05(
			plan=created["plan"], version=created["version"], user=approver
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["approved_by"], approver)

	def test_viewer_cannot_create(self) -> None:
		viewer = ensure_user_with_roles(
			"pln.gate02.viewer@test.local",
			roles=("Planning Viewer",),
			pe=PE_MOH,
			org_unit=None,
			include_descendants=0,
		)
		with self.assertRaises(frappe.PermissionError):
			assert_can_create_plan(viewer)
