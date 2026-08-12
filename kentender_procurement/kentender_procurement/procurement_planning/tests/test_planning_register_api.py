# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-02 / create-scope + create_procurement_plan whitelist."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api import (
	create_procurement_plan,
	get_planning_create_scope,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder,
)
from kentender_procurement.procurement_planning.services.get_planning_create_scope import (
	get_planning_create_scope as scope_svc,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	ROLE_PLANNER,
)
from kentender_procurement.procurement_planning.seeds.pln_seed_004_empty_draft import (
	UI_PLAN_CODE,
	ensure_empty_draft_plan_fixture,
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


class TestPlanningRegisterApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def test_create_scope_single_pe_readonly(self) -> None:
		planner = ensure_moh_planner()
		scope = scope_svc(user=planner)
		self.assertEqual(scope["selection_mode"], MODE_SINGLE)
		self.assertEqual(scope["procuring_entity"], PE_MOH)
		self.assertFalse(scope["has_budget_fields"])
		self.assertTrue(scope["period_start"])
		self.assertTrue(scope["period_end"])

	def test_create_scope_zero_blocked(self) -> None:
		email = ensure_user_with_roles(
			"pln.gate03.zero.reg@test.local",
			roles=(ROLE_PLANNER,),
			pe=None,
			clear_scope=True,
		)
		scope = scope_svc(user=email)
		self.assertEqual(scope["selection_mode"], MODE_BLOCKED)

	def test_create_scope_multi(self) -> None:
		email = "pln.gate03.multi.reg@test.local"
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
		scope = scope_svc(user=email)
		self.assertEqual(scope["selection_mode"], MODE_MULTI)
		self.assertIsNone(scope["procuring_entity"])
		chosen = scope_svc(user=email, selected_pe=PE_CGK)
		self.assertEqual(chosen["procuring_entity"], PE_CGK)

	def test_create_missing_fields_returns_errors(self) -> None:
		planner = ensure_moh_planner()
		frappe.set_user(planner)
		try:
			result = create_procurement_plan(
				procuring_entity=PE_MOH,
				financial_year="",
				title="",
				currency="KES",
				coordinating_org_unit="",
			)
		finally:
			frappe.set_user("Administrator")
		self.assertFalse(result["ok"])
		self.assertIn("financial_year", result["errors"])
		self.assertIn("title", result["errors"])
		self.assertIn("coordinating_org_unit", result["errors"])

	def test_create_happy_path_redirects_to_builder(self) -> None:
		planner = ensure_moh_planner()
		fy = f"212{frappe.db.count('Procurement Plan') % 9}/90"
		fy_code = fy.replace("/", "-")
		# Versions can outlive plans if a prior run aborted mid-create — clear both.
		for name in frappe.get_all(
			"Procurement Plan Version",
			filters={"name": ["like", f"PLN-MOH-{fy_code}-%"]},
			pluck="name",
		):
			frappe.delete_doc("Procurement Plan Version", name, force=True, ignore_permissions=True)
		for name in frappe.get_all(
			"Procurement Plan",
			filters={"procuring_entity": PE_MOH, "financial_year": fy},
			pluck="name",
		):
			frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		frappe.set_user(planner)
		try:
			result = create_procurement_plan(
				procuring_entity=PE_MOH,
				financial_year=fy,
				title="Gate03 Register Plan",
				currency="KES",
				coordinating_org_unit=OU_MOH,
			)
		finally:
			frappe.set_user("Administrator")
		self.assertTrue(result.get("ok"), msg=str(result))
		self.assertIn("procurement-plan-builder", result.get("redirect", ""))
		self.assertNotIn("budget", str(result).lower().split("coordinating")[0])

	def test_admin_cannot_create_via_api(self) -> None:
		admin = ensure_admin_only()
		frappe.set_user(admin)
		try:
			result = create_procurement_plan(
				procuring_entity=PE_MOH,
				financial_year="2111/12",
				title="Admin blocked",
				currency="KES",
				coordinating_org_unit=OU_MOH,
			)
		finally:
			frappe.set_user("Administrator")
		self.assertFalse(result.get("ok"))

	def test_seed004_empty_builder(self) -> None:
		planner = ensure_moh_planner()
		fixture = ensure_empty_draft_plan_fixture(commit=True)
		self.assertEqual(fixture["plan_code"], UI_PLAN_CODE)
		builder = get_plan_builder(plan=fixture["plan"], user=planner)
		self.assertTrue(builder["ok"])
		self.assertTrue(builder["empty"])
		self.assertEqual(builder["item_count"], 0)
		self.assertFalse(builder.get("add_demand_pending_gate"))
