# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2-REG-001 — Planning does not mutate upstream demand authority."""

from __future__ import annotations

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.demand_journey_bootstrap import (
	ensure_procurement_journey_for_demand_code,
)
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.tests.pp2_reg_regression_helpers import (
	demand_authority_snapshot,
	mk_active_plan,
	mk_approved_demand,
	require_active_template,
	seed_budget_line,
)


class TestPP2RegDemandSourceAuthority(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not demand_consumers_live() or not frappe.db.exists("DocType", "Procurement Plan"):
			self._skip = True
			return
		self._skip = False
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if doctype == "Procurement Journey":
				frappe.db.sql("DELETE FROM `tabProcurement Journey` WHERE name=%s", name)
				continue
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_pp2_reg_001_planning_pipeline_preserves_demand_authority(self) -> None:
		if self._skip:
			self.skipTest("Demand or Procurement Plan not installed")
		from kentender_procurement.procurement_planning.tests.pp2_reg_regression_helpers import (
			require_active_template,
		)

		if not require_active_template():
			self.skipTest("No active Procurement Template with profiles available")

		bl_name, entity, dept, _ = seed_budget_line()
		if not bl_name:
			self.skipTest("No active budget line available")
		plan_name = mk_active_plan(self._cleanup)
		demand = mk_approved_demand(bl_name, entity, dept, self._cleanup)
		before = demand_authority_snapshot(demand.name)
		frappe.db.commit()

		journey_code = ensure_procurement_journey_for_demand_code(demand.demand_id) or ""
		if journey_code:
			self._cleanup.append(("Procurement Journey", journey_code))
		incl = include_demand_in_procurement_plan(
			demand.demand_id,
			[f"DEMITEM-P7-{frappe.generate_hash()[:8]}"],
			plan_name,
			"Administrator",
		)
		inclusion_code = incl.get("inclusion_code") or ""
		if inclusion_code:
			self._cleanup.append(("Procurement Handoff Card", inclusion_code))
		pkg_out = create_package_from_planning_inclusion(inclusion_code, "Administrator")
		package_code = pkg_out.get("package_code") or ""
		self.assertTrue(package_code, msg=f"Package creation failed: {pkg_out}")
		self._cleanup.append(("Procurement Package", package_code))
		for lc in pkg_out.get("package_line_codes") or []:
			self._cleanup.append(("Procurement Package Line", lc))

		after = demand_authority_snapshot(demand.name)
		self.assertEqual(before, after, msg="Planning pipeline must not mutate demand authority fields")
