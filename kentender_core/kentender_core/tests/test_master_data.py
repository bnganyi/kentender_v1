"""Phase B — core master data DocTypes (Procuring Entity, Procuring Department, Business Unit).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core
"""

import frappe
from frappe.tests import IntegrationTestCase


class TestKenTenderMasterData(IntegrationTestCase):
	doctype = None

	def test_procuring_entity_department_business_unit_chain(self):
		code = "KT-TEST-PE-001"
		if frappe.db.exists("Procuring Entity", code):
			frappe.delete_doc("Procuring Entity", code, force=1)

		pe = frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": code,
				"entity_name": "Test Procuring Entity",
			}
		)
		pe.insert()

		pd = frappe.get_doc(
			{
				"doctype": "Procuring Department",
				"department_name": "Test Department",
				"procuring_entity": pe.name,
			}
		)
		pd.insert()

		bu = frappe.get_doc(
			{
				"doctype": "Business Unit",
				"unit_name": "Test Business Unit",
				"department": pd.name,
			}
		)
		bu.insert()

		self.assertTrue(frappe.db.exists("Procuring Entity", pe.name))
		self.assertTrue(frappe.db.exists("Procuring Department", pd.name))
		self.assertTrue(frappe.db.exists("Business Unit", bu.name))
		self.assertEqual(pd.procuring_entity, pe.name)
		self.assertEqual(bu.department, pd.name)

		frappe.delete_doc("Business Unit", bu.name, force=1)
		frappe.delete_doc("Procuring Department", pd.name, force=1)
		frappe.delete_doc("Procuring Entity", pe.name, force=1)
