# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""Strategy Target v1.1 validation — timeframe (T1–T3), measurement (M3), draft guard (G2).

Run:
  bench --site <site> run-tests --app kentender_strategy --module kentender_strategy.tests.test_strategy_target_v11
"""

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate

from kentender_core.seeds._common import ensure_procuring_entity


class TestStrategyTargetV11(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.entity = ensure_procuring_entity("MOH", "Ministry of Health Test")
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Test Plan ST v11 {frappe.generate_hash(length=8)}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		)
		self.plan.insert(ignore_permissions=True)
		self.program = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan.name,
				"program_title": "P1",
				"order_index": 0,
			}
		)
		self.program.insert(ignore_permissions=True)
		self.objective = frappe.get_doc(
			{
				"doctype": "Strategy Objective",
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"objective_title": "O1",
				"order_index": 0,
			}
		)
		self.objective.insert(ignore_permissions=True)

	def _target_kwargs(self, **extra):
		kw = {
			"doctype": "Strategy Target",
			"strategic_plan": self.plan.name,
			"program": self.program.name,
			"objective": self.objective.name,
			"target_title": f"T {frappe.generate_hash(length=6)}",
			"order_index": 0,
			"measurement_type": "Numeric",
			"target_value_numeric": 10,
			"target_unit": "U",
		}
		kw.update(extra)
		return kw

	def test_t1_annual_year_in_plan_range_ok(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				target_period_type="Annual",
				target_year=2028,
				target_due_date=None,
			)
		)
		doc.insert(ignore_permissions=True)

	def test_t1_annual_year_out_of_range_fails(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				target_period_type="Annual",
				target_year=2035,
				target_due_date=None,
			)
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)

	def test_t1_annual_missing_year_fails(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				target_period_type="Annual",
				target_year=None,
				target_due_date=None,
			)
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)

	def test_t1_annual_with_due_date_fails(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				target_period_type="Annual",
				target_year=2028,
				target_due_date=getdate("2028-06-01"),
			)
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)

	def test_t2_end_of_plan_no_time_fields_ok(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				target_period_type="End of Plan",
				target_year=None,
				target_due_date=None,
			)
		)
		doc.insert(ignore_permissions=True)

	def test_t2_end_of_plan_with_year_fails(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				target_period_type="End of Plan",
				target_year=2028,
			)
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)

	def test_t3_milestone_requires_due_date(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				measurement_type="Milestone",
				target_value_text="done",
				target_value_numeric=None,
				target_unit=None,
				target_period_type="Milestone Date",
				target_year=None,
				target_due_date=None,
			)
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)

	def test_t3_milestone_ok(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				measurement_type="Milestone",
				target_value_text="Gate passed",
				target_value_numeric=None,
				target_unit=None,
				target_period_type="Milestone Date",
				target_year=None,
				target_due_date=getdate("2027-03-15"),
			)
		)
		doc.insert(ignore_permissions=True)

	def test_m3_percentage_normalizes_percent_unit(self):
		doc = frappe.get_doc(
			self._target_kwargs(
				measurement_type="Percentage",
				target_value_numeric=50,
				target_unit="Ignored",
				target_period_type="Annual",
				target_year=2028,
			)
		)
		doc.insert(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.target_unit, "Percent")

	def test_g2_active_plan_blocks_insert(self):
		self.plan.status = "Active"
		self.plan.save(ignore_permissions=True)
		doc = frappe.get_doc(
			self._target_kwargs(
				target_period_type="Annual",
				target_year=2028,
			)
		)
		with self.assertRaises(ValidationError):
			doc.insert(ignore_permissions=True)
