# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Review-stage validation — return/reject reasons and approve gates (§24.3)."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.lifecycle import (
	approve_finance,
	approve_hod,
	reject_from_hod,
	return_from_hod,
)
from kentender_procurement.demand_intake.services.readiness import evaluate_review_action


class TestDemandReviewValidation(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_REV_{h}", f"Entity Rev {h}")
		self.dept = ensure_department(f"Dept Rev {h}", self.entity)
		self._demand_names: list[str] = []

	def tearDown(self):
		if getattr(self, "_skipped_no_demand", False):
			return
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		dept = getattr(self, "dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)
		ent = getattr(self, "entity", None)
		if ent and frappe.db.exists("Procuring Entity", ent):
			frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)

	def _mk_demand(self, **kwargs):
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"Rev {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": "Goods",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"beneficiary_summary": "Benefit",
				"specification_summary": "Scope",
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 100,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc

	def test_return_requires_reason(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand(requested_by="Administrator", status="Draft")
		frappe.db.set_value("Demand", doc.name, "status", "Pending HoD Approval", update_modified=False)
		out = evaluate_review_action(doc, action="return")
		self.assertFalse(out["ready"])
		with self.assertRaises(frappe.ValidationError):
			return_from_hod(doc.name, reason="")

	def test_reject_requires_reason(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand(requested_by="Administrator", status="Draft")
		frappe.db.set_value("Demand", doc.name, "status", "Pending HoD Approval", update_modified=False)
		with self.assertRaises(frappe.ValidationError):
			reject_from_hod(doc.name, rejection_reason="")

	def test_hod_approve_without_budget(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"hod_rev_{frappe.generate_hash(length=4)}@test.local"
		hod = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "HoD",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		hod.insert(ignore_permissions=True)
		hod.add_roles("Department Approver")
		doc = self._mk_demand(requested_by="Administrator", status="Draft", budget_line=None)
		frappe.db.set_value("Demand", doc.name, "status", "Pending HoD Approval", update_modified=False)
		try:
			frappe.set_user(hod.name)
			out = approve_hod(doc.name)
			self.assertEqual(out["status"], "Pending Finance Approval")
			doc.reload()
			self.assertFalse(doc.budget_line)
			self.assertEqual(doc.planning_status, "Not Planned")
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", hod.name):
				frappe.delete_doc("User", hod.name, force=True, ignore_permissions=True)

	def test_finance_approve_requires_budget(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand(requested_by="Administrator", status="Draft", budget_line=None)
		frappe.db.set_value("Demand", doc.name, "status", "Pending Finance Approval", update_modified=False)
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			approve_finance(doc.name)
