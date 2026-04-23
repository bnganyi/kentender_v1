# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""E1 — Demand Form header API (`get_dia_demand_form_header`).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_form_header_e1
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.dia_detail import get_dia_demand_form_header


class TestDiaFormHeaderE1(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_E1_{h}", f"Entity E1 {h}")
		self.dept = ensure_department(f"Dept E1 {h}", self.entity)
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
				"title": kwargs.pop("title", None) or f"E1 {frappe.generate_hash(length=4)}",
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

	def test_form_header_empty_name(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		out = get_dia_demand_form_header("")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("actions"), [])
		self.assertTrue(out.get("basic_items_editable"))

	def test_form_header_omits_open_form_includes_submit(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"req_e1_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "E1",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Requisitioner")
		try:
			frappe.set_user(user.name)
			name = self._mk_demand(requested_by=user.name, status="Draft")
			out = get_dia_demand_form_header(name)
			self.assertTrue(out.get("ok"))
			ids = {a.get("id") for a in (out.get("actions") or [])}
			self.assertNotIn("open_form", ids)
			self.assertIn("submit_demand", ids)
			self.assertEqual(out.get("status"), "Draft")
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)
