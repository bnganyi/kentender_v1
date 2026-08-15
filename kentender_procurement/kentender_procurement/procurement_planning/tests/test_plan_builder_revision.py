# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-03/05 ordinary builder projection contract."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.get_plan_builder import get_plan_builder
from kentender_procurement.procurement_planning.services.plan_item_finance import confirm_plan_item_funding
from kentender_procurement.procurement_planning.services.plan_item_finance import _source_demand_row
from kentender_procurement.procurement_planning.services.plan_builder_successor import save_plan_draft
from kentender_procurement.procurement_planning.services.update_plan_item import update_plan_item
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
	attach_demand_funding,
	approve_plan_via_gate05,
	complete_plan_item_for_signoff,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	make_test_budget_line,
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

	def _successor_awaiting_finance(self) -> tuple[str, str, str, str]:
		planner = ensure_planner_user()
		created = create_plan_as_planner(title="PLN-CHG-014 successor")
		base = make_approved_demand(title="Operational Approved item", item_amount=455_000_000)
		base_item = add_demand_to_plan(plan=created["plan"], demand=base["demand"], user=planner)["plan_item"]
		complete_plan_item_for_signoff(plan_item=base_item, user=planner)
		approve_plan_via_gate05(plan=created["plan"], version=created["version"])
		addition = make_approved_demand(
			title="Digital health technical staff certification programme",
			item_amount=80_000_000,
			required_by_date=frappe.db.get_value("Procurement Plan", created["plan"], "period_start"),
		)
		added = add_demand_to_plan(plan=created["plan"], demand=addition["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		source = _source_demand_row(added["plan_item"])
		if source and not frappe.db.exists("Demand Funding Allocation", {"demand": source["demand"]}):
			funding = make_test_budget_line(approved_amount=160_000_000, plan=created["plan"])
			attach_demand_funding(
				demand=source["demand"],
				budget_line=funding["budget_line"],
				budget=funding["budget"],
				amount=80_000_000,
			)
		draft = frappe.db.get_value("Procurement Plan", created["plan"], "open_draft_version")
		token = frappe.db.get_value("Procurement Plan Version", draft, "concurrency_token")
		saved = save_plan_draft(
			plan=created["plan"],
			expected_version_token=token,
			update_reason="Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.",
			idempotency_key=f"TEST-SAVE-SUCCESSOR-{draft}",
			user=planner,
		)
		self.assertTrue(saved["ok"])
		requested = update_plan_item(
			plan_item=added["plan_item"],
			fields={},
			request_finance=True,
			expected_version_token=saved["concurrency_token"],
			idempotency_key=f"TEST-REQUEST-SUCCESSOR-{draft}",
			user=planner,
		)
		self.assertTrue(requested["ok"])
		validate_plan(plan=created["plan"], user=planner)
		return created["plan"], draft, added["plan_item"], planner

	def test_successor_awaiting_finance_uses_exact_ui05_contract(self) -> None:
		plan, draft, added_item, planner = self._successor_awaiting_finance()
		payload = get_plan_builder(plan=plan, user=planner)
		self.assertEqual(payload["state_id"], "PLN-UI-05")
		self.assertEqual(payload["builder_kind"], "successor")
		self.assertEqual(payload["readiness_state"], "needs_attention")
		self.assertEqual(payload["item_count"], 2)
		self.assertEqual(payload["planned_total"], 535_000_000)
		self.assertEqual(payload["change_amount"], 80_000_000)
		self.assertEqual(payload["change_display"], "KES 80,000,000 added")
		self.assertEqual(payload["planning_complete_display"], "2 of 2")
		self.assertEqual(payload["finance_confirmed_display"], "1 of 2")
		self.assertEqual(payload["validation_projection"], "Needs attention")
		self.assertFalse(payload["can_submit"])
		self.assertEqual([row["plan_item"] for row in payload["items"]], [added_item])
		self.assertEqual(payload["items"][0]["action_label"], "View Plan Item")
		self.assertEqual(payload["items"][0]["validation_status"], "Needs attention")
		self.assertIn(payload["items"][0]["plan_item_code"], payload["issue_message"])
		self.assertIn("unchanged Active Plan Item", payload["unchanged_operational_copy"])

		# A replay resolves before stale-token rejection and returns the original result.
		replayed = save_plan_draft(
			plan=plan,
			expected_version_token="stale-token",
			update_reason=payload["update_reason"],
			idempotency_key=f"TEST-SAVE-SUCCESSOR-{draft}",
			user=planner,
		)
		self.assertTrue(replayed["idempotent"])

	def test_successor_ready_uses_exact_ui05_contract(self) -> None:
		plan, _draft, added_item, planner = self._successor_awaiting_finance()
		iv_name = frappe.db.get_value("Procurement Plan Item", added_item, "draft_item_version")
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		confirmed = confirm_plan_item_funding(
			task=iv.finance_task_id,
			expected_token=iv.finance_task_token,
			idempotency_key=f"TEST-CONFIRM-SUCCESSOR-{iv.finance_task_id}",
			user=iv.finance_task_assignee,
		)
		self.assertTrue(confirmed["ok"])
		validate_plan(plan=plan, user=planner)
		payload = get_plan_builder(plan=plan, user=planner)
		self.assertEqual(payload["readiness_state"], "ready")
		self.assertEqual(payload["planning_complete_display"], "2 of 2")
		self.assertEqual(payload["finance_confirmed_display"], "2 of 2")
		self.assertEqual(payload["validation_projection"], "Ready")
		self.assertEqual(payload["readiness_message"], "All required Planning validation and Finance confirmations are ready.")
		self.assertTrue(payload["can_submit"])
