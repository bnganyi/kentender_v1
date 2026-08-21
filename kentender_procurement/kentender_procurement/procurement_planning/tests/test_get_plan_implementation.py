# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-015 / PLN-UI-09 — get_plan_implementation read DTO."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import (
	TAKEUP_NOT_TAKEN,
	VERSION_APPROVED,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_implementation import (
	get_plan_implementation,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_VIEWER,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	approve_plan_via_gate05,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	PE_MOH,
	ensure_user_with_roles,
)


class TestGetPlanImplementation(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_draft_plan_is_not_an_implementation_surface(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3100, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Draft not approved overview", financial_year=fy)
		with self.assertRaises(frappe.ValidationError):
			get_plan_implementation(plan=plan["plan"], user=planner)

	def test_approved_dto_without_handoff_or_publication(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3100, bucket=1)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Approved overview", financial_year=fy)
		d = make_approved_demand(title="Approved overview demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		dto = get_plan_implementation(plan=plan["plan"], user=planner)
		self.assertTrue(dto["ok"], dto)
		self.assertEqual(dto["version_status"], VERSION_APPROVED)
		self.assertIn("add_demand", dto["actions"])
		self.assertNotIn("export", dto["actions"])
		self.assertTrue(dto["items"])
		self.assertEqual(dto["items"][0]["takeup_label"], TAKEUP_NOT_TAKEN)
		self.assertNotIn("progress_label", dto["items"][0])
		self.assertEqual(dto["items"][0]["variance_label"], "—")
		self.assertNotIn("on_schedule_label", dto)
		self.assertFalse(dto["has_downstream_actuals"])
		self.assertIn("propose_removal", dto["items"][0]["actions"])
		self.assertIn("procurement-plan-approved", dto["items"][0]["actions"]["view"]["route"])
		self.assertNotIn("procurement-plan-item-editor", dto["items"][0]["actions"]["view"]["route"])
		self.assertNotIn("publication", dto)
		self.assertFalse(dto["has_successor"])
		self.assertIn("procurement-plan-approved", dto["approved_route"])
		self.assertNotIn("continue_update", dto["actions"])

	def test_successor_notice_after_add_to_approved(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3100, bucket=2)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Successor notice", financial_year=fy)
		d1 = make_approved_demand(title="Successor base demand")
		add_demand_to_plan(plan=plan["plan"], demand=d1["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		d2 = make_approved_demand(
			title="Successor extra demand",
			required_by_date=frappe.db.get_value(
				"Procurement Plan", plan["plan"], "period_start"
			),
		)
		add_demand_to_plan(plan=plan["plan"], demand=d2["demand"], user=planner)
		dto = get_plan_implementation(plan=plan["plan"], user=planner)
		self.assertTrue(dto["has_successor"])
		self.assertIn("Draft Version", dto["successor_label"])
		self.assertIn("add_demand", dto["actions"])
		self.assertIn("procurement-plan-builder", dto["actions"]["continue_update"]["route"])
		self.assertNotIn("procurement-plan-update", dto["actions"]["continue_update"]["route"])

	def test_viewer_cannot_add_or_propose(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3100, bucket=3)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Viewer overview", financial_year=fy)
		d = make_approved_demand(title="Viewer overview demand")
		add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		viewer = ensure_user_with_roles(
			"pln.ui09.viewer@test.local",
			roles=(ROLE_VIEWER,),
			pe=PE_MOH,
			org_unit=None,
			include_descendants=0,
		)
		dto = get_plan_implementation(plan=plan["plan"], user=viewer)
		self.assertTrue(dto["ok"], dto)
		self.assertNotIn("add_demand", dto["actions"])
		self.assertNotIn("export", dto["actions"])
		self.assertTrue(dto["items"])
		self.assertNotIn("propose_removal", dto["items"][0]["actions"])
		self.assertIn("view", dto["items"][0]["actions"])
