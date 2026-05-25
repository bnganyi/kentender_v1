# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 governance — plan cancel workflow and completeness helpers."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import constants as C
from kentender_procurement.procurement_planning.api import workflow
from kentender_procurement.procurement_planning.pp2_constants import PLAN_CANCELLED, PLAN_DRAFT, PKG_DRAFT
from kentender_procurement.procurement_planning.services.package_completeness import (
	get_package_completeness_blockers,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPpGovernanceSpec(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_cancel_plan_sets_cancelled(self):
		if not _pp_ok():
			self.skipTest("PP not installed")
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "Gov cancel test",
				"plan_code": f"PP-CNL-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		frappe.db.commit()
		try:
			out = workflow.cancel_plan(plan.name, reason="Test cancel for governance.")
			self.assertEqual(out.get("status"), PLAN_CANCELLED)
		finally:
			frappe.delete_doc("Procurement Plan", plan.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_completeness_blockers_without_lines(self):
		if not _pp_ok():
			self.skipTest("PP not installed")
		tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
		if not tpl:
			self.skipTest("no template")
		dcp = frappe.get_all("Decision Criteria Profile", limit=1, pluck="name")
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "Gov completeness",
				"plan_code": f"PP-CMP-{frappe.generate_hash()[:6]}",
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_DRAFT,
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
				"decision_criteria_profile_id": dcp[0] if dcp else None,
				"status": PKG_DRAFT,
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
