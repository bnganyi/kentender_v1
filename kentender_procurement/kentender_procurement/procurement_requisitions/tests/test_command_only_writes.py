# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-013 — decisions, handoffs, versions, events and the other
Requisition records change only through the Requisitions commands. Administrator
and System Manager hold read, not write, create or delete; and the controller
refuses the same writes for Administrator, who passes Frappe's own permission
check whatever DocPerm says (REQ-CHG-001 v1.14 invariant 12, §8)."""

from __future__ import annotations

import frappe

from kentender_core.services.command_write_guard import CommandWriteError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase

FAMILY = (
	"Procurement Requisition",
	"Requisition Version",
	"Requisition Task",
	"Requisition Decision",
	"Authorised Requisition Handoff",
	"IT Equipment Requirement Package",
	"IT Equipment Requirement Package Version",
	"Requisition Event",
	"Requisition Correction Outcome",
	"Requisition Command Journal",
)


def _a_plain_field(doctype: str) -> str:
	"""A non-standard field (`set_value` refuses the standard ones before it checks permission)."""
	return next(df.fieldname for df in frappe.get_meta(doctype).fields if df.fieldtype in ("Data", "Small Text", "Text", "Long Text", "Code") and not df.fieldname.startswith("fixture"))


SM = "reqt.guard.sysman@example.test"


class TestRequisitionRecordsAreCommandOnly(RequisitionCase):
	def _world(self) -> dict[str, str]:
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		fx.authorise(requisition)
		frappe.set_user("Administrator")
		root = frappe.get_doc("Procurement Requisition", requisition)
		package = frappe.db.get_value("IT Equipment Requirement Package", {"requisition": requisition}, "name")
		return {
			"Procurement Requisition": requisition,
			"Requisition Version": root.authorised_version,
			"Requisition Task": frappe.db.get_value("Requisition Task", {"requisition": requisition}, "name"),
			"Requisition Decision": frappe.db.get_value("Requisition Decision", {"requisition_version": root.authorised_version}, "name"),
			"Authorised Requisition Handoff": root.handoff,
			"IT Equipment Requirement Package": package,
			"IT Equipment Requirement Package Version": frappe.db.get_value("IT Equipment Requirement Package Version", {"package": package}, "name"),
			"Requisition Event": frappe.db.get_value("Requisition Event", {"requisition": requisition}, "name"),
			"Requisition Command Journal": frappe.db.get_value("Requisition Command Journal", {"document_name": requisition}, "name")
			or frappe.db.get_value("Requisition Command Journal", {}, "name"),
		}

	def _system_manager(self) -> str:
		from kentender_procurement.procurement_planning.tests import fixtures as pln_fx

		pln_fx._user(SM, "REQ Test System Manager")
		frappe.get_doc("User", SM).add_roles("System Manager")
		self.addCleanup(self._remove_system_manager)
		return SM

	def _remove_system_manager(self) -> None:
		frappe.set_user("Administrator")
		for contact in frappe.get_all("Contact Email", filters={"email_id": SM}, pluck="parent"):
			frappe.delete_doc("Contact", contact, force=1, ignore_permissions=True)
		if frappe.db.exists("User", SM):
			frappe.delete_doc("User", SM, force=1, ignore_permissions=True)

	def test_no_role_holds_write_create_or_delete_on_a_requisition_record(self):
		for doctype in FAMILY:
			for permission in frappe.get_meta(doctype).permissions:
				self.assertFalse(
					permission.write or permission.create or permission.delete,
					f"{doctype}: {permission.role} still holds write/create/delete",
				)

	def test_a_system_manager_cannot_change_or_delete_any_of_them_through_the_api(self):
		world = self._world()
		manager = self._system_manager()
		frappe.set_user(manager)
		for doctype, name in world.items():
			self.assertTrue(name, f"the world built no {doctype}")
			with self.assertRaises(frappe.PermissionError, msg=doctype):
				frappe.client.set_value(doctype, name, _a_plain_field(doctype), "x")
			with self.assertRaises(frappe.PermissionError, msg=doctype):
				frappe.client.delete(doctype, name)
			self.assertTrue(frappe.db.exists(doctype, name), doctype)

	def test_the_controller_refuses_a_save_delete_or_insert_by_administrator(self):
		world = self._world()
		frappe.set_user("Administrator")
		for doctype, name in world.items():
			with self.assertRaises(CommandWriteError, msg=f"{doctype} save") as saved:
				frappe.get_doc(doctype, name).save()
			self.assertEqual(saved.exception.code, "COMMAND_ONLY_WRITE", doctype)
			with self.assertRaises(CommandWriteError, msg=f"{doctype} delete") as deleted:
				frappe.delete_doc(doctype, name)
			self.assertEqual(deleted.exception.code, "COMMAND_ONLY_DELETE", doctype)
			with self.assertRaises(CommandWriteError, msg=f"{doctype} insert") as inserted:
				frappe.get_doc({"doctype": doctype}).insert()
			self.assertEqual(inserted.exception.code, "COMMAND_ONLY_WRITE", doctype)
			self.assertTrue(frappe.db.exists(doctype, name), doctype)

	def test_a_changed_decision_or_handoff_digest_is_refused_where_it_matters(self):
		"""The reproduction in the finding: rewriting the handoff payload so its stored digest no longer matches."""
		world = self._world()
		frappe.set_user("Administrator")
		handoff = frappe.get_doc("Authorised Requisition Handoff", world["Authorised Requisition Handoff"])
		before = handoff.payload_json
		handoff.payload_json = '{"tampered": true}'
		with self.assertRaises(CommandWriteError):
			handoff.save()
		with self.assertRaises(CommandWriteError):
			frappe.client.set_value("Requisition Decision", world["Requisition Decision"], "decision", "Return")
		self.assertEqual(frappe.db.get_value("Authorised Requisition Handoff", handoff.name, "payload_json"), before)
