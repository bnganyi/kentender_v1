# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""E5/E6 — Demand submission gate mirrors exception rules (server).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_builder_e5_e6
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_budget.api.dia_budget_control import get_budget_line_context


class TestDiaBuilderE5E6(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		dept = getattr(self, "_dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)

	def _bl_and_entity(self):
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl_name:
			return None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None
		ent = (ctx.get("data") or {}).get("procuring_entity")
		return bl_name, ent

	def _base_demand_kwargs(self, bl_name: str, entity: str) -> dict:
		ensure_currency_kes()
		self._dept = ensure_department(f"Dept E56 {frappe.generate_hash(length=4)}", entity)
		return {
			"doctype": "Demand",
			"title": "E56 gate",
			"procuring_entity": entity,
			"requesting_department": self._dept,
			"request_date": today(),
			"required_by_date": today(),
			"specification_summary": "Spec",
			"delivery_location": "HQ",
			"requested_delivery_period_days": 14,
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
		}

	def test_unplanned_submission_gate_requires_beneficiary_and_impact(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		bl_name, entity = self._bl_and_entity()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")

		self._demand_names = []
		doc = frappe.get_doc({**self._base_demand_kwargs(bl_name, entity), "demand_type": "Unplanned"})
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)

		doc.beneficiary_summary = ""
		doc.impact_if_not_procured = ""
		with self.assertRaises(frappe.ValidationError):
			doc.validate_submission_gate()

	def test_emergency_submission_gate_requires_emergency_justification(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		bl_name, entity = self._bl_and_entity()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")

		self._demand_names = []
		doc = frappe.get_doc({**self._base_demand_kwargs(bl_name, entity), "demand_type": "Emergency"})
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)

		doc.beneficiary_summary = "Patients"
		doc.impact_if_not_procured = "High"
		doc.emergency_justification = ""
		with self.assertRaises(frappe.ValidationError):
			doc.validate_submission_gate()

	def test_planned_submission_gate_ok_without_impact_text(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		bl_name, entity = self._bl_and_entity()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")

		self._demand_names = []
		doc = frappe.get_doc({**self._base_demand_kwargs(bl_name, entity), "demand_type": "Planned"})
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)

		doc.beneficiary_summary = ""
		doc.impact_if_not_procured = ""
		doc.emergency_justification = ""
		doc.validate_submission_gate()
