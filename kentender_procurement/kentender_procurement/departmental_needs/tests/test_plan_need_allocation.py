from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import OU, PE, PLANNER, REQUESTER, upsert_departmental_needs
from kentender_procurement.departmental_needs.services.usage import planning_usage
from kentender_procurement.procurement_planning.services.need_allocations import (
	activate_need_allocations, allocate_need_lines, list_eligible_needs, reverse_need_allocations,
)


class TestPlanNeedAllocation(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def test_draft_effective_and_reversed_usage_projection(self):
		suffix = uuid4().hex[:8].upper()
		fy = next(row for row in enabled_fiscal_years() if row["is_current"])["id"]
		need = frappe.get_doc({"doctype": "Departmental Need", "need_reference": f"NDS-MOH-{fy[:4]}-{suffix[:3]}", "title": "Partially allocated test Need",
			"procuring_entity": PE, "organisation_unit": OU, "target_financial_year": fy, "submitted_by": REQUESTER,
			"business_justification": "Allocation projection test", "required_by_date": enabled_fiscal_years()[0]["end_date"],
			"delivery_or_use_location": "MOH", "status": "Draft", "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		line = frappe.get_doc({"doctype": "Departmental Need Item", "item_reference": f"{need.name}-001", "departmental_need": need.name,
			"line_number": 1, "description": "Ten sets", "indicative_quantity": 10, "unit": "sets"}).insert(ignore_permissions=True)
		frappe.db.set_value("Departmental Need", need.name, "status", "Accepted for planning", update_modified=False)
		plan = frappe.get_doc({"doctype": "Procurement Plan", "plan_code": f"PLN-NDS-{suffix}", "title": "NDS allocation test Plan", "procuring_entity": PE,
			"financial_year": fy, "currency": "KES", "plan_type": "Annual", "lifecycle_state": "Open"}).insert(ignore_permissions=True)
		version = frappe.get_doc({"doctype": "Procurement Plan Version", "plan": plan.name, "version_number": 1, "version_code": f"{plan.name}-V1",
			"status": "Draft", "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "open_draft_version", version.name, update_modified=False)
		item = frappe.get_doc({"doctype": "Procurement Plan Item", "plan": plan.name, "plan_item_code": f"PPI-NDS-{suffix}", "procuring_entity": PE,
			"owner_org_unit": OU, "baseline_state": "Proposed"}).insert(ignore_permissions=True)
		eligible = list_eligible_needs(plan=plan.name, user=PLANNER)
		self.assertIn(need.name, [row["need"] for row in eligible["needs"]])
		result = allocate_need_lines(plan=plan.name, plan_item=item.name,
			allocations=[{"departmental_need_item": line.name, "allocated_quantity": 4}],
			expected_version_token=version.concurrency_token, idempotency_key=f"NDS-ALLOC-{suffix}", user=PLANNER)
		allocation = frappe.get_doc("Plan Need Allocation", result["allocations"][0])
		self.assertEqual(allocation.departmental_need, need.name)
		self.assertEqual(allocation.departmental_need_item, line.name)
		self.assertEqual(allocation.status, "Draft")
		self.assertEqual(planning_usage(need.name), "Not included")
		with self.assertRaises(frappe.ValidationError):
			allocate_need_lines(plan=plan.name, plan_item=item.name,
				allocations=[{"departmental_need_item": line.name, "allocated_quantity": 7}],
				expected_version_token=result["concurrency_token"], idempotency_key=f"NDS-OVER-{suffix}", user=PLANNER)
		activate_need_allocations(version=version.name)
		self.assertEqual(planning_usage(need.name), "Partially included")
		reverse_need_allocations(plan_item=item.name, version=version.name, reason="Approved amendment")
		self.assertEqual(planning_usage(need.name), "Not included")
		self.assertEqual(len(result["allocations"]), 1)
