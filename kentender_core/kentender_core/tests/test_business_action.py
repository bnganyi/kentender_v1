"""Phase I — execute_business_action (guard + audit)."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.business_action_service import execute_business_action


class TestBusinessAction(IntegrationTestCase):
	doctype = None

	def test_execute_business_action_guard_then_audit(self):
		code = "KT-TEST-BA-001"
		if frappe.db.exists("Procuring Entity", code):
			frappe.delete_doc("Procuring Entity", code, force=1)

		pe = frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": code,
				"entity_name": "Test PE for business action",
			}
		)
		pe.insert()

		action = "test.submit"
		ok, message = execute_business_action(action, pe)
		self.assertTrue(ok)
		self.assertEqual(message, "")

		rows = frappe.get_all(
			"Audit Event",
			filters={
				"event_type": "ken.business_action",
				"document_type": "Procuring Entity",
				"document_name": pe.name,
				"action": action,
			},
			pluck="name",
			limit=1,
		)
		self.assertEqual(len(rows), 1)
		row = frappe.get_doc("Audit Event", rows[0])
		self.assertEqual(row.event_type, "ken.business_action")
		self.assertEqual(row.document_type, "Procuring Entity")
		self.assertEqual(row.document_name, pe.name)
		self.assertEqual(row.action, action)
		meta = row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata)
		self.assertEqual(meta.get("action"), action)

		frappe.delete_doc("Audit Event", rows[0], force=True, ignore_permissions=True)
		frappe.delete_doc("Procuring Entity", pe.name, force=1)
		frappe.db.commit()
