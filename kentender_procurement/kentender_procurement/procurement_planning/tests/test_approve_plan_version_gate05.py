# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-011 Gate 05 — approve only after In review + recommend + Ready."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_EFFECTIVE,
	FINANCE_AWAITING,
	VERSION_APPROVED,
	VERSION_IN_REVIEW,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	advance_draft_to_recommended,
	approve_plan_via_gate05,
	complete_plan_item_for_signoff,
	confirm_included_items_funding,
	create_plan_as_planner,
	ensure_approver_user,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)


class TestApprovePlanVersionGate05(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_approve_requires_in_review(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		fy = unique_test_fy(base_year=2800, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Draft approve deny", financial_year=fy)
		d = make_approved_demand(title="Draft approve demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			approve_plan_version(
				version=plan["version"], concurrency_token=token, user=approver
			)
		msg = str(ctx.exception).lower()
		self.assertTrue(
			"in review" in msg or "not_approvable" in msg or "approvable" in msg,
			msg,
		)

	def test_professional_task_replaces_recommendation(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		fy = unique_test_fy(base_year=2800, bucket=1)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="No recommend approve", financial_year=fy)
		d = make_approved_demand(title="No recommend demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		confirm_included_items_funding(plan=plan["plan"], planner=planner)
		validate_plan(plan=plan["plan"], user=planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		sub = submit_plan_for_review(
			plan=plan["plan"], expected_token=token,
			idempotency_key=f"TEST-SUBMIT-{plan['version']}", user=planner
		)
		self.assertTrue(sub["ok"], sub)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Version", plan["version"], "status"),
			VERSION_IN_REVIEW,
		)
		approved = approve_plan_version(
			task=sub["task"], expected_token=sub["task_token"],
			idempotency_key=f"TEST-APPROVE-{sub['task']}", user=sub["assignee"]
		)
		self.assertEqual(approved["status"], VERSION_APPROVED)

	def test_happy_path_effective_once(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		fy = unique_test_fy(base_year=2800, bucket=2)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Approve happy", financial_year=fy)
		d = make_approved_demand(title="Approve happy demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		result = approve_plan_via_gate05(
			plan=plan["plan"], version=plan["version"], user=approver
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["status"], VERSION_APPROVED)
		self.assertEqual(
			frappe.db.get_value("Plan Demand Allocation", added["allocation"], "status"),
			ALLOC_EFFECTIVE,
		)
		# Idempotent: second approve fails
		with self.assertRaises(frappe.ValidationError):
			approve_plan_version(
				version=plan["version"],
				concurrency_token=frappe.db.get_value(
					"Procurement Plan Version", plan["version"], "concurrency_token"
				),
				user=approver,
			)

	def test_get_plan_review_rail_modes(self) -> None:
		from kentender_procurement.procurement_planning.services.get_plan_review import (
			get_plan_review,
		)

		planner = ensure_planner_user()
		approver = ensure_approver_user()
		fy = unique_test_fy(base_year=2800, bucket=3)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Review dto", financial_year=fy)
		d = make_approved_demand(title="Review dto demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		advanced = advance_draft_to_recommended(
			plan=plan["plan"], version=plan["version"]
		)
		as_approver = get_plan_review(task=advanced["task"], user=advanced["assignee"])
		self.assertEqual(as_approver["surface"], "task")
		self.assertTrue(as_approver["can_approve"])
		self.assertTrue(as_approver["items"])
		self.assertEqual(as_approver["statutory_coverage"], [])
		self.assertTrue(as_approver.get("finance_complete"))
		self.assertEqual(
			as_approver.get("finance_confirmed_label"),
			f"{as_approver['finance_confirmed_count']} of {as_approver['finance_item_count']}",
		)
		self.assertEqual(as_approver["finance_confirmed_count"], as_approver["finance_item_count"])
		self.assertTrue(as_approver["finance_item_count"] >= 1)
		for row in as_approver["items"]:
			self.assertEqual(row.get("finance_status_label"), "Confirmed")

	def test_approve_denied_when_finance_not_confirmed(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		fy = unique_test_fy(base_year=2800, bucket=4)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Approve finance deny", financial_year=fy)
		d = make_approved_demand(title="Approve finance deny demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		advanced = advance_draft_to_recommended(
			plan=plan["plan"], version=plan["version"]
		)
		iv_name = frappe.db.get_value(
			"Procurement Plan Item", added["plan_item"], "draft_item_version"
		)
		frappe.db.set_value(
			"Procurement Plan Item Version",
			iv_name,
			"finance_status",
			FINANCE_AWAITING,
			update_modified=False,
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			approve_plan_version(
				task=advanced["task"], expected_token=advanced["task_token"],
				idempotency_key=f"TEST-DENY-{advanced['task']}", user=advanced["assignee"]
			)
		msg = str(ctx.exception).upper()
		self.assertTrue("FINANCE" in msg or "PLN_FINANCE_NOT_CONFIRMED" in msg, msg)
