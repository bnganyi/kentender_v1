# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Governance v1 — plan Returned workflow and completeness helpers."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import constants as C
from kentender_procurement.procurement_planning.api import workflow
from kentender_procurement.procurement_planning.services.package_completeness import (
	get_package_completeness_blockers,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPpGovernanceSpec(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_return_plan_sets_returned(self):
		if not _pp_ok():
			self.skipTest("PP not installed")
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "Gov return test",
				"plan_code": f"PP-RTN-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": "Submitted",
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.commit()
		try:
			out = workflow.return_plan(plan.name, reason="Test return for governance.")
			self.assertEqual(out.get("status"), "Returned")
		finally:
			frappe.delete_doc("Procurement Plan", plan.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_completeness_blockers_without_lines(self):
		if not _pp_ok():
			self.skipTest("PP not installed")
		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			self.skipTest("no template")
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "Gov completeness",
				"plan_code": f"PP-CMP-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": "Draft",
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		pkg = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_name": "Completeness probe",
				"plan_id": plan.name,
				"template_id": tpl[0],
				"procurement_method": "Direct Procurement",
				"contract_type": "Fixed Price",
				"currency": "KES",
				"risk_profile_id": frappe.get_all("Risk Profile", limit=1, pluck="name")[0],
				"kpi_profile_id": frappe.get_all("KPI Profile", limit=1, pluck="name")[0],
				"vendor_management_profile_id": frappe.get_all("Vendor Management Profile", limit=1, pluck="name")[
					0
				],
				"status": "Draft",
				"is_active": 1,
			}
		)
		pkg.insert(ignore_permissions=True)
		frappe.db.commit()
		try:
			pkg.reload()
			b = get_package_completeness_blockers(pkg)
			self.assertTrue(len(b) >= 1)
		finally:
			frappe.delete_doc("Procurement Package", pkg.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Procurement Plan", plan.name, force=True, ignore_permissions=True)
			frappe.db.commit()
