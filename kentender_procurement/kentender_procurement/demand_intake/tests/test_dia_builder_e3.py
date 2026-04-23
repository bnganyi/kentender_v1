# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""E3 — Basic Request + Items edit flag on form header API (`basic_items_editable`).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_builder_e3
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.dia_detail import get_dia_demand_form_header


class TestDiaBuilderE3(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_E3_{h}", f"Entity E3 {h}")
		self.dept = ensure_department(f"Dept E3 {h}", self.entity)
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

	def _mk_demand(self, **kwargs) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"E3 {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 10,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc.name

	def test_header_empty_name_is_editable(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		out = get_dia_demand_form_header("")
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("basic_items_editable"))

	def test_header_draft_and_rejected_editable(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		name = self._mk_demand(status="Draft")
		out = get_dia_demand_form_header(name)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("basic_items_editable"))

		frappe.db.set_value("Demand", name, "status", "Rejected", update_modified=False)
		out2 = get_dia_demand_form_header(name)
		self.assertTrue(out2.get("basic_items_editable"))

	def test_header_non_editable_states(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		name = self._mk_demand(status="Draft")
		for st in (
			"Pending HoD Approval",
			"Pending Finance Approval",
			"Approved",
			"Planning Ready",
			"Cancelled",
		):
			frappe.db.set_value("Demand", name, "status", st, update_modified=False)
			out = get_dia_demand_form_header(name)
			self.assertTrue(out.get("ok"), msg=st)
			self.assertFalse(
				out.get("basic_items_editable"),
				msg=f"expected locked for status={st}",
			)
