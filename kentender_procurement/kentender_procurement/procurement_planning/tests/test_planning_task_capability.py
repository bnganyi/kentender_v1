# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-GATE-C01 — record vs task vs mutation capability + Admin/PE hardening."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version,
)
from kentender_procurement.procurement_planning.services.create_procurement_plan import (
	create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.get_departmental_contribution import (
	get_departmental_contribution,
)
from kentender_procurement.procurement_planning.services.get_plan_review import (
	get_plan_review,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	ROLE_VIEWER,
	assert_can_approve_plan,
	assert_can_confirm_plan_funding,
	assert_can_create_plan,
	assert_can_open_finance_task,
	assert_can_open_review_task,
	assert_can_submit_for_review,
	resolve_pe_for_create,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	advance_draft_to_recommended,
	make_approved_demand,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	OU_MOH,
	PE_MOH,
	ensure_admin_only,
	ensure_county_planner,
	ensure_moh_approver,
	ensure_moh_planner,
	ensure_org,
	ensure_user_with_roles,
)


def _unique_fy(prefix: int = 2190) -> str:
	n = frappe.db.count("Procurement Plan")
	return f"{prefix + (n % 9)}/{str(n + 40)[-2:]}"


class TestPlanningTaskCapability(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def _in_review_plan(self, planner: str) -> dict[str, str]:
		created = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=_unique_fy(),
			title="C01 capability plan",
			currency="KES",
			coordinating_org_unit=OU_MOH,
			user=planner,
		)
		demand = make_approved_demand(title="C01 capability demand")
		add_demand_to_plan(plan=created["plan"], demand=demand["demand"], user=planner)
		advanced = advance_draft_to_recommended(
			plan=created["plan"], version=created["version"]
		)
		return {
			"plan": created["plan"],
			"version": advanced["version"],
			"reviewer": advanced["reviewer"],
		}

	def test_admin_without_usa_denied_create_submit_approve_review_task(self) -> None:
		admin = ensure_admin_only()
		with self.assertRaises(frappe.PermissionError):
			assert_can_create_plan(admin)
		with self.assertRaises(frappe.PermissionError):
			assert_can_submit_for_review(admin)
		with self.assertRaises(frappe.PermissionError):
			assert_can_approve_plan(admin)
		with self.assertRaises(frappe.PermissionError):
			assert_can_open_review_task(admin)
		with self.assertRaises(frappe.PermissionError):
			assert_can_open_finance_task(admin)
		with self.assertRaises(frappe.PermissionError):
			assert_can_confirm_plan_funding(admin)

		planner = ensure_moh_planner()
		ctx = self._in_review_plan(planner)
		with self.assertRaises(frappe.PermissionError):
			get_plan_review(plan=ctx["plan"], user=admin)

	def test_planner_workspace_ok_review_task_actions_denied(self) -> None:
		planner = ensure_moh_planner()
		assert_can_create_plan(planner)
		with self.assertRaises(frappe.PermissionError):
			assert_can_open_review_task(planner)
		with self.assertRaises(frappe.PermissionError):
			assert_can_approve_plan(planner)
		with self.assertRaises(frappe.PermissionError):
			assert_can_open_finance_task(planner)
		with self.assertRaises(frappe.PermissionError):
			assert_can_confirm_plan_funding(planner)

		ctx = self._in_review_plan(planner)
		dto = get_plan_review(plan=ctx["plan"], user=planner)
		self.assertEqual(dto["surface"], "neutral")
		self.assertFalse(dto["can_approve"])
		self.assertFalse(dto["can_recommend"])
		self.assertFalse(dto["can_return"])
		self.assertEqual(dto["rail_mode"], "readonly")

	def test_viewer_neutral_read_mutation_and_task_denied(self) -> None:
		viewer = ensure_user_with_roles(
			"pln.c01.viewer@test.local",
			roles=(ROLE_VIEWER,),
			pe=PE_MOH,
			org_unit=None,
			include_descendants=0,
		)
		with self.assertRaises(frappe.PermissionError):
			assert_can_create_plan(viewer)
		with self.assertRaises(frappe.PermissionError):
			assert_can_open_review_task(viewer)
		with self.assertRaises(frappe.PermissionError):
			assert_can_approve_plan(viewer)

		planner = ensure_moh_planner()
		draft = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=_unique_fy(2195),
			title="C01 viewer draft",
			currency="KES",
			coordinating_org_unit=OU_MOH,
			user=planner,
		)
		with self.assertRaises(frappe.PermissionError):
			get_departmental_contribution(plan=draft["plan"], user=viewer)

		ctx = self._in_review_plan(planner)
		dto = get_plan_review(plan=ctx["plan"], user=viewer)
		self.assertEqual(dto["surface"], "neutral")
		self.assertFalse(dto["can_approve"])
		self.assertFalse(dto["can_recommend"])
		self.assertFalse(dto["can_return"])

	def test_reviewer_and_approver_task_surface(self) -> None:
		planner = ensure_moh_planner()
		approver = ensure_moh_approver()
		ctx = self._in_review_plan(planner)

		assert_can_open_review_task(ctx["reviewer"])
		as_reviewer = get_plan_review(plan=ctx["plan"], user=ctx["reviewer"])
		self.assertEqual(as_reviewer["surface"], "task")
		self.assertIn(as_reviewer["rail_mode"], ("reviewer", "approver"))

		assert_can_open_review_task(approver)
		assert_can_approve_plan(approver)
		as_approver = get_plan_review(plan=ctx["plan"], user=approver)
		self.assertEqual(as_approver["surface"], "task")
		self.assertEqual(as_approver["rail_mode"], "approver")
		self.assertTrue(as_approver["can_approve"])

	def test_cross_pe_county_denied_moh_review(self) -> None:
		planner = ensure_moh_planner()
		county = ensure_county_planner()
		ctx = self._in_review_plan(planner)
		with self.assertRaises(frappe.PermissionError):
			get_plan_review(plan=ctx["plan"], user=county)
		with self.assertRaises(frappe.PermissionError):
			token = frappe.db.get_value(
				"Procurement Plan Version", ctx["version"], "concurrency_token"
			)
			approve_plan_version(
				version=ctx["version"],
				concurrency_token=token,
				user=county,
			)

	def test_resolve_pe_for_create_zero_one_multi(self) -> None:
		admin = ensure_admin_only()
		blocked = resolve_pe_for_create(admin)
		self.assertEqual(blocked["selection_mode"], MODE_BLOCKED)
		self.assertIsNone(blocked["procuring_entity"])

		planner = ensure_moh_planner()
		single = resolve_pe_for_create(planner)
		self.assertEqual(single["selection_mode"], MODE_SINGLE)
		self.assertEqual(single["procuring_entity"], PE_MOH)

		multi = ensure_user_with_roles(
			"pln.c01.multi@test.local",
			roles=("Procurement Planner",),
			pe=PE_MOH,
			org_unit=OU_MOH,
		)
		from kentender_procurement.procurement_planning.tests._gate02_helpers import (
			OU_CGK,
			PE_CGK,
		)

		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": multi,
				"role": "Procurement Planner",
				"procuring_entity": PE_CGK,
				"organisation_unit": OU_CGK,
				"include_descendants": 1,
			}
		).insert(ignore_permissions=True)
		scope = resolve_pe_for_create(multi)
		self.assertEqual(scope["selection_mode"], MODE_MULTI)
		self.assertIsNone(scope["procuring_entity"])
		chosen = resolve_pe_for_create(multi, selected_pe=PE_CGK)
		self.assertEqual(chosen["procuring_entity"], PE_CGK)

	def test_finance_capability_scaffold_denied_for_planner(self) -> None:
		planner = ensure_moh_planner()
		with self.assertRaises(frappe.PermissionError):
			assert_can_open_finance_task(planner)
		with self.assertRaises(frappe.PermissionError):
			assert_can_confirm_plan_funding(planner)
