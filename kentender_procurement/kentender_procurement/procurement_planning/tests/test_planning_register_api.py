# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Approved PLN-UI-02 registration contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api import create_procurement_plan
from kentender_procurement.procurement_planning.services.create_procurement_plan import (
	create_procurement_plan as create_svc,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import get_plan_builder
from kentender_procurement.procurement_planning.services.get_planning_create_scope import (
	get_planning_create_scope,
)
from kentender_procurement.procurement_planning.services.planning_permissions import ROLE_PLANNER
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	PE_MOH,
	ensure_admin_only,
	ensure_org,
	ensure_user_with_roles,
)

FY = "2028/29"


def _planner() -> str:
	return ensure_user_with_roles(
		"pln.revision.register@test.local",
		roles=(ROLE_PLANNER,),
		pe=PE_MOH,
		org_unit=None,
		include_descendants=1,
	)


class TestPlanningRegisterApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def test_scope_is_explicit_and_contains_five_governed_values(self) -> None:
		scope = get_planning_create_scope(
			procuring_entity=PE_MOH, financial_year=FY, user=_planner()
		)
		self.assertTrue(scope["ok"])
		self.assertEqual(scope["financial_year"], FY)
		self.assertEqual(scope["currency"], "KES")
		self.assertEqual(scope["title"], "Ministry of Health Annual Procurement Plan 2028/29")
		self.assertEqual(scope["period_start"], "2028-07-01")
		self.assertEqual(scope["period_end"], "2029-06-30")
		self.assertEqual(len(scope["identity_values"]), 5)

	def test_scope_requires_explicit_context(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			get_planning_create_scope(
				procuring_entity="", financial_year=FY, user=_planner()
			)

	def test_admin_without_assignment_is_denied(self) -> None:
		with self.assertRaises(frappe.PermissionError):
			get_planning_create_scope(
				procuring_entity=PE_MOH,
				financial_year=FY,
				user=ensure_admin_only(),
			)

	def test_api_accepts_only_pe_and_fy(self) -> None:
		frappe.set_user(_planner())
		try:
			with self.assertRaises(TypeError):
				create_procurement_plan(
					procuring_entity=PE_MOH,
					financial_year=FY,
					title="Client-authored title",  # type: ignore[call-arg]
				)
		finally:
			frappe.set_user("Administrator")

	def test_atomic_create_is_idempotent_and_side_effect_free(self) -> None:
		planner = _planner()
		first = create_svc(procuring_entity=PE_MOH, financial_year=FY, user=planner)
		second = create_svc(procuring_entity=PE_MOH, financial_year=FY, user=planner)
		self.assertTrue(first["created"])
		self.assertFalse(second["created"])
		self.assertEqual(first["plan"], second["plan"])
		self.assertEqual(first["plan_code"], "PLN-MOH-2028-001")
		self.assertEqual(first["version_code"], "PLN-MOH-2028-001-V1")
		self.assertEqual(
			frappe.db.count("Procurement Plan", {"procuring_entity": PE_MOH, "financial_year": FY}),
			1,
		)
		self.assertEqual(frappe.db.count("Procurement Plan Item", {"plan": first["plan"]}), 0)
		self.assertEqual(frappe.db.count("Plan Decision", {"plan_version": first["version"]}), 1)
		builder = get_plan_builder(plan=first["plan"], user=planner)
		self.assertEqual(builder["state_id"], "PLN-UI-03")
		self.assertEqual(builder["item_count"], 0)

	def test_missing_fields_return_accessible_api_errors(self) -> None:
		frappe.set_user(_planner())
		try:
			result = create_procurement_plan(procuring_entity=PE_MOH, financial_year="")
		finally:
			frappe.set_user("Administrator")
		self.assertFalse(result["ok"])
		self.assertIn("financial_year", result["errors"])
