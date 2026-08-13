# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-013 — publish/export current Approved Plan Version."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import (
	PUB_PUBLISHED,
	VERSION_APPROVED,
)
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.publish_approved_plan import (
	publish_approved_plan,
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


class TestPublishApprovedPlan(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_draft_cannot_publish(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3200, bucket=0)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Draft publish deny", financial_year=fy)
		result = publish_approved_plan(plan=plan["plan"], user=planner)
		self.assertFalse(result["ok"])
		self.assertIn("form", result["errors"])

	def test_publish_keeps_plan_approved(self) -> None:
		planner = ensure_planner_user()
		fy = unique_test_fy(base_year=3200, bucket=1)
		purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Publish approved", financial_year=fy)
		d = make_approved_demand(title="Publish demand")
		add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		approve_plan_via_gate05(plan=plan["plan"], version=plan["version"])
		result = publish_approved_plan(plan=plan["plan"], user=planner)
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["status"], PUB_PUBLISHED)
		self.assertEqual(result["destination"], "Tender Portal")
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Version", plan["version"], "status"),
			VERSION_APPROVED,
		)
		event = frappe.get_all(
			"Publication Event",
			filters={"plan_version": plan["version"]},
			fields=["status", "channel"],
			limit=1,
		)
		self.assertTrue(event)
		self.assertEqual(event[0].status, PUB_PUBLISHED)

		again = publish_approved_plan(plan=plan["plan"], user=planner)
		self.assertTrue(again["ok"], again)
		self.assertTrue(again.get("idempotent"))
		self.assertEqual(
			frappe.db.count("Publication Event", {"plan_version": plan["version"]}),
			1,
		)
