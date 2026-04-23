# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""D2 — KPI strip semantics for DIA landing (`get_dia_landing_shell_data`).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_landing_d2
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.landing import (
	_count_returned_this_week,
	get_dia_landing_shell_data,
)


class TestLandingD2Kpis(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_D2_{h}", f"Entity D2 {h}")
		self.dept = ensure_department(f"Dept D2 {h}", self.entity)
		self._demand_names: list[str] = []

	def tearDown(self):
		if getattr(self, "_skipped_no_demand", False):
			return
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		self._demand_names = []
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
				"title": kwargs.pop("title", None) or f"D2 {frappe.generate_hash(length=4)}",
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
						"estimated_unit_cost": kwargs.pop("line_cost", 100),
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc.name

	def _mark_rejected(self, name: str):
		frappe.db.set_value(
			"Demand",
			name,
			{
				"status": "Rejected",
				"rejection_reason": "Test rejection",
				"rejected_by": frappe.session.user,
				"rejected_at": now_datetime(),
			},
			update_modified=False,
		)

	def test_admin_payload_has_procurement_kpis(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		out = get_dia_landing_shell_data()
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("role_key"), "admin")
		kpis = out.get("kpis") or []
		self.assertEqual(len(kpis), 4)
		ids = [k["id"] for k in kpis]
		self.assertEqual(ids, ["approved", "planning_ready", "emergency_approved", "total_ready_value"])
		self.assertEqual(
			[k.get("testid") for k in kpis],
			["dia-kpi-my-drafts", "dia-kpi-pending-approval", "dia-kpi-emergency", "dia-kpi-total-value"],
		)

	def test_requisitioner_rejected_returned_includes_returned_draft(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"requisitioner_d2_{frappe.generate_hash(length=4)}@test.local"
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
			self._mk_demand(requested_by=user.name, title="Plain draft")
			self._mk_demand(
				requested_by=user.name,
				title="Returned",
				return_reason="HoD returned",
				returned_at=now_datetime(),
			)
			rej_name = self._mk_demand(requested_by=user.name, title="To reject")
			self._mark_rejected(rej_name)
			out = get_dia_landing_shell_data()
			self.assertTrue(out.get("ok"))
			self.assertEqual(out.get("role_key"), "requisitioner")
			rej_kpi = next(k for k in out["kpis"] if k["id"] == "rejected_returned")
			self.assertEqual(int(rej_kpi["value"]), 2)
		finally:
			frappe.set_user("Administrator")
			for name in list(self._demand_names):
				if frappe.db.exists("Demand", name):
					frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
			self._demand_names.clear()
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)

	def test_returned_this_week_excludes_old_returns(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		c0 = _count_returned_this_week()
		old = add_days(now_datetime(), -10)
		self._mk_demand(title="Old return", return_reason="x", returned_at=old)
		self.assertEqual(_count_returned_this_week(), c0)
		c1 = _count_returned_this_week()
		self._mk_demand(title="Fresh return", return_reason="y", returned_at=now_datetime())
		self.assertEqual(_count_returned_this_week(), c1 + 1)

	def test_hod_kpi_returned_week_matches_counter(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"hod_d2_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "HoD",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Department Approver")
		self._mk_demand(title="HoD KPI row", return_reason="r", returned_at=now_datetime())
		try:
			frappe.set_user(user.name)
			out = get_dia_landing_shell_data()
			self.assertTrue(out.get("ok"))
			self.assertEqual(out.get("role_key"), "hod")
			wk = next(k for k in out["kpis"] if k["id"] == "returned_week")
			self.assertEqual(int(wk["value"]), _count_returned_this_week())
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)
