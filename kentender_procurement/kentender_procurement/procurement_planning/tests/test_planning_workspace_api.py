# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-001 — get_planning_workspace API (PE-scope matrix)."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cstr

from kentender_procurement.procurement_planning.api import (
	get_planning_workspace as api_get_planning_workspace,
)
from kentender_procurement.procurement_planning.services.get_planning_workspace import (
	get_planning_workspace,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	ROLE_PLANNER,
	ROLE_VIEWER,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	make_approved_demand,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	OU_CGK,
	OU_MOH,
	PE_CGK,
	PE_MOH,
	_ensure_ou,
	ensure_admin_only,
	ensure_moh_planner,
	ensure_org,
	ensure_user_with_roles,
)


class TestPlanningWorkspaceApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def test_admin_only_without_viewer_blocked(self) -> None:
		"""System Manager with no Planning role still cannot load PE-bound workspace data."""
		admin = ensure_admin_only()
		with self.assertRaises(frappe.PermissionError):
			get_planning_workspace(procuring_entity=PE_MOH, user=admin)

	def test_support_viewer_requires_deliberate_entity_selection(self) -> None:
		"""Support visibility never restores the retired all-entities projection."""
		email = ensure_user_with_roles(
			"pln.gate03.support.viewer@test.local",
			roles=(ROLE_VIEWER,),
			pe=PE_MOH,
			org_unit=OU_MOH,
			clear_scope=True,
		)
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_VIEWER,
				"procuring_entity": PE_CGK,
				"organisation_unit": OU_CGK,
				"include_descendants": 1,
			}
		).insert(ignore_permissions=True)
		payload = get_planning_workspace(user=email)
		self.assertTrue(payload["ok"])
		self.assertTrue(payload.get("read_only"))
		self.assertFalse(payload.get("can_create_plan"))
		self.assertIsNone(payload["procuring_entity"])
		self.assertEqual(payload["selection_mode"], MODE_MULTI)
		ids = {e["id"] for e in payload["procuring_entities"]}
		self.assertIn(PE_MOH, ids)
		self.assertIn(PE_CGK, ids)
		# Explicit PE still works.
		moh = get_planning_workspace(procuring_entity=PE_MOH, user=email)
		self.assertEqual(moh["procuring_entity"], PE_MOH)
		self.assertTrue(moh.get("read_only"))
		self.assertFalse(moh.get("can_create_plan"))

	def test_desk_administrator_support_viewer_seed(self) -> None:
		from kentender_core.seeds.kentender_mvp_v1.users import (
			ensure_administrator_planning_support_viewer,
		)

		ensure_administrator_planning_support_viewer()
		payload = get_planning_workspace(user="Administrator")
		self.assertTrue(payload["ok"])
		self.assertTrue(payload.get("read_only"))
		self.assertFalse(payload.get("can_create_plan"))
		self.assertNotEqual(payload["selection_mode"], MODE_BLOCKED)
		self.assertIsNone(payload["procuring_entity"])
		self.assertNotIn("__all__", {e["id"] for e in payload["procuring_entities"]})

	def test_single_pe_workspace_shape(self) -> None:
		planner = ensure_moh_planner()
		payload = get_planning_workspace(
			procuring_entity=PE_MOH, financial_year="2027/28", user=planner
		)
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["selection_mode"], MODE_SINGLE)
		self.assertEqual(payload["procuring_entity"], PE_MOH)
		self.assertIn("current_plan", payload)
		self.assertIn("work_queue", payload)
		self.assertIn("work_requiring_action", payload)
		self.assertIn("waiting_on_others", payload)
		self.assertEqual(payload["primary_action"]["label"], "View approved plan")
		self.assertEqual(payload["current_plan"]["approved"]["planned_total"], 455_000_000)
		self.assertEqual(payload["current_plan"]["approved"]["finance_confirmed_label"], "1 of 1")
		self.assertEqual(payload["current_plan"]["approved"]["validation_projection"], "Ready")
		self.assertIsInstance(payload["work_queue"], list)
		# Whitelist entry also callable
		frappe.set_user(planner)
		try:
			api_payload = api_get_planning_workspace(
				procuring_entity=PE_MOH, financial_year="2027/28"
			)
		finally:
			frappe.set_user("Administrator")
		self.assertTrue(api_payload["ok"])

	def test_work_queue_soft_filters_out_of_scope_ou_without_msgprint(self) -> None:
		"""Out-of-scope Demand OUs must not raise PLN_SCOPE_DENIED dialogs on load."""
		ensure_org()
		other_ou = "MOH-DIR-HRMD"
		_ensure_ou(other_ou, "Human Resource Management", PE_MOH)
		planner = ensure_moh_planner()
		foreign = make_approved_demand(
			pe=PE_MOH,
			ou=other_ou,
			title="Out-of-scope OU demand for queue filter",
		)
		frappe.db.set_value("Demand", foreign["demand"], "status", "Returned")
		frappe.db.commit()

		titles: list[str] = []
		orig = frappe.msgprint

		def _spy(msg, *args, **kwargs):
			titles.append(cstr(kwargs.get("title") or ""))
			return orig(msg, *args, **kwargs)

		frappe.msgprint = _spy
		try:
			payload = get_planning_workspace(
				procuring_entity=PE_MOH, financial_year="2027/28", user=planner
			)
		finally:
			frappe.msgprint = orig

		self.assertTrue(payload["ok"])
		self.assertNotIn("PLN_SCOPE_DENIED", titles)
		queue_ids = {row.get("demand") for row in payload.get("work_queue") or []}
		self.assertNotIn(foreign["demand"], queue_ids)

	def test_approved_demand_routes_to_preselected_add_dialog(self) -> None:
		planner = ensure_moh_planner()
		demand = make_approved_demand(
			pe=PE_MOH,
			ou=OU_MOH,
			title="Workspace route demand",
		)
		frappe.db.set_value(
			"Demand", demand["demand"], "required_by_date", "2027-12-01", update_modified=False
		)
		demand_row = frappe.db.get_value(
			"Demand",
			demand["demand"],
			["procuring_entity", "owner_org_unit", "status", "planning_ready", "required_by_date", "planning_usage"],
			as_dict=True,
		)
		self.assertEqual(demand_row.procuring_entity, PE_MOH)
		self.assertEqual(demand_row.owner_org_unit, OU_MOH)
		self.assertEqual(demand_row.status, "Approved")
		self.assertEqual(int(demand_row.planning_ready or 0), 1)
		self.assertEqual(str(demand_row.required_by_date), "2027-12-01")
		self.assertFalse(
			frappe.db.exists(
				"Plan Demand Allocation",
				{"demand": demand["demand"], "status": ["in", ["Draft", "Effective"]]},
			)
		)
		payload = get_planning_workspace(procuring_entity=PE_MOH, user=planner)
		approved = next(
			row for row in payload["work_queue"] if row.get("demand") == demand["demand"]
		)
		self.assertEqual(approved["action"]["label"], "Add to plan")
		self.assertIn(f"add_demand={demand['demand']}", approved["action"]["route"])
		self.assertIn("procurement-plan-approved", approved["action"]["route"])

		filtered = get_planning_workspace(
			procuring_entity=PE_MOH,
			user=planner,
			work_filter="approved_demands",
			search=demand["demand_code"],
		)
		self.assertEqual([row["demand"] for row in filtered["work_requiring_action"]], [demand["demand"]])

	def test_viewer_queue_has_no_finance_task_actions(self) -> None:
		"""PLN-GAP-PERM-002 — Viewer/Auditor get View only; no Confirm/Review return."""
		viewer = ensure_user_with_roles(
			"pln.gate03.queue.viewer@test.local",
			roles=(ROLE_VIEWER,),
			pe=PE_MOH,
			org_unit=OU_MOH,
			clear_scope=True,
		)
		payload = get_planning_workspace(procuring_entity=PE_MOH, user=viewer)
		self.assertTrue(payload.get("read_only"))
		self.assertEqual(payload.get("work_queue"), [])
		self.assertEqual(payload.get("work_requiring_action"), [])
		self.assertEqual(payload.get("waiting_on_others"), [])

	def test_zero_scope_blocked(self) -> None:
		email = ensure_user_with_roles(
			"pln.gate03.zero.ws@test.local",
			roles=(ROLE_PLANNER,),
			pe=None,
			clear_scope=True,
		)
		payload = get_planning_workspace(user=email)
		self.assertEqual(payload["selection_mode"], MODE_BLOCKED)
		self.assertIsNone(payload["current_plan"])

	def test_multi_pe_requires_selection(self) -> None:
		email = "pln.gate03.multi.ws@test.local"
		ensure_user_with_roles(
			email,
			roles=(ROLE_PLANNER,),
			pe=PE_MOH,
			org_unit=OU_MOH,
			clear_scope=True,
		)
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_PLANNER,
				"procuring_entity": PE_CGK,
				"organisation_unit": OU_CGK,
				"include_descendants": 1,
			}
		).insert(ignore_permissions=True)
		payload = get_planning_workspace(user=email)
		self.assertEqual(payload["selection_mode"], MODE_MULTI)
		self.assertIsNone(payload["procuring_entity"])
		chosen = get_planning_workspace(procuring_entity=PE_CGK, user=email)
		self.assertEqual(chosen["procuring_entity"], PE_CGK)

	def test_search_result_growth_does_not_add_per_row_sql(self) -> None:
		"""Returning more queue rows must not introduce a per-record query loop."""
		planner = ensure_moh_planner()
		for index in range(3):
			demand = make_approved_demand(
				pe=PE_MOH,
				ou=OU_MOH,
				title=f"Workspace query-growth demand {index}",
			)
			frappe.db.set_value(
				"Demand", demand["demand"], "required_by_date", "2027-12-01", update_modified=False
			)
		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as many_sql:
			many = get_planning_workspace(
				procuring_entity=PE_MOH,
				financial_year="2027/28",
				work_filter="approved_demands",
				search="Workspace query-growth demand",
				user=planner,
			)
		many_count = many_sql.call_count
		self.assertGreaterEqual(len(many["work_requiring_action"]), 3)
		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as one_sql:
			one = get_planning_workspace(
				procuring_entity=PE_MOH,
				financial_year="2027/28",
				work_filter="approved_demands",
				search="Workspace query-growth demand 0",
				user=planner,
			)
		self.assertGreaterEqual(len(one["work_requiring_action"]), 1)
		self.assertLessEqual(many_count, one_sql.call_count + 1)
