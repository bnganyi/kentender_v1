# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""DIA audit API — timeline and downstream usage."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.audit import get_demand_audit_data


class TestDiaAuditAPI(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_AUD_{h}", f"Entity Audit {h}")
		self.dept = ensure_department(f"Dept Audit {h}", self.entity)
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
				"title": kwargs.pop("title", None) or f"Audit {frappe.generate_hash(length=4)}",
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
						"estimated_unit_cost": 50,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc.name

	def test_get_demand_audit_data_returns_timeline_and_downstream(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		name = self._mk_demand(
			status="Pending HoD Approval",
			submitted_by=frappe.session.user,
			submitted_at=now_datetime(),
		)
		out = get_demand_audit_data(name)
		self.assertEqual(out["demand_name"], name)
		self.assertTrue(out["timeline"])
		labels = [row["label"] for row in out["timeline"]]
		self.assertIn("Draft created", labels)
		self.assertIn("Submitted for approval", labels)
		self.assertNotIn("HoD approved", labels)
		self.assertIn("downstream", out)
		self.assertIn("linked_packages", out["downstream"])
