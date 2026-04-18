"""Phase D — audit event logging."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.audit_event_service import log_audit_event


class TestAuditEvent(IntegrationTestCase):
	doctype = None

	def test_log_audit_event_persists_row(self):
		name = log_audit_event(
			event_type="test.event",
			entity="ENT-1",
			document_type="Procuring Entity",
			document_name="PE-001",
			action="create",
			performed_by="Administrator",
			metadata={"k": "v"},
		)
		self.assertTrue(frappe.db.exists("Audit Event", name))
		row = frappe.get_doc("Audit Event", name)
		self.assertEqual(row.event_type, "test.event")
		self.assertEqual(row.entity, "ENT-1")
		self.assertEqual(row.document_type, "Procuring Entity")
		self.assertEqual(row.document_name, "PE-001")
		self.assertEqual(row.action, "create")
		self.assertEqual(row.performed_by, "Administrator")
		meta = row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata)
		self.assertEqual(meta, {"k": "v"})
		frappe.delete_doc("Audit Event", name, force=True, ignore_permissions=True)
		frappe.db.commit()
