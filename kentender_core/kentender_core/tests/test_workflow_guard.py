"""Phase H — workflow guard placeholder."""

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.workflow_guard_service import run_workflow_guard


class TestWorkflowGuard(IntegrationTestCase):
	doctype = None

	def test_run_workflow_guard_passes(self):
		code = "KT-TEST-WG-001"
		if frappe.db.exists("Procuring Entity", code):
			frappe.delete_doc("Procuring Entity", code, force=1)

		pe = frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": code,
				"entity_name": "Test PE for workflow guard",
			}
		)
		pe.insert()

		ok, message = run_workflow_guard("test.action", pe)
		self.assertTrue(ok)
		self.assertEqual(message, "")
		self.assertIsInstance(ok, bool)
		self.assertIsInstance(message, str)

		frappe.delete_doc("Procuring Entity", pe.name, force=1)
