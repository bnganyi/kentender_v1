# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""D3 — queue list API (`get_dia_queue_list`).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_queue_list_d3
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.queue_list import (
	_resolve_filters,
	get_dia_queue_list,
)


class TestDiaQueueListD3(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_D3_{h}", f"Entity D3 {h}")
		self.dept = ensure_department(f"Dept D3 {h}", self.entity)
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
				"title": kwargs.pop("title", None) or f"D3 {frappe.generate_hash(length=4)}",
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

	def test_resolve_filters_procurement_rejected_queue_ids(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		f_tab = _resolve_filters(role_key="procurement", work_tab="rejected", queue_id="dia_rejected", user="Administrator")
		self.assertEqual(f_tab, {"status": "Rejected"})
		f_all = _resolve_filters(role_key="procurement", work_tab="all", queue_id="dia_rejected", user="Administrator")
		self.assertEqual(f_all, {"status": "Rejected"})

	def test_resolve_filters_auditor_default_and_approved(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		f_all = _resolve_filters(role_key="auditor", work_tab="all", queue_id="all_demands", user="Administrator")
		self.assertEqual(f_all, {"status": ["not in", ["Cancelled"]]})
		f_app = _resolve_filters(role_key="auditor", work_tab="approved", queue_id="all_approved", user="Administrator")
		self.assertEqual(f_app, {"status": ["in", ["Approved", "Planning Ready"]]})

	def test_resolve_filters_requisitioner_my_drafts(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		u = "req_d3@test.local"
		if not frappe.db.exists("User", u):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": u,
					"first_name": "R",
					"send_welcome_email": 0,
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
		try:
			f = _resolve_filters(role_key="requisitioner", work_tab="mywork", queue_id="my_drafts", user=u)
			self.assertEqual(f.get("requested_by"), u)
			self.assertEqual(f.get("status"), "Draft")
		finally:
			if frappe.db.exists("User", u):
				frappe.delete_doc("User", u, force=True, ignore_permissions=True)

	def test_admin_get_list_ok_shape(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		out = get_dia_queue_list(work_tab="approved", queue_id="planning_ready", limit=10, start=0)
		self.assertTrue(out.get("ok"))
		self.assertIn("demands", out)
		self.assertEqual(out.get("queue_id"), "planning_ready")
		self.assertIn("has_more", out)

	def test_requisitioner_list_after_insert(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"req_d3_{frappe.generate_hash(length=4)}@test.local"
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
			self._mk_demand(requested_by=user.name, title="Draft row")
			out = get_dia_queue_list(work_tab="mywork", queue_id="my_drafts")
			self.assertTrue(out.get("ok"))
			self.assertGreaterEqual(len(out.get("demands") or []), 1)
			row = (out.get("demands") or [])[0]
			self.assertIn("name", row)
			self.assertIn("demand_id", row)
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)
