# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-013 — the Tender family changes only through the Tenders commands.
Administrator and System Manager hold read, not write, create or delete; the
controller refuses the same writes for Administrator (who passes Frappe's own
permission check whatever DocPerm says), and a posted `flags` key cannot open
the window (TPR-CHG-001 v0.17 §12.3 rule 1)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.command_write_guard import CommandWriteError
from kentender_procurement.tenders.services import envelope, events
from kentender_procurement.tenders.tests import fixtures as fx

FAMILY = (
	"Tender", "Tender Version", "Tender Task", "Tender Decision", "Tender Publication", "Tender Channel Confirmation",
	"Tender Addendum", "Tender Clarification", "Tender Candidate Notice", "Tender Bid Definition", "Tender Cancellation",
	"Tender Document", "Tender Event", "Tender Submission Handoff", "Tender Command Journal",
)


def _a_plain_field(doctype: str) -> str:
	"""A non-standard field (`set_value` refuses the standard ones before it checks permission)."""
	return next(df.fieldname for df in frappe.get_meta(doctype).fields if df.fieldtype in ("Data", "Small Text", "Text", "Long Text", "Code") and not df.fieldname.startswith("fixture"))


SM = "tndt.guard.sysman@example.test"


class TestTenderRecordsAreCommandOnly(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_tender_rows()
		self.addCleanup(fx.wipe_tender_rows)
		self.addCleanup(frappe.set_user, "Administrator")

	def _world(self) -> dict[str, str]:
		root = envelope.insert(frappe.get_doc({"doctype": "Tender", "tender_reference": "TND-TEST-GUARD-001", "overall_status": "Draft", "record_version": 0, "fixture_namespace": fx.NS}))
		version = envelope.insert(frappe.get_doc({"doctype": "Tender Version", "tender": root.name, "version_number": 1, "status": "Draft", "record_version": 0, "fixture_namespace": fx.NS}))
		event = events.emit(tender=root.name, event_type="TenderTestGuard", command="Test", idempotency_key=fx.key(), fixture_namespace=fx.NS)
		key = fx.key()
		envelope.record_command(idempotency_key=key, command="Test", payload={"a": 1}, result={"ok": True}, document_type="Tender", document_name=root.name, fixture_namespace=fx.NS)
		return {
			"Tender": root.name,
			"Tender Version": version.name,
			"Tender Event": event.name,
			"Tender Command Journal": frappe.db.get_value("Tender Command Journal", {"idempotency_key": key}, "name"),
		}

	def _system_manager(self) -> str:
		fx._user(SM, "TND Test System Manager")
		frappe.get_doc("User", SM).add_roles("System Manager")
		self.addCleanup(self._remove_system_manager)
		return SM

	def _remove_system_manager(self) -> None:
		frappe.set_user("Administrator")
		for contact in frappe.get_all("Contact Email", filters={"email_id": SM}, pluck="parent"):
			frappe.delete_doc("Contact", contact, force=1, ignore_permissions=True)
		if frappe.db.exists("User", SM):
			frappe.delete_doc("User", SM, force=1, ignore_permissions=True)

	def test_no_role_holds_write_create_or_delete_on_a_tender_record(self):
		for doctype in FAMILY:
			for permission in frappe.get_meta(doctype).permissions:
				self.assertFalse(
					permission.write or permission.create or permission.delete,
					f"{doctype}: {permission.role} still holds write/create/delete",
				)

	def test_a_system_manager_cannot_change_or_delete_a_tender_record_through_the_api(self):
		world = self._world()
		manager = self._system_manager()
		frappe.set_user(manager)
		for doctype, name in world.items():
			with self.assertRaises(frappe.PermissionError, msg=doctype):
				frappe.client.set_value(doctype, name, _a_plain_field(doctype), "x")
			with self.assertRaises(frappe.PermissionError, msg=doctype):
				frappe.client.delete(doctype, name)
			self.assertTrue(frappe.db.exists(doctype, name), doctype)

	def test_the_controller_refuses_a_save_delete_or_insert_by_administrator(self):
		world = self._world()
		for doctype, name in world.items():
			with self.assertRaises(CommandWriteError, msg=f"{doctype} save") as saved:
				frappe.get_doc(doctype, name).save()
			self.assertEqual(saved.exception.code, "COMMAND_ONLY_WRITE", doctype)
			with self.assertRaises(CommandWriteError, msg=f"{doctype} delete") as deleted:
				frappe.delete_doc(doctype, name)
			self.assertEqual(deleted.exception.code, "COMMAND_ONLY_DELETE", doctype)
			self.assertTrue(frappe.db.exists(doctype, name), doctype)
		for doctype in FAMILY:
			with self.assertRaises(CommandWriteError, msg=f"{doctype} insert") as inserted:
				frappe.get_doc({"doctype": doctype}).insert()
			self.assertEqual(inserted.exception.code, "COMMAND_ONLY_WRITE", doctype)

	def test_a_posted_flags_key_does_not_open_the_window(self):
		"""The old guard read `doc.flags.kt_lifecycle`; a request body can carry a `flags` key."""
		world = self._world()
		doc = frappe.get_doc({**frappe.get_doc("Tender Version", world["Tender Version"]).as_dict(), "flags": {"kt_lifecycle": True, "kt_fixture_wipe": True}})
		doc.flags.kt_lifecycle = True
		doc.flags.kt_fixture_wipe = True
		with self.assertRaises(CommandWriteError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(CommandWriteError):
			doc.delete(ignore_permissions=True)

	def test_the_envelope_commands_still_write(self):
		world = self._world()
		root = frappe.get_doc("Tender", world["Tender"])
		envelope.bump(root, overall_status="Awaiting procurement approval")
		root.reload()
		self.assertEqual(root.overall_status, "Awaiting procurement approval")
