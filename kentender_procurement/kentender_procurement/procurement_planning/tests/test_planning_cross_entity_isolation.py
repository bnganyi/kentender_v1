# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-PERM-005 — MOH vs County PE isolation."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.create_procurement_plan import (
	create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_planning_scope,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	make_approved_demand,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	OU_CGK,
	OU_MOH,
	PE_CGK,
	PE_MOH,
	ensure_county_planner,
	ensure_moh_planner,
	ensure_org,
)


class TestPlanningCrossEntityIsolation(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()

	def test_moh_planner_cannot_access_county_scope(self) -> None:
		planner = ensure_moh_planner()
		with self.assertRaises(frappe.PermissionError):
			assert_planning_scope(
				procuring_entity=PE_CGK,
				org_unit=OU_CGK,
				user=planner,
				require_write=True,
			)

	def test_county_planner_cannot_mutate_moh_plan(self) -> None:
		moh_planner = ensure_moh_planner()
		county = ensure_county_planner()
		fy = f"214{frappe.db.count('Procurement Plan') % 9}/55"
		for name in frappe.get_all(
			"Procurement Plan",
			filters={"procuring_entity": PE_MOH, "financial_year": fy},
			pluck="name",
		):
			frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		created = create_procurement_plan(
			procuring_entity=PE_MOH,
			financial_year=fy,
			title="MOH isolation plan",
			currency="KES",
			coordinating_org_unit=OU_MOH,
			user=moh_planner,
		)
		demand = make_approved_demand(title="Isolation demand")
		with self.assertRaises(frappe.PermissionError):
			add_demand_to_plan(
				plan=created["plan"],
				demand=demand["demand"],
				user=county,
			)

	def test_county_planner_can_create_county_plan(self) -> None:
		county = ensure_county_planner()
		fy = f"213{frappe.db.count('Procurement Plan') % 9}/56"
		for name in frappe.get_all(
			"Procurement Plan",
			filters={"procuring_entity": PE_CGK, "financial_year": fy},
			pluck="name",
		):
			frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		result = create_procurement_plan(
			procuring_entity=PE_CGK,
			financial_year=fy,
			title="County plan",
			currency="KES",
			coordinating_org_unit=OU_CGK,
			user=county,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(
			frappe.db.get_value("Procurement Plan", result["plan"], "procuring_entity"),
			PE_CGK,
		)
