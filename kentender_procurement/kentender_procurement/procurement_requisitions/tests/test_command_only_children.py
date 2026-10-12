# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-06 (AUD-XC-013, child rows): the child-table rows of the guarded
Requisitions and Tenders parents change only through the owning commands.

Frappe's REST create inserts a child row on its own (the parent is never saved)
and a REST/`frappe.delete_doc` delete of a child row runs only the child's
controller, so a guard on the parent alone leaves both open to Administrator.
These tests drive the same calls the REST layer makes, on rows that carry a
made-up parent so no real record is touched, and clean up under the maintenance
window."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.command_write_guard import CommandWriteError, command_write, maintenance_write, purge_doc

# child doctype -> (parent doctype, parent field, family)
CHILDREN = {
	"Requisition Item": ("IT Equipment Requirement Package Version", "items", "Requisitions"),
	"Requisition Technical Requirement": ("IT Equipment Requirement Package Version", "technical_requirements", "Requisitions"),
	"Requisition Related Service": ("IT Equipment Requirement Package Version", "related_services", "Requisitions"),
	"Requisition Acceptance Requirement": ("IT Equipment Requirement Package Version", "acceptance_requirements", "Requisitions"),
	"Requisition Supporting Material": ("IT Equipment Requirement Package Version", "supporting_materials", "Requisitions"),
	"Requisition Contributing Unit": ("Procurement Requisition", "contributing_org_units", "Requisitions"),
	"Requisition Drawdown Line": ("Requisition Version", "drawdown_lines", "Requisitions"),
	"Tender Evidence Requirement": ("Tender Version", "evidence_requirements", "Tenders"),
	"Tender Review Finding": ("Tender Version", "review_findings", "Tenders"),
	"Tender Cancellation Obligation": ("Tender Cancellation", "obligations", "Tenders"),
	"Tender Candidate Notice Attempt": ("Tender Candidate Notice", "attempts", "Tenders"),
}
MARK = "RG06-NO-SUCH-PARENT"


def _row(doctype: str):
	parent_type, parent_field, _ = CHILDREN[doctype]
	return frappe.get_doc({"doctype": doctype, "parent": MARK, "parenttype": parent_type, "parentfield": parent_field})


class TestChildRowsAreCommandOnly(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(self._purge)

	def _purge(self):
		frappe.set_user("Administrator")
		for doctype in CHILDREN:
			for name in frappe.get_all(doctype, filters={"parent": MARK}, pluck="name"):
				purge_doc(doctype, name)
		frappe.db.commit()

	def _fixture_row(self, doctype: str) -> str:
		family = CHILDREN[doctype][2]
		doc = _row(doctype)
		with maintenance_write(family, reason="RG-06 test fixture child row"):
			doc.insert(ignore_permissions=True, ignore_mandatory=True, ignore_links=True)
		return doc.name

	def test_every_listed_child_is_covered_by_the_guard_in_its_controller(self):
		for doctype, (_, _, family) in CHILDREN.items():
			controller = frappe.get_doc({"doctype": doctype}).__class__
			self.assertEqual(getattr(controller, "command_write_family", ""), family, doctype)

	def test_a_child_row_cannot_be_inserted_alone_by_administrator(self):
		for doctype in CHILDREN:
			with self.assertRaises(CommandWriteError, msg=doctype) as caught:
				_row(doctype).insert(ignore_mandatory=True, ignore_links=True)
			self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE", doctype)
			self.assertFalse(frappe.db.exists(doctype, {"parent": MARK}), doctype)

	def test_a_child_row_cannot_be_deleted_or_changed_directly_by_administrator(self):
		for doctype in CHILDREN:
			name = self._fixture_row(doctype)
			with self.assertRaises(CommandWriteError, msg=f"{doctype} delete") as deleted:
				frappe.delete_doc(doctype, name)
			self.assertEqual(deleted.exception.code, "COMMAND_ONLY_DELETE", doctype)
			with self.assertRaises(CommandWriteError, msg=f"{doctype} save"):
				frappe.get_doc(doctype, name).save()
			self.assertTrue(frappe.db.exists(doctype, name), doctype)

	def test_the_owning_command_window_still_writes_and_deletes_the_row(self):
		for doctype, (_, _, family) in CHILDREN.items():
			doc = _row(doctype)
			with command_write(family):
				doc.insert(ignore_permissions=True, ignore_mandatory=True, ignore_links=True)
				frappe.delete_doc(doctype, doc.name, force=True, ignore_permissions=True)
			self.assertFalse(frappe.db.exists(doctype, doc.name), doctype)
