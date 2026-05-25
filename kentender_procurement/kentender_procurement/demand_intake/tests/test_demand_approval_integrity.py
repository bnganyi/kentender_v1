# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Approved ⇒ Reserved invariant, integrity evaluation, return-to-finance (Phase L1)."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.lifecycle import return_approved_to_finance
from kentender_procurement.demand_intake.api.review import get_demand_review_data
from kentender_procurement.demand_intake.services.readiness import evaluate_approval_integrity


class TestDemandApprovalIntegrity(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_INT_{h}", f"Entity Int {h}")
		self.dept = ensure_department(f"Dept Int {h}", self.entity)
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

	def _seed_budget_line(self):
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		dept = ensure_department(f"Dept Int BL {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_demand(self, bl_name, entity, dept, **kwargs):
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"Int {frappe.generate_hash(length=4)}",
				"procuring_entity": entity,
				"requesting_department": dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": "Goods",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"specification_summary": "Scope",
				"budget_line": bl_name,
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

	def test_approved_without_reservation_fails_validate(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")
		doc = self._mk_demand(bl_name, entity, dept)
		frappe.db.set_value(
			"Demand",
			doc.name,
			{
				"status": "Approved",
				"reservation_status": "None",
				"hod_approved_by": "Administrator",
				"hod_approved_at": today(),
				"finance_approved_by": "Administrator",
				"finance_approved_at": today(),
			},
			update_modified=False,
		)
		doc.reload()
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_evaluate_approval_integrity_reports_missing_reservation(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")
		doc = self._mk_demand(bl_name, entity, dept)
		frappe.db.set_value(
			"Demand",
			doc.name,
			{"status": "Approved", "reservation_status": "None"},
			update_modified=False,
		)
		doc.reload()
		out = evaluate_approval_integrity(doc)
		self.assertTrue(out.get("blocked"))
		self.assertGreaterEqual(out.get("blocker_count") or 0, 1)
		blockers = out.get("blockers") or []
		res_blocker = next((b for b in blockers if b.get("id") == "budget_reservation"), None)
		self.assertIsNotNone(res_blocker)
		self.assertFalse(res_blocker.get("ok"))

	def test_return_approved_to_finance_clears_finance_and_reservation(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")
		doc = self._mk_demand(bl_name, entity, dept)
		frappe.db.set_value(
			"Demand",
			doc.name,
			{
				"status": "Approved",
				"reservation_status": "Reserved",
				"reservation_reference": "RES-INTEGRITY-TEST",
				"hod_approved_by": "Administrator",
				"hod_approved_at": today(),
				"finance_approved_by": "Administrator",
				"finance_approved_at": today(),
			},
			update_modified=False,
		)
		doc.reload()
		return_approved_to_finance(doc.name, reason="Missing reservation integrity repair")
		doc.reload()
		self.assertEqual(doc.status, "Pending Finance Approval")
		self.assertIsNone(doc.finance_approved_by)
		self.assertIsNone(doc.finance_approved_at)
		self.assertEqual(doc.hod_approved_by, "Administrator")
		self.assertIn(doc.reservation_status, ("Released", "None"))

	def test_review_data_uses_approved_outcome_view(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")
		doc = self._mk_demand(bl_name, entity, dept)
		frappe.db.set_value(
			"Demand",
			doc.name,
			{
				"status": "Approved",
				"reservation_status": "Reserved",
				"reservation_reference": "RES-REVIEW-TEST",
				"hod_approved_by": "Administrator",
				"hod_approved_at": today(),
				"finance_approved_by": "Administrator",
				"finance_approved_at": today(),
			},
			update_modified=False,
		)
		doc.reload()
		out = get_demand_review_data(doc.name)
		self.assertEqual(out.get("review_view"), "approved_outcome")
		self.assertIsNotNone(out.get("approval_outcome"))
		self.assertIsNone(out.get("review_action_readiness"))
