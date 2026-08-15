# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-009 — submit_plan_for_review (Ready-only; no contribution)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cstr

from kentender_procurement.procurement_planning.mvp1_constants import VERSION_IN_REVIEW
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review as _submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
	confirm_included_items_funding,
	create_plan_as_planner,
	ensure_hod_user,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)


def submit_plan_for_review(*, plan: str, user: str, concurrency_token: str | None = None):
	return _submit_plan_for_review(
		plan=plan,
		expected_token=concurrency_token,
		idempotency_key=f"TEST-SUBMIT-{plan}" if concurrency_token else None,
		user=user,
	)


class TestSubmitPlanForReview(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()
		for user in ("pln.gate01.approver@test.local", "moh.plan.approver@example.test"):
			for name in frappe.get_all(
				"User Scope Assignment",
				filters={"user": user, "role": "Designated Approver", "procuring_entity": "PE-MOH"},
				pluck="name",
			):
				frappe.delete_doc("User Scope Assignment", name, force=True, ignore_permissions=True)

	def _ready_plan(self):
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=2600, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Submit review plan", financial_year=fy)
		d = make_approved_demand(title="Submit review demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		validate_plan(plan=plan["plan"], user=planner)
		return planner, plan

	def test_submit_blocked_until_finance_confirmed(self) -> None:
		planner, plan = self._ready_plan()
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		blocked = submit_plan_for_review(
			plan=plan["plan"], concurrency_token=token, user=planner
		)
		self.assertFalse(blocked["ok"], blocked)
		self.assertIn("form", blocked["errors"])
		self.assertIn("finance", blocked["errors"]["form"].lower())

		confirm_included_items_funding(plan=plan["plan"], planner=planner)
		token2 = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		result = submit_plan_for_review(
			plan=plan["plan"], concurrency_token=token2, user=planner
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["status"], VERSION_IN_REVIEW)

	def test_planner_submits_for_review_without_contribution(self) -> None:
		planner, plan = self._ready_plan()
		confirm_included_items_funding(plan=plan["plan"], planner=planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		result = submit_plan_for_review(
			plan=plan["plan"], concurrency_token=token, user=planner
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["status"], VERSION_IN_REVIEW)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Version", plan["version"], "status"),
			VERSION_IN_REVIEW,
		)

	def test_submit_notifies_pe_reviewer_not_kisumu(self) -> None:
		from kentender_procurement.procurement_planning.services.planning_notification_service import (
			EVENT_PLAN_SUBMITTED,
		)
		from kentender_procurement.procurement_planning.services.planning_permissions import (
			ROLE_REVIEWER,
		)
		from kentender_core.seeds.kentender_mvp_v1.constants import USER_HOP
		from kentender_procurement.procurement_planning.tests._gate02_helpers import (
			PE_CGK,
			ensure_org,
			ensure_user_with_roles,
		)

		ensure_org()
		reviewer = USER_HOP
		kisumu = ensure_user_with_roles(
			"pln.wave3.kisumu.reviewer@test.local",
			roles=(ROLE_REVIEWER,),
			pe=PE_CGK,
			org_unit=None,
			include_descendants=0,
		)
		planner, plan = self._ready_plan()
		confirm_included_items_funding(plan=plan["plan"], planner=planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		before = frappe.db.count(
			"Notification Log",
			{"for_user": reviewer, "email_header": ["like", "pln-submit-review:%"]},
		)
		kisumu_before = frappe.db.count(
			"Notification Log",
			{"for_user": kisumu, "email_header": ["like", "pln-submit-review:%"]},
		)
		result = submit_plan_for_review(
			plan=plan["plan"], concurrency_token=token, user=planner
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(
			frappe.db.count(
				"Notification Log",
				{"for_user": reviewer, "email_header": ["like", "pln-submit-review:%"]},
			),
			before + 1,
		)
		self.assertEqual(
			frappe.db.count(
				"Notification Log",
				{"for_user": kisumu, "email_header": ["like", "pln-submit-review:%"]},
			),
			kisumu_before,
		)
		content = frappe.db.get_value(
			"Notification Log",
			{"for_user": reviewer, "email_header": ["like", "pln-submit-review:%"]},
			"email_content",
		)
		self.assertIn(EVENT_PLAN_SUBMITTED, cstr(content))
		self.assertIn("PE-MOH", cstr(content))

	def test_blocks_when_not_ready(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=2600, bucket=2)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Not ready review", financial_year=fy)
		d = make_approved_demand(title="Not ready demand")
		add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		result = submit_plan_for_review(plan=plan["plan"], user=planner)
		self.assertFalse(result["ok"])
		self.assertIn("form", result["errors"])

	def test_hod_denied(self) -> None:
		planner, plan = self._ready_plan()
		hod = ensure_hod_user()
		with self.assertRaises(frappe.PermissionError):
			submit_plan_for_review(plan=plan["plan"], user=hod)
