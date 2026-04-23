# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""D6 — DIA detail panel API (`get_dia_demand_detail`).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_detail_d6
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.dia_detail import get_dia_demand_detail


class TestDiaDetailD6(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_D6_{h}", f"Entity D6 {h}")
		self.dept = ensure_department(f"Dept D6 {h}", self.entity)
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
				"title": kwargs.pop("title", None) or f"D6 {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"items": [
					{
						"item_description": "Test line",
						"category": "c",
						"uom": "ea",
						"quantity": 2,
						"estimated_unit_cost": 25,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc.name

	def test_detail_missing_name(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		out = get_dia_demand_detail("")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "MISSING_NAME")

	def test_detail_not_found(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		out = get_dia_demand_detail("nonexistent-demand-xyz")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_detail_ok_sections_and_items(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"req_d6_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Detail",
				"last_name": "User",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Requisitioner")
		try:
			frappe.set_user(user.name)
			name = self._mk_demand(requested_by=user.name, title="Detail panel seed")
			out = get_dia_demand_detail(name)
			self.assertTrue(out.get("ok"))
			for key in ("a", "b", "c", "d", "e", "name", "currency"):
				self.assertIn(key, out)
			self.assertEqual((out.get("d") or {}).get("line_count"), 1)
			rows = (out.get("d") or {}).get("rows") or []
			self.assertEqual(len(rows), 1)
			self.assertEqual(rows[0].get("item_description"), "Test line")
			self.assertEqual(flt(rows[0].get("line_total")), 50.0)
			a = out.get("a") or {}
			self.assertEqual(a.get("title"), "Detail panel seed")
			self.assertIn("Dept D6", a.get("requesting_department_label") or "")
			acts = out.get("actions") or []
			self.assertGreaterEqual(len(acts), 1)
			ids = {x.get("id") for x in acts}
			self.assertIn("open_form", ids)
			self.assertIn("submit_demand", ids)
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)
