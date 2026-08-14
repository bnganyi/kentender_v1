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
		with self.assertRaises(frappe.PermissionError):
			assert_can_handoff(admin)

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
		with self.assertRaises(frappe.PermissionError):
			assert_can_handoff(planner)

		ctx = self._in_review_plan(planner)
		dto = get_plan_review(plan=ctx["plan"], user=planner)
		self.assertEqual(dto["surface"], "neutral")
		self.assertFalse(dto["can_approve"])
		self.assertFalse(dto["can_recommend"])
		self.assertFalse(dto["can_return"])
		self.assertEqual(dto["rail_mode"], "readonly")

	def test_viewer_neutral_read_mutation_and_task_denied(self) -> None:
		"""PLN-AC-021 — Neutral visibility must not expose Finance or approval task forms."""
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
		with self.assertRaises(frappe.PermissionError):
			assert_can_handoff(viewer)

		planner = ensure_moh_planner()
		draft = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=_unique_fy(2195),
			title="C01 viewer draft",
			currency="KES",
			coordinating_org_unit=OU_MOH,
			user=planner,
		)
		# Viewer may read plan review as neutral; cannot mutate/create.
		dto_draft = get_plan_review(plan=draft["plan"], user=viewer)
		self.assertEqual(dto_draft["surface"], "neutral")
		self.assertFalse(dto_draft["can_approve"])

		ctx = self._in_review_plan(planner)
		dto = get_plan_review(plan=ctx["plan"], user=viewer)
		self.assertEqual(dto["surface"], "neutral")
		self.assertFalse(dto["can_approve"])
		self.assertFalse(dto["can_recommend"])
		self.assertFalse(dto["can_return"])

	def test_reviewer_cannot_approve_plan(self) -> None:
		"""PLN-PERM-005 — Reviewer Recommend/Return only; Approve is denied."""
		reviewer = ensure_user_with_roles(
			"pln.c01.reviewer.deny@test.local",
			roles=(ROLE_REVIEWER,),
			pe=PE_MOH,
			org_unit=None,
			include_descendants=0,
		)
		with self.assertRaises(frappe.PermissionError):
			assert_can_approve_plan(reviewer)

		planner = ensure_moh_planner()
		approver = ensure_moh_approver()
		ctx = self._in_review_plan(planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", ctx["version"], "concurrency_token"
		)
		with self.assertRaises(frappe.PermissionError):
			approve_plan_version(
				version=ctx["version"],
				concurrency_token=token,
				user=reviewer,
			)
		assert_can_approve_plan(approver)
		result = approve_plan_version(
			version=ctx["version"],
			concurrency_token=token,
			user=approver,
		)
		self.assertTrue(result["ok"], result)

	def test_reviewer_and_approver_task_surface(self) -> None:
		planner = ensure_moh_planner()
		approver = ensure_moh_approver()
		ctx = self._in_review_plan(planner)

		assert_can_open_review_task(ctx["reviewer"])
		as_reviewer = get_plan_review(plan=ctx["plan"], user=ctx["reviewer"])
		self.assertEqual(as_reviewer["surface"], "task")
		self.assertIn(as_reviewer["rail_mode"], ("reviewer", "approver"))
		self.assertFalse(as_reviewer["can_approve"])
		self.assertTrue(as_reviewer["can_recommend"] or as_reviewer["has_recommendation"])

		assert_can_open_review_task(approver)
		assert_can_approve_plan(approver)
		as_approver = get_plan_review(plan=ctx["plan"], user=approver)
		self.assertEqual(as_approver["surface"], "task")
		self.assertEqual(as_approver["rail_mode"], "approver")
		self.assertTrue(as_approver["can_approve"])

	def test_reviewer_draft_plan_is_neutral_surface(self) -> None:
		"""PLN-GAP-PERM-004 — role alone must not open the professional rail."""
		planner = ensure_moh_planner()
		reviewer = ensure_reviewer_user()
		created = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=_unique_fy(prefix=2290),
			title="PERM-004 draft review",
			currency="KES",
			coordinating_org_unit=OU_MOH,
			user=planner,
		)
		dto = get_plan_review(plan=created["plan"], user=reviewer)
		self.assertEqual(dto["surface"], "neutral")
		self.assertFalse(dto["can_recommend"])
		self.assertFalse(dto["can_approve"])
		self.assertEqual(dto["rail_mode"], "readonly")

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
