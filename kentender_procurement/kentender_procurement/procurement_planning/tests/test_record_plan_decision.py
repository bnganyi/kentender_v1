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
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.record_plan_decision import (
	record_plan_decision,
)
from kentender_procurement.procurement_planning.services.submit_departmental_contribution import (
	submit_departmental_contribution,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
	create_plan_as_planner,
	ensure_hod_user,
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
		hod = ensure_hod_user()
		reviewer = ensure_reviewer_user()
		fy = unique_test_fy(base_year=2700, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Decision plan", financial_year=fy)
		d = make_approved_demand(title="Decision demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		validate_plan(plan=plan["plan"], user=planner)
		self.assertTrue(
			submit_departmental_contribution(plan=plan["plan"], declaration=1, user=hod)[
				"ok"
			]
		)
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

	def test_planner_cannot_recommend(self) -> None:
		planner, _reviewer, plan = self._in_review()
		with self.assertRaises(frappe.PermissionError):
			record_plan_decision(
				version=plan["version"],
				decision="recommend",
				user=planner,
			)
