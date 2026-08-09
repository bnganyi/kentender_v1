# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-001 — get_planning_workspace API (PE-scope matrix)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

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
	PE_FILTER_ALL,
	ROLE_PLANNER,
	ROLE_VIEWER,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	OU_CGK,
	OU_MOH,
	PE_CGK,
	PE_MOH,
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

	def test_support_viewer_read_only_all_entities(self) -> None:
		"""Planning Viewer (support) sees sample data; create stays blocked."""
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
		self.assertEqual(payload["procuring_entity"], PE_FILTER_ALL)
		self.assertEqual(payload["selection_mode"], MODE_MULTI)
		ids = {e["id"] for e in payload["procuring_entities"]}
		self.assertIn(PE_FILTER_ALL, ids)
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
		self.assertIn(
			PE_FILTER_ALL,
			{e["id"] for e in payload["procuring_entities"]},
		)

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
		self.assertIsInstance(payload["work_queue"], list)
		self.assertTrue(payload.get("helper_text"))
		# Whitelist entry also callable
		frappe.set_user(planner)
		try:
			api_payload = api_get_planning_workspace(
				procuring_entity=PE_MOH, financial_year="2027/28"
			)
		finally:
			frappe.set_user("Administrator")
		self.assertTrue(api_payload["ok"])

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
