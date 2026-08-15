# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-03/05 initial-Draft builder projection contract."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.get_plan_builder import get_plan_builder
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestPlanBuilderRevision(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_empty_initial_draft_uses_ui03_contract(self) -> None:
		created = create_plan_as_planner()
		payload = get_plan_builder(plan=created["plan"], user=ensure_planner_user())
		self.assertEqual(payload["state_id"], "PLN-UI-03")
		self.assertEqual(payload["item_count"], 0)
		self.assertEqual(payload["planned_total"], 0)
		self.assertEqual(payload["planning_complete_display"], "0 of 0")
		self.assertEqual(payload["finance_confirmed_display"], "0 of 0")
		self.assertEqual(payload["validation_projection"], "Not run")

	def test_populated_initial_draft_uses_exact_rows_and_server_filters(self) -> None:
		created = create_plan_as_planner()
		first = make_approved_demand(title="Clinical training laptops", item_amount=48_000_000)
		second = make_approved_demand(title="Clinical deployment laptops", item_amount=72_000_000)
		add_demand_to_plan(
			plan=created["plan"], demands=[first["demand"], second["demand"]],
			formation_mode="separate", user=ensure_planner_user(),
		)
		payload = get_plan_builder(plan=created["plan"], user=ensure_planner_user())
		self.assertEqual(payload["state_id"], "PLN-UI-05")
		self.assertEqual(payload["item_count"], 2)
		self.assertEqual(payload["planned_total"], 120_000_000)
		self.assertEqual(payload["planning_complete_display"], "0 of 2")
		self.assertEqual(payload["finance_confirmed_display"], "0 of 2")
		self.assertEqual([row["action_label"] for row in payload["items"]], ["Complete item", "Complete item"])
		filtered = get_plan_builder(
			plan=created["plan"], search="deployment", status="incomplete",
			user=ensure_planner_user(),
		)
		self.assertEqual([row["title"] for row in filtered["items"]], ["Clinical deployment laptops"])
		self.assertEqual(filtered["unfiltered_item_count"], 2)

	def test_builder_query_count_does_not_grow_per_item(self) -> None:
		created = create_plan_as_planner()
		demands = [make_approved_demand(title=f"Bounded builder item {index}") for index in range(4)]
		add_demand_to_plan(
			plan=created["plan"], demands=[row["demand"] for row in demands],
			formation_mode="separate", user=ensure_planner_user(),
		)
		# Warm Frappe metadata and permission caches before comparing query growth.
		get_plan_builder(plan=created["plan"], user=ensure_planner_user())
		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as many_sql:
			many = get_plan_builder(plan=created["plan"], user=ensure_planner_user())
		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as one_sql:
			one = get_plan_builder(
				plan=created["plan"], search="Bounded builder item 0",
				user=ensure_planner_user(),
			)
		self.assertEqual(len(many["items"]), 4)
		self.assertEqual(len(one["items"]), 1)
		# A one-query cache warm-up difference is acceptable; row count must not
		# produce linear growth.
		self.assertLessEqual(abs(many_sql.call_count - one_sql.call_count), 1)
