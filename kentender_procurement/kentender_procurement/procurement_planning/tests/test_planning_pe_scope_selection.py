# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-PERM-004 — zero / single / multi PE selection for plan create."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.create_procurement_plan import (
	create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	ROLE_PLANNER,
	assert_pe_resolved_for_create,
	resolve_pe_for_create,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	purge_pe_fy,
	unique_test_fy,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	OU_CGK,
	OU_MOH,
	PE_CGK,
	PE_MOH,
	ensure_moh_planner,
	ensure_org,
	ensure_user_with_roles,
)


class TestPlanningPeScopeSelection(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def test_zero_scope_blocks_create(self) -> None:
		email = ensure_user_with_roles(
			"pln.gate02.zero.scope@test.local",
			roles=(ROLE_PLANNER,),
			pe=None,
			clear_scope=True,
		)
		scope = resolve_pe_for_create(email)
		self.assertEqual(scope["selection_mode"], MODE_BLOCKED)
		with self.assertRaises(frappe.PermissionError):
			assert_pe_resolved_for_create(user=email)
		with self.assertRaises(frappe.PermissionError):
			create_procurement_plan(
				procuring_entity=PE_MOH,
				financial_year="2150/51",
				title="Zero scope",
				currency="KES",
				coordinating_org_unit=OU_MOH,
				user=email,
			)

	def test_single_pe_forces_assignment(self) -> None:
		"""PLN-AC-001 — one PE stays the assigned entity; caller cannot invent another."""
		planner = ensure_moh_planner()
		scope = resolve_pe_for_create(planner, selected_pe=None)
		self.assertEqual(scope["selection_mode"], MODE_SINGLE)
		self.assertEqual(scope["procuring_entity"], PE_MOH)
		# Even if caller passes a different PE, create forces the assigned PE.
		fy = unique_test_fy(base_year=2160, bucket=int(frappe.db.count("Procurement Plan") or 0))
		purge_pe_fy(fy)
		result = create_procurement_plan(
			procuring_entity=PE_CGK,  # wrong — must be overridden
			financial_year=fy,
			title="Single PE force",
			currency="KES",
			coordinating_org_unit=OU_MOH,
			user=planner,
		)
		self.assertTrue(result["ok"])
		pe = frappe.db.get_value("Procurement Plan", result["plan"], "procuring_entity")
		self.assertEqual(pe, PE_MOH)

	def test_multi_pe_requires_explicit_selection(self) -> None:
		email = "pln.gate02.multi.pe@test.local"
		ensure_user_with_roles(
			email,
			roles=(ROLE_PLANNER,),
			pe=PE_MOH,
			org_unit=OU_MOH,
			clear_scope=True,
		)
		# Second PE assignment
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
		scope = resolve_pe_for_create(email)
		self.assertEqual(scope["selection_mode"], MODE_MULTI)
		self.assertIsNone(scope["procuring_entity"])
		with self.assertRaises(frappe.ValidationError):
			assert_pe_resolved_for_create(user=email, selected_pe=None)
		pe = assert_pe_resolved_for_create(user=email, selected_pe=PE_CGK)
		self.assertEqual(pe, PE_CGK)
