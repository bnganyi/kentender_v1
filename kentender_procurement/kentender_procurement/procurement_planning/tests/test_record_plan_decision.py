# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-010 — record_plan_decision recommend / return."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import (
	DECISION_RECOMMENDED,
	DECISION_RETURNED,
	VERSION_IN_REVIEW,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.record_plan_decision import (
	record_plan_decision,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
	confirm_included_items_funding,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_reviewer_user,
	ensure_scope,
	make_approved_demand,
	purge_pe_fy,
	unique_test_fy,
)


class TestRecordPlanDecision(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _in_review(self):
		planner = ensure_planner_user()
		reviewer = ensure_reviewer_user()
		fy = unique_test_fy(base_year=2700, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Decision plan", financial_year=fy)
		d = make_approved_demand(title="Decision demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		confirm_included_items_funding(plan=plan["plan"], planner=planner)
		validate_plan(plan=plan["plan"], user=planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		sub = submit_plan_for_review(
			plan=plan["plan"], concurrency_token=token, user=planner
		)
		self.assertTrue(sub["ok"], sub)
		return planner, reviewer, plan

	def test_reviewer_recommends(self) -> None:
		_planner, reviewer, plan = self._in_review()
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		result = record_plan_decision(
			version=plan["version"],
			decision="recommend",
			comment="Looks good",
			concurrency_token=token,
			user=reviewer,
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["decision"], DECISION_RECOMMENDED)
		self.assertEqual(result["status"], VERSION_IN_REVIEW)
		self.assertTrue(
			frappe.db.exists(
				"Plan Decision",
				{"plan_version": plan["version"], "decision": DECISION_RECOMMENDED},
			)
		)

	def test_return_requires_comment(self) -> None:
		_planner, reviewer, plan = self._in_review()
		result = record_plan_decision(
			version=plan["version"],
			decision="return",
			comment="",
			user=reviewer,
		)
		self.assertFalse(result["ok"])
		self.assertIn("decision_comment", result["errors"])

	def test_return_sets_returned(self) -> None:
		_planner, reviewer, plan = self._in_review()
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		result = record_plan_decision(
			version=plan["version"],
			decision="return",
			comment="Fix statutory coverage narrative",
			concurrency_token=token,
			user=reviewer,
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["decision"], DECISION_RETURNED)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Version", plan["version"], "status"),
			VERSION_RETURNED,
		)
		planner_logs = frappe.db.count(
			"Notification Log",
			{"for_user": _planner, "email_header": ["like", f"pln-return:{plan['version']}:%"]},
		)
		self.assertGreaterEqual(planner_logs, 1)

	def test_stale_concurrency_token_rejected(self) -> None:
		"""PLN-NFR-003 — stale concurrency token cannot record a review decision."""
		_planner, reviewer, plan = self._in_review()
		stale = record_plan_decision(
			version=plan["version"],
			decision="recommend",
			comment="Looks good",
			concurrency_token="not-the-token",
			user=reviewer,
		)
		self.assertFalse(stale.get("ok"), stale)
		self.assertIn("form", stale.get("errors") or {})
		self.assertIn("changed by another user", str(stale.get("errors")).lower())

	def test_planner_cannot_recommend(self) -> None:
		planner, _reviewer, plan = self._in_review()
		with self.assertRaises(frappe.PermissionError):
			record_plan_decision(
				version=plan["version"],
				decision="recommend",
				user=planner,
			)

	def test_recommend_stamps_usa_role_not_desk_approver(self) -> None:
		"""PLN-GAP-PERM-005 — actor_role comes from USA, not frappe.get_roles."""
		from kentender_procurement.procurement_planning.services.planning_permissions import (
			ROLE_DESIGNATED_APPROVER,
			ROLE_REVIEWER,
		)

		_planner, reviewer, plan = self._in_review()
		user = frappe.get_doc("User", reviewer)
		if ROLE_DESIGNATED_APPROVER not in {r.role for r in user.roles}:
			user.add_roles(ROLE_DESIGNATED_APPROVER)
		token = frappe.db.get_value(
			"Procurement Plan Version", plan["version"], "concurrency_token"
		)
		result = record_plan_decision(
			version=plan["version"],
			decision="recommend",
			comment="USA role stamp",
			concurrency_token=token,
			user=reviewer,
		)
		self.assertTrue(result["ok"], result)
		stamped = frappe.db.get_value(
			"Plan Decision",
			{"plan_version": plan["version"], "decision": DECISION_RECOMMENDED},
			"actor_role",
		)
		self.assertEqual(stamped, ROLE_REVIEWER)
