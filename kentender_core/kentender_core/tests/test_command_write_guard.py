"""The command-only write guard (WP2.1): allowed with the in-process flag,
refused without it, not spoofable from the client, deletes refused, and a
Draft allow-list.

The guard functions are driven directly against stored Audit Event records
(any doctype with a few plain fields will do); the Audit Event controller
itself is tested in test_audit_event.py."""

from __future__ import annotations

import copy

import frappe
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase

from kentender_core.services.audit_event_service import log_audit_event, purge_audit_events
from kentender_core.services.command_write_guard import (
	CommandWriteError,
	CommandWriteGuardMixin,
	command_write,
	command_write_active,
	guard_command_delete,
	guard_command_write,
	maintenance_write,
)

FAMILY = "KT Guard Test Family"
MARK = "kt-guard-test"


class TestCommandWriteGuard(IntegrationTestCase):
	doctype = None

	def setUp(self):
		super().setUp()
		self.addCleanup(self._purge)
		name = log_audit_event(event_type=MARK, document_type="Procuring Entity", document_name=MARK, action="create", performed_by="Administrator")
		self.doc = frappe.get_doc("Audit Event", name)

	def _purge(self):
		purge_audit_events({"event_type": MARK}, reason="command write guard test clean-up")
		frappe.db.commit()

	def _changed(self, **values):
		"""The stored record, as a user save would see it: before-save copy plus edits."""
		doc = frappe.get_doc("Audit Event", self.doc.name)
		doc._doc_before_save = copy.deepcopy(doc)
		doc.update(values)
		return doc

	def _code(self, fn, *args, **kwargs):
		with self.assertRaises(CommandWriteError) as caught:
			fn(*args, **kwargs)
		return caught.exception.code

	# -- the in-process flag --------------------------------------------------

	def test_command_write_authorises_and_closes(self):
		doc = self._changed(action="edited")
		self.assertFalse(command_write_active(FAMILY))
		with command_write(FAMILY):
			self.assertTrue(command_write_active(FAMILY))
			guard_command_write(doc, FAMILY)
			guard_command_delete(doc, FAMILY)
		self.assertFalse(command_write_active(FAMILY))
		self.assertEqual(self._code(guard_command_write, doc, FAMILY), "COMMAND_ONLY_WRITE")

	def test_a_command_for_one_family_does_not_open_another(self):
		doc = self._changed(action="edited")
		with command_write("Some Other Family"):
			self.assertEqual(self._code(guard_command_write, doc, FAMILY), "COMMAND_ONLY_WRITE")

	def test_nested_windows_close_in_order_and_on_error(self):
		with command_write(FAMILY):
			with command_write(FAMILY):
				pass
			self.assertTrue(command_write_active(FAMILY))
		self.assertFalse(command_write_active(FAMILY))
		with self.assertRaises(RuntimeError), command_write(FAMILY):
			raise RuntimeError("boom")
		self.assertFalse(command_write_active(FAMILY))

	def test_refused_without_the_flag_for_insert_update_and_delete(self):
		fresh = frappe.new_doc("Audit Event")
		self.assertEqual(self._code(guard_command_write, fresh, FAMILY), "COMMAND_ONLY_WRITE")
		self.assertEqual(self._code(guard_command_write, self._changed(action="x"), FAMILY), "COMMAND_ONLY_WRITE")
		self.assertEqual(self._code(guard_command_delete, self.doc, FAMILY), "COMMAND_ONLY_DELETE")

	# -- spoofing ---------------------------------------------------------------

	def test_doc_flags_and_request_parameters_cannot_open_the_window(self):
		doc = self._changed(action="edited")
		for flag in ("kt_command_write", "kt_awd_command", "kt_evl_command", FAMILY, "ignore_permissions", "kt_fixture_wipe"):
			doc.flags[flag] = True
		frappe.form_dict.update({"kt_command_write_families": {FAMILY: 1}, FAMILY: 1, "flags": {"kt_command_write": 1}})
		self.addCleanup(frappe.form_dict.clear)
		self.assertEqual(self._code(guard_command_write, doc, FAMILY), "COMMAND_ONLY_WRITE")
		self.assertEqual(self._code(guard_command_delete, doc, FAMILY), "COMMAND_ONLY_DELETE")

	def test_a_posted_document_carrying_flags_is_still_refused(self):
		posted = frappe.get_doc(
			{
				"doctype": "Audit Event",
				"event_type": MARK,
				"document_type": "Procuring Entity",
				"document_name": MARK,
				"action": "forged",
				"performed_by": "Administrator",
				"flags": {"kt_command_write": True, FAMILY: True},
			}
		)
		self.assertEqual(self._code(guard_command_write, posted, FAMILY), "COMMAND_ONLY_WRITE")

	# -- allow-list --------------------------------------------------------------

	def _draft(self, before):
		return before.action == "draft"

	def test_allow_listed_field_on_an_editable_draft_is_accepted(self):
		self.doc.db_set("action", "draft", update_modified=False)
		doc = self._changed(entity="edited by the author")
		guard_command_write(doc, FAMILY, user_editable_fields=("entity",), user_editable_when=self._draft)

	def test_a_lifecycle_field_on_an_editable_draft_is_refused_and_named(self):
		self.doc.db_set("action", "draft", update_modified=False)
		doc = self._changed(entity="fine", event_type="not fine")
		with self.assertRaises(CommandWriteError) as caught:
			guard_command_write(doc, FAMILY, user_editable_fields=("entity",), user_editable_when=self._draft)
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_FIELD")
		self.assertEqual(caught.exception.fields, ("event_type",))

	def test_an_allow_listed_field_after_the_draft_is_refused(self):
		doc = self._changed(entity="too late")  # stored action is not "draft"
		self.assertEqual(
			self._code(guard_command_write, doc, FAMILY, user_editable_fields=("entity",), user_editable_when=self._draft), "COMMAND_ONLY_WRITE"
		)

	def test_user_insert_needs_every_other_field_at_its_default(self):
		ok = frappe.new_doc("Audit Event")
		ok.entity = "drafted"
		guard_command_write(ok, FAMILY, user_editable_fields=("entity",), user_insert=True)
		forged = frappe.new_doc("Audit Event")
		forged.entity = "drafted"
		forged.action = "Approved"
		with self.assertRaises(CommandWriteError) as caught:
			guard_command_write(forged, FAMILY, user_editable_fields=("entity",), user_insert=True)
		self.assertEqual((caught.exception.code, caught.exception.fields), ("COMMAND_ONLY_FIELD", ("action",)))

	def test_a_draft_may_be_deleted_only_when_the_controller_says_so(self):
		guard_command_delete(self.doc, FAMILY, user_deletable_when=lambda doc: True)
		self.assertEqual(self._code(guard_command_delete, self.doc, FAMILY, user_deletable_when=lambda doc: False), "COMMAND_ONLY_DELETE")

	# -- the mixin and the maintenance path -------------------------------------

	def test_the_mixin_reads_its_class_declarations(self):
		class Guarded(CommandWriteGuardMixin, Document):
			command_write_family = FAMILY
			command_user_editable_fields = ("entity",)

			def user_editable_when(self, before):
				return True

			def user_deletable_when(self):
				return False

		def guarded(**values):
			doc = self._changed(**values)
			doc.__class__ = Guarded
			return doc

		guarded(entity="ok").validate()
		self.assertEqual(self._code(guarded(action="no").validate), "COMMAND_ONLY_FIELD")
		self.assertEqual(self._code(guarded(entity="ok").on_trash), "COMMAND_ONLY_DELETE")
		with command_write(FAMILY):
			guarded(action="yes").validate()
			guarded(entity="ok").on_trash()

	def test_maintenance_write_is_refused_inside_a_request_and_without_a_reason(self):
		with maintenance_write(FAMILY, reason="test"):
			self.assertTrue(command_write_active(FAMILY))
		self.assertFalse(command_write_active(FAMILY))
		with self.assertRaises(ValueError), maintenance_write(FAMILY, reason=""):
			pass
		frappe.local.request = object()
		self.addCleanup(lambda: setattr(frappe.local, "request", None))
		with self.assertRaises(CommandWriteError) as caught, maintenance_write(FAMILY, reason="test"):
			pass
		self.assertEqual(caught.exception.code, "COMMAND_MAINTENANCE_REFUSED")
