from __future__ import annotations

import frappe
from frappe.exceptions import PermissionError, ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.audit_service import (
	get_std_audit_events,
	record_std_audit_event,
)


def _delete_audit_events(object_code: str):
	frappe.db.delete("STD Audit Event", {"object_code": object_code})


class TestSTDAuditService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_delete_audit_events("STD-AUDIT-SVC-1")
		_delete_audit_events("STD-AUDIT-SVC-2")

	def tearDown(self):
		frappe.set_user("Administrator")
		_delete_audit_events("STD-AUDIT-SVC-1")
		_delete_audit_events("STD-AUDIT-SVC-2")
		frappe.db.commit()
		super().tearDown()

	def test_record_event_persists_audit_context(self):
		resp = record_std_audit_event(
			event_type="LOCKED_EDIT_DENIED",
			object_type="STD_INSTANCE",
			object_code="STD-AUDIT-SVC-1",
			actor="Administrator",
			previous_state="Ready",
			new_state="Ready",
			reason="immutable after publish",
			denial_code="STD_AUTH_INSTANCE_IMMUTABLE",
			metadata={"field": "boq_items", "attempt": "manual-edit"},
		)
		self.assertTrue(resp["audit_event_code"].startswith("AUD-"))

		doc = frappe.get_doc("STD Audit Event", {"audit_event_code": resp["audit_event_code"]})
		self.assertEqual("LOCKED_EDIT_DENIED", doc.event_type)
		self.assertEqual("STD_INSTANCE", doc.object_type)
		self.assertEqual("STD-AUDIT-SVC-1", doc.object_code)
		self.assertEqual("STD_AUTH_INSTANCE_IMMUTABLE", doc.denial_code)
		self.assertEqual("Administrator", doc.actor)

	def test_event_code_stays_append_only_for_update_and_delete(self):
		resp = record_std_audit_event(
			event_type="EVIDENCE_EXPORTED",
			object_type="AUDIT_EVENT",
			object_code="STD-AUDIT-SVC-2",
			actor="Administrator",
		)
		doc = frappe.get_doc("STD Audit Event", {"audit_event_code": resp["audit_event_code"]})
		doc.reason = "edited"
		with self.assertRaises(ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(ValidationError):
			frappe.delete_doc("STD Audit Event", doc.name, force=True, ignore_permissions=True)

	def test_read_api_requires_audit_role(self):
		record_std_audit_event(
			event_type="PERMISSION_DENIED",
			object_type="STD_INSTANCE",
			object_code="STD-AUDIT-SVC-1",
			actor="Administrator",
		)

		frappe.set_user("Guest")
		with self.assertRaises(PermissionError):
			get_std_audit_events(object_type="STD_INSTANCE", object_code="STD-AUDIT-SVC-1")

		frappe.set_user("Administrator")
		events = get_std_audit_events(object_type="STD_INSTANCE", object_code="STD-AUDIT-SVC-1")
		self.assertGreaterEqual(len(events), 1)
		self.assertEqual("PERMISSION_DENIED", events[0]["event_type"])

