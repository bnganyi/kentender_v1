# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""D5 — master list row payload (labels + DIA fields for Desk list).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_queue_list_d5
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.queue_list import get_dia_queue_list


class TestDiaQueueListD5(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_D5_{h}", f"Entity D5 {h}")
		self.dept = ensure_department(f"Dept D5 Label {h}", self.entity)
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
				"title": kwargs.pop("title", None) or f"D5 {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": kwargs.pop("required_by_date", None) or add_days(today(), 14),
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": kwargs.pop("line_cost", 50),
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc.name

	def test_queue_row_includes_d5_fields_and_labels(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"req_d5_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Pat",
				"last_name": "Requester",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Requisitioner")
		try:
			frappe.set_user(user.name)
			self._mk_demand(
				requested_by=user.name,
				title="D5 row shape",
				demand_type="Planned",
				priority_level="Normal",
				status="Draft",
			)
			out = get_dia_queue_list(work_tab="mywork", queue_id="my_drafts", limit=50)
			self.assertTrue(out.get("ok"))
			rows = [r for r in (out.get("demands") or []) if r.get("title") == "D5 row shape"]
			self.assertEqual(len(rows), 1)
			r = rows[0]
			for key in (
				"required_by_date",
				"demand_type",
				"priority_level",
				"status",
				"requesting_department_label",
				"requested_by_label",
			):
				self.assertIn(key, r)
			self.assertIn("Dept D5 Label", r.get("requesting_department_label") or "")
			self.assertIn("Requester", r.get("requested_by_label") or "")
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)
