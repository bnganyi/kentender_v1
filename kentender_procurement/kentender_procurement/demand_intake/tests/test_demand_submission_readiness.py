# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Submission readiness — staged validation without mandatory budget line."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.services.readiness import (
	assert_submission_ready,
	evaluate_submission_readiness,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy


class TestDemandSubmissionReadiness(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = upsert_works_master_strategy_hierarchy()

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		self.entity = self.seed["procuring_entity"]
		self.dept = ensure_department(f"Dept Sub {frappe.generate_hash(length=6)}", self.entity)
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
		# Do not delete seeded MOH procuring entity

	def _mk_demand(self, **kwargs):
		# Goods + strategy target: Required PVCs are category-filtered out on MOH seed
		if "strategy_target" not in kwargs:
			kwargs["strategy_target"] = self.seed["target"]
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"Sub {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": "Goods",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"beneficiary_summary": "Benefit",
				"specification_summary": "Scope summary",
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

	def test_planned_demand_ready_without_budget_line(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand(budget_line=None)
		out = evaluate_submission_readiness(doc)
		self.assertTrue(out["ready"])
		budget_check = next(c for c in out["checks"] if c["id"] == "budget_line")
		self.assertFalse(budget_check["ok"])
		self.assertFalse(budget_check["required"])
		assert_submission_ready(doc)

	def test_unplanned_requires_beneficiary_and_specification(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand(demand_type="Unplanned", specification_summary="", beneficiary_summary="")
		out = evaluate_submission_readiness(doc)
		self.assertFalse(out["ready"])
		with self.assertRaises(frappe.ValidationError):
			assert_submission_ready(doc)

	def test_item_row_requires_category(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		doc = self._mk_demand(
			items=[
				{
					"item_description": "Line",
					"category": "",
					"uom": "ea",
					"quantity": 1,
					"estimated_unit_cost": 100,
				}
			]
		)
		out = evaluate_submission_readiness(doc)
		self.assertFalse(out["ready"])
