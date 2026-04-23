# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Phase F — DIA workspace gate (F3) and Demand row visibility (F1).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_phase_f
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.landing import get_dia_landing_shell_data


class TestDiaPhaseF(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		dept = getattr(self, "_dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)
		ent = getattr(self, "_entity", None)
		if ent and frappe.db.exists("Procuring Entity", ent):
			frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)
		for u in getattr(self, "_users", []):
			if frappe.db.exists("User", u):
				frappe.delete_doc("User", u, force=True, ignore_permissions=True)

	def test_landing_denied_without_dia_workspace_role(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		self._demand_names = []
		self._dept = None
		self._entity = None
		self._users = []
		email = f"dia_f_{frappe.generate_hash(length=4)}@test.local"
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "DIA",
				"last_name": "NoRole",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		u.insert(ignore_permissions=True)
		u.add_roles("Report Manager")
		self._users.append(u.name)
		frappe.set_user(u.name)
		try:
			out = get_dia_landing_shell_data()
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "DIA_ACCESS_DENIED")
		finally:
			frappe.set_user("Administrator")

	def test_requisitioner_cannot_read_peer_demand(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		self._demand_names = []
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self._entity = ensure_procuring_entity(f"MOH_F_{h}", f"Entity F {h}")
		self._dept = ensure_department(f"Dept F {h}", self._entity)
		self._users = []

		def _mk_user(suffix: str) -> str:
			email = f"req_f_{suffix}_{h}@test.local"
			u = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Req",
					"last_name": suffix,
					"send_welcome_email": 0,
					"enabled": 1,
				}
			)
			u.insert(ignore_permissions=True)
			u.add_roles("Requisitioner")
			self._users.append(u.name)
			return u.name

		u1 = _mk_user("a")
		u2 = _mk_user("b")

		frappe.set_user(u1)
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Peer test {h}",
				"procuring_entity": self._entity,
				"requesting_department": self._dept,
				"request_date": today(),
				"required_by_date": today(),
				"specification_summary": "Spec",
				"delivery_location": "HQ",
				"requested_delivery_period_days": 10,
				"requested_by": u1,
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 50,
					}
				],
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)

		frappe.set_user(u2)
		try:
			self.assertFalse(frappe.has_permission("Demand", "read", doc=doc.name, user=u2))
		finally:
			frappe.set_user("Administrator")

	def test_auditor_read_only_access(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		self._demand_names = []
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self._entity = ensure_procuring_entity(f"MOH_FA_{h}", f"Entity FA {h}")
		self._dept = ensure_department(f"Dept FA {h}", self._entity)
		self._users = []

		req_email = f"req_fa_{h}@test.local"
		req = frappe.get_doc(
			{
				"doctype": "User",
				"email": req_email,
				"first_name": "Req",
				"last_name": "FA",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		req.insert(ignore_permissions=True)
		req.add_roles("Requisitioner")
		self._users.append(req.name)

		frappe.set_user(req.name)
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"Auditor read-only {h}",
				"procuring_entity": self._entity,
				"requesting_department": self._dept,
				"request_date": today(),
				"required_by_date": today(),
				"specification_summary": "Spec",
				"delivery_location": "HQ",
				"requested_delivery_period_days": 10,
				"requested_by": req.name,
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 75,
					}
				],
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)

		aud_email = f"aud_fa_{h}@test.local"
		aud = frappe.get_doc(
			{
				"doctype": "User",
				"email": aud_email,
				"first_name": "Audit",
				"last_name": "FA",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		aud.insert(ignore_permissions=True)
		aud.add_roles("Auditor")
		self._users.append(aud.name)

		frappe.set_user(aud.name)
		try:
			self.assertTrue(frappe.has_permission("Demand", "read", doc=doc.name, user=aud.name))
			self.assertFalse(frappe.has_permission("Demand", "write", doc=doc.name, user=aud.name))
		finally:
			frappe.set_user("Administrator")
