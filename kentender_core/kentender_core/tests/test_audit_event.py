"""Phase D — audit event logging; AUD-XC-010 — the ledger is append-only."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.audit_event_service import log_audit_event, purge_audit_events
from kentender_core.services.command_write_guard import CommandWriteError

MARK = "kt-audit-immutability-test"
SM_USER = "kt-audit-sm@example.com"


def _purge():
	purge_audit_events({"event_type": ["in", ["test.event", MARK]]}, reason="Audit Event test clean-up")
	frappe.db.commit()


class TestAuditEvent(IntegrationTestCase):
	doctype = None

	def test_log_audit_event_persists_row(self):
		self.addCleanup(_purge)
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


class TestAuditEventIsAppendOnly(IntegrationTestCase):
	"""AUD-XC-010: no update or delete by anyone, inserts only by the audit writer."""

	doctype = None

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, frappe.session.user)
		self.addCleanup(_purge)
		self.addCleanup(self._drop_user)
		if not frappe.db.exists("User", SM_USER):
			user = frappe.get_doc({"doctype": "User", "email": SM_USER, "first_name": "Audit SM", "send_welcome_email": 0})
			user.append("roles", {"role": "System Manager"})
			user.insert(ignore_permissions=True)
		self.name = log_audit_event(
			event_type=MARK, document_type="Strategic Plan Version", document_name="SPV-1", action="Submit for approval", performed_by="Guest"
		)

	def _drop_user(self):
		frappe.set_user("Administrator")
		frappe.delete_doc("User", SM_USER, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _refused(self, fn, *args, **kwargs):
		"""System Manager is stopped by DocPerm (the first lock); Administrator
		bypasses DocPerm, so only the controller guard (the second lock) stops
		it, with a typed code. Returns the code a guard refusal carries."""
		with self.assertRaises(frappe.PermissionError) as caught:
			fn(*args, **kwargs)
		if frappe.session.user == SM_USER and not isinstance(caught.exception, CommandWriteError):
			return self.expected
		self.assertIsInstance(caught.exception, CommandWriteError)
		return caught.exception.code

	def _expect(self, code):
		self.expected = code

	def _stored(self):
		return frappe.db.get_value("Audit Event", self.name, ["performed_by", "action"], as_dict=True)

	def test_nobody_holds_write_create_or_delete_permission(self):
		for perm in frappe.get_meta("Audit Event").permissions:
			self.assertFalse(perm.write or perm.create or perm.delete, f"{perm.role} still has a write path")
		for role in ("System Manager", "Administrator"):
			self.assertTrue(any(p.role == role and p.read for p in frappe.get_meta("Audit Event").permissions))
		self.assertFalse(frappe.has_permission("Audit Event", "write", user=SM_USER))
		self.assertFalse(frappe.has_permission("Audit Event", "delete", user=SM_USER))

	def test_update_refused_for_system_manager_and_administrator(self):
		for user in (SM_USER, "Administrator"):
			frappe.set_user(user)
			doc = frappe.get_doc("Audit Event", self.name)
			doc.performed_by = "Administrator"
			self._expect("COMMAND_ONLY_WRITE"); self.assertEqual(self._refused(doc.save, ignore_permissions=True), "COMMAND_ONLY_WRITE", user)
			self._expect("COMMAND_ONLY_WRITE"); self.assertEqual(self._refused(frappe.client.set_value, "Audit Event", self.name, "performed_by", "Administrator"), "COMMAND_ONLY_WRITE")
			self._expect("COMMAND_ONLY_WRITE"); self.assertEqual(self._refused(frappe.client.save, {"doctype": "Audit Event", "name": self.name, "modified": str(frappe.db.get_value("Audit Event", self.name, "modified")), "action": "Approved"}), "COMMAND_ONLY_WRITE")
		self.assertEqual(self._stored(), {"performed_by": "Guest", "action": "Submit for approval"})

	def test_delete_refused_for_system_manager_and_administrator(self):
		for user in (SM_USER, "Administrator"):
			frappe.set_user(user)
			self._expect("COMMAND_ONLY_DELETE"); self.assertEqual(self._refused(frappe.delete_doc, "Audit Event", self.name), "COMMAND_ONLY_DELETE", user)
			self._expect("COMMAND_ONLY_DELETE"); self.assertEqual(self._refused(frappe.delete_doc, "Audit Event", self.name, force=True, ignore_permissions=True), "COMMAND_ONLY_DELETE", user)
			self._expect("COMMAND_ONLY_DELETE"); self.assertEqual(self._refused(frappe.client.delete, "Audit Event", self.name), "COMMAND_ONLY_DELETE", user)
		self.assertTrue(frappe.db.exists("Audit Event", self.name))

	def test_insert_only_through_the_audit_writer(self):
		row = {
			"doctype": "Audit Event",
			"event_type": MARK,
			"document_type": "Strategic Plan Version",
			"document_name": "SPV-1",
			"action": "Forged",
			"performed_by": "Administrator",
		}
		for user in (SM_USER, "Administrator"):
			frappe.set_user(user)
			self._expect("COMMAND_ONLY_WRITE"); self.assertEqual(self._refused(frappe.get_doc(row).insert, ignore_permissions=True), "COMMAND_ONLY_WRITE", user)
			self._expect("COMMAND_ONLY_WRITE"); self.assertEqual(self._refused(frappe.client.insert, row), "COMMAND_ONLY_WRITE", user)
			self._expect("COMMAND_ONLY_WRITE"); self.assertEqual(self._refused(frappe.get_doc({**row, "flags": {"kt_awd_command": True, "ignore_permissions": True}}).insert), "COMMAND_ONLY_WRITE", user)
		self.assertFalse(frappe.db.exists("Audit Event", {"event_type": MARK, "action": "Forged"}))

	def test_a_rename_is_refused(self):
		self.assertFalse(frappe.get_meta("Audit Event").allow_rename)

	def test_purge_is_filtered_and_in_process_only(self):
		with self.assertRaises(ValueError):
			purge_audit_events({}, reason="no filter")
		frappe.local.request = object()
		self.addCleanup(lambda: setattr(frappe.local, "request", None))
		self.assertEqual(self._refused(purge_audit_events, {"event_type": MARK}, reason="from a request"), "COMMAND_MAINTENANCE_REFUSED")
		frappe.local.request = None
		self.assertEqual(purge_audit_events({"event_type": MARK}, reason="test"), 1)
		self.assertFalse(frappe.db.exists("Audit Event", self.name))
