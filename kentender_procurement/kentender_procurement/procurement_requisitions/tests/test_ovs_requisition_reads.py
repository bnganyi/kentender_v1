# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Accounting Officer reads authorised Requisitions (OVS-CHG-001 v0.6 §4.1; plan Phase 10;
tracker OVS6-1004; acceptance OVS-AC-008, OVS-AC-009).

"AO receives read-only authorised Requisitions and their decision/history." The grant is read-only and
only for a Requisition that was authorised (or later revoked): never a Draft, never one still in review,
and never a command. The same grant is checked at the framework hooks (list, record) and in the record
read the screen uses."""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_requisitions.services import read, records
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase

AO = fx.ACCOUNTING_OFFICER


class TestAccountingOfficerReadsAuthorised(RequisitionCase):
	def authorised(self) -> str:
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		fx.authorise(requisition)
		return requisition

	def test_the_accounting_officer_lists_and_opens_an_authorised_requisition(self):
		requisition = self.authorised()
		frappe.set_user(AO)
		self.assertIn(requisition, frappe.get_list("Procurement Requisition", pluck="name"))
		self.assertTrue(frappe.has_permission("Procurement Requisition", "read", requisition, user=AO))
		record = read.get_requisition_record(requisition=requisition, user=AO)
		self.assertNotIn(record.get("outcome"), ("NOT_FOUND", "FORBIDDEN"), record.get("outcome"))
		register = read.get_requisition_workspace(user=AO)
		self.assertIn(requisition, [r["requisition"] for r in register["register"]])

	def assert_hidden_from_ao(self, name: str):
		frappe.set_user(AO)
		self.assertNotIn(name, frappe.get_list("Procurement Requisition", pluck="name"))
		self.assertFalse(frappe.has_permission("Procurement Requisition", "read", name, user=AO))
		self.assertEqual(read.get_requisition_record(requisition=name, user=AO).get("outcome"), "NOT_FOUND")
		self.assertNotIn(name, [r["requisition"] for r in read.get_requisition_workspace(user=AO)["register"]])

	def test_a_draft_is_not_found_to_the_accounting_officer(self):
		_, item_id = fx.active_item()
		self.assert_hidden_from_ao(fx.prepare(item_id)["requisition"])

	def test_a_requisition_still_in_review_is_not_found_to_the_accounting_officer(self):
		_, item_id = fx.active_item()
		self.assert_hidden_from_ao(fx.submitted(item_id))

	def test_the_grant_gives_no_command(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		with self.assertRaises((ProcurementRequisitionsError, frappe.DoesNotExistError, frappe.PermissionError)):
			fx.authorise(requisition, user=AO)
		self.assertNotEqual(records.load(requisition)[0].current_state, "Authorised")

	def test_a_person_without_the_responsibility_is_unchanged(self):
		requisition = self.authorised()
		frappe.set_user(fx.FINANCE_OFFICER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Procurement Requisition", pluck="name")
		self.assertEqual(read.get_requisition_record(requisition=requisition, user=fx.FINANCE_OFFICER).get("outcome"), "FORBIDDEN")
