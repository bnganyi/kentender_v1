# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-GATE-C01 — record vs task vs mutation capability + Admin/PE hardening."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_procurement_plan_for_test as create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_review import (
	get_plan_review,
)
from kentender_procurement.procurement_planning.mvp1_constants import (
	FINANCE_AWAITING,
	FINANCE_RETURNED,
	VERSION_IN_REVIEW,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CAP_PLAN_FINANCE_CONFIRM,
	CAP_PLAN_ITEM_EDIT,
	CAP_PLAN_VIEW,
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	ROLE_REVIEWER,
	ROLE_TENDER_INITIATOR,
	ROLE_VIEWER,
	assert_can_approve_plan,
	assert_can_confirm_plan_funding,
	assert_can_create_plan,
	assert_can_handoff,
	assert_can_open_finance_task,
	assert_can_open_review_task,
	assert_can_submit_for_review,
	get_available_actions,
	resolve_pe_for_create,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	advance_draft_to_recommended,
	ensure_reviewer_user,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
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
	fy = unique_test_fy(base_year=prefix, bucket=int(frappe.db.count("Procurement Plan") or 0))
	purge_pe_fy(fy)
	return fy


class TestPlanningTaskCapability(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def _in_review_plan(self, planner: str) -> dict[str, str]:
		created = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=_unique_fy(),
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
			"task": advanced["task"],
			"assignee": advanced["assignee"],
		}

	def test_review_projection_is_task_only_and_assignment_protected(self) -> None:
		planner = ensure_moh_planner()
		ctx = self._in_review_plan(planner)
		with self.assertRaises(frappe.PermissionError):
			get_plan_review(task=ctx["task"], user=planner)
		county = ensure_county_planner()
		with self.assertRaises(frappe.PermissionError):
			get_plan_review(task=ctx["task"], user=county)
		dto = get_plan_review(task=ctx["task"], user=ctx["assignee"])
		self.assertEqual(dto["surface"], "task")
		self.assertTrue(dto["can_approve"])
		self.assertTrue(dto["can_return"])
		self.assertNotIn("can_recommend", dto)

	def test_assigned_professional_approval_uses_task_token(self) -> None:
		planner = ensure_moh_planner()
		ctx = self._in_review_plan(planner)
		dto = get_plan_review(task=ctx["task"], user=ctx["assignee"])
		result = approve_plan_version(
			task=ctx["task"],
			expected_token=dto["task_token"],
			idempotency_key=f"C01-APPROVE-{ctx['task']}",
			user=ctx["assignee"],
		)
		self.assertTrue(result["ok"], result)

	def test_resolve_pe_for_create_zero_one_multi(self) -> None:
		"""PLN-AC-001 — multi-PE selects; zero blocks; one PE stays visible."""
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

	def test_available_actions_finance_and_review_from_capability(self) -> None:
		"""PLN-GAP-PERM-003 — queues must not invent Confirm/Review from status."""
		planner = ensure_moh_planner()
		viewer = ensure_user_with_roles(
			"pln.c01.actions.viewer@test.local",
			roles=(ROLE_VIEWER,),
			pe=PE_MOH,
			org_unit=OU_MOH,
		)
		awaiting = {"kind": "finance_item", "finance_status": FINANCE_AWAITING}
		returned = {"kind": "finance_item", "finance_status": FINANCE_RETURNED}
		planner_await = get_available_actions(planner, awaiting)
		self.assertEqual(planner_await[0]["action"], "view")
		self.assertNotEqual(planner_await[0]["code"], CAP_PLAN_FINANCE_CONFIRM)
		planner_ret = get_available_actions(planner, returned)
		self.assertEqual(planner_ret[0]["action"], "continue_item")
		self.assertEqual(planner_ret[0]["code"], CAP_PLAN_ITEM_EDIT)
		viewer_await = get_available_actions(viewer, awaiting)
		self.assertEqual(viewer_await[0]["action"], "view")
		self.assertEqual(viewer_await[0]["code"], CAP_PLAN_VIEW)
		viewer_ret = get_available_actions(viewer, returned)
		self.assertEqual(viewer_ret[0]["action"], "view")
		review = get_available_actions(
			planner,
			{"kind": "plan_version", "version_status": VERSION_IN_REVIEW},
		)
		self.assertEqual(review[0]["action"], "view")

	def test_tender_initiator_can_handoff_planner_cannot(self) -> None:
		"""PLN-GAP-PERM-001 — take-up is Tender Initiator only."""
		planner = ensure_moh_planner()
		with self.assertRaises(frappe.PermissionError):
			assert_can_handoff(planner)
		initiator = ensure_user_with_roles(
			"pln.c01.initiator@test.local",
			roles=(ROLE_TENDER_INITIATOR,),
			pe=PE_MOH,
			org_unit=OU_MOH,
		)
		assert_can_handoff(initiator)
