# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""D4 — queue refine filters + search (`get_dia_queue_filter_meta`, `get_dia_queue_list`).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_queue_list_d4
"""

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.queue_list import get_dia_queue_filter_meta, get_dia_queue_list


class TestDiaQueueListD4(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_D4_{h}", f"Entity D4 {h}")
		self.dept = ensure_department(f"Dept D4 {h}", self.entity)
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
				"title": kwargs.pop("title", None) or f"D4 {frappe.generate_hash(length=4)}",
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

	def test_filter_meta_ok_shape(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		out = get_dia_queue_filter_meta()
		self.assertTrue(out.get("ok"))
		for key in (
			"demand_types",
			"priorities",
			"requisition_types",
			"statuses",
			"departments",
			"budget_lines",
		):
			self.assertIn(key, out)
		self.assertIsInstance(out.get("departments"), list)

	def test_search_on_title_requisitioner_queue(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		token = f"D4SRCH_{frappe.generate_hash(length=8)}"
		email = f"req_d4_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Req",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Requisitioner")
		try:
			frappe.set_user(user.name)
			self._mk_demand(requested_by=user.name, title=f"Alpha {token} Beta")
			out_all = get_dia_queue_list(work_tab="mywork", queue_id="my_drafts", search="")
			self.assertTrue(out_all.get("ok"))
			out_find = get_dia_queue_list(work_tab="mywork", queue_id="my_drafts", search=token)
			self.assertTrue(out_find.get("ok"))
			rows = out_find.get("demands") or []
			self.assertGreaterEqual(len(rows), 1)
			self.assertTrue(any(token in (r.get("title") or "") for r in rows))
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)

	def test_refine_requesting_department_admin_queue(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		name = self._mk_demand(title=f"D4Dept {frappe.generate_hash(length=4)}")
		frappe.db.set_value("Demand", name, "status", "Planning Ready", update_modified=False)
		ref = json.dumps({"requesting_department": self.dept})
		out = get_dia_queue_list(
			work_tab="approved",
			queue_id="planning_ready",
			filters=ref,
			limit=200,
		)
		self.assertTrue(out.get("ok"))
		names = {r.get("name") for r in (out.get("demands") or [])}
		self.assertIn(name, names)
		applied = out.get("applied_refine") or {}
		self.assertEqual(applied.get("requesting_department"), self.dept)

	def test_invalid_refine_dropped_from_applied(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		ref = json.dumps({"demand_type": "__definitely_not_a_valid_option__"})
		out = get_dia_queue_list(work_tab="approved", queue_id="planning_ready", filters=ref)
		self.assertTrue(out.get("ok"))
		applied = out.get("applied_refine") or {}
		self.assertNotIn("demand_type", applied)
