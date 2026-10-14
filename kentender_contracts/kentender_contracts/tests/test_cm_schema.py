# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §4, §5.1, §5.17 and plan D3/D5 (tracker CM8-103): the spike
records exist in the Contract Management module, carry only the facts a named rule
needs, change only through Contract Management commands, and give no business
role a write path through Desk."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.command_write_guard import CommandWriteError, command_write, fixture_insert, purge_doc

MODULE = "Contract Management"
NAMESPACE = "CM_TEST"
RECORDS = ("Contract Case", "Contract Operation Intent", "Contract Command Journal")
SINGLES = ("Contract Test Environment Controls",)
FIELDS = {
	"Contract Case": {"contract_id", "source_kind", "source_reference", "supplier_organisation", "lifecycle", "record_version", "fixture_namespace"},
	"Contract Operation Intent": {"contract_case", "subject", "subject_version", "operation_kind", "operation_key", "operation_identity", "state",
		"recovery_owner", "result_reference", "attempts_json", "fixture_namespace"},
	"Contract Command Journal": {"idempotency_key", "command", "payload_hash", "result_json", "actor", "contract_case", "recorded_at", "fixture_namespace"},
	"Contract Test Environment Controls": {"signing_outcome", "native_failure_after_success"},
}


def options(doctype: str, fieldname: str) -> set[str]:
	return set(filter(None, (frappe.get_meta(doctype).get_field(fieldname).options or "").split("\n")))


class TestContractSchema(IntegrationTestCase):
	def tearDown(self) -> None:
		for doctype in ("Contract Command Journal", "Contract Operation Intent", "Contract Case"):
			for name in frappe.get_all(doctype, filters={"fixture_namespace": NAMESPACE}, pluck="name"):
				purge_doc(doctype, name)
		frappe.db.commit()

	def test_module_belongs_to_the_contracts_app(self):
		self.assertEqual(frappe.db.get_value("Module Def", MODULE, "app_name"), "kentender_contracts")
		for doctype in RECORDS + SINGLES:
			self.assertEqual(frappe.db.get_value("DocType", doctype, "module"), MODULE, doctype)

	def test_records_carry_the_spec_facts(self):
		for doctype, fields in FIELDS.items():
			have = {f.fieldname for f in frappe.get_meta(doctype).fields}
			self.assertEqual(fields - have, set(), doctype)

	def test_lifecycle_and_states_are_the_spec_vocabulary(self):
		self.assertEqual(options("Contract Case", "lifecycle"), {"Preparing", "Awaiting signatures", "Active", "Closed", "Did not proceed", "Terminated"})
		self.assertEqual(options("Contract Case", "source_kind"), {"KenTender award", "External record"})
		self.assertEqual(options("Contract Operation Intent", "state"), {"Recorded", "Attempting", "Succeeded", "Failed", "Uncertain", "Reconciled"})
		self.assertEqual(options("Contract Operation Intent", "operation_kind"), {
			"Purchase order", "Funding conversion", "Funding adjustment", "Funding closure", "Accepted receipt", "Native invoice", "Native payment",
			"Signing attempt", "Report dispatch", "Notice dispatch"})
		self.assertEqual(options("Contract Test Environment Controls", "signing_outcome"), {"Unavailable", "Indeterminate", "Rejected"})

	def test_no_role_writes_through_desk(self):
		for doctype in RECORDS:
			for perm in frappe.get_meta(doctype).permissions:
				self.assertFalse(perm.write or perm.create or perm.delete, f"{doctype} gives {perm.role} a write path")

	def test_a_desk_save_is_refused_and_a_command_save_is_accepted(self):
		doc = frappe.get_doc({"doctype": "Contract Case", "contract_id": "CM-TEST-0001", "source_kind": "External record", "fixture_namespace": NAMESPACE})
		with self.assertRaises(CommandWriteError) as caught:
			doc.insert(ignore_permissions=True)
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")
		with command_write("Contract Management"):
			doc.insert(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Contract Case", "CM-TEST-0001", "lifecycle"), "Preparing")
		with self.assertRaises(CommandWriteError) as caught:
			frappe.delete_doc("Contract Case", "CM-TEST-0001", ignore_permissions=True)
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_DELETE")

	def test_one_operation_identity_names_one_native_effect(self):
		case = fixture_insert(frappe.get_doc({"doctype": "Contract Case", "contract_id": "CM-TEST-0002", "source_kind": "External record", "fixture_namespace": NAMESPACE}))
		row = {"doctype": "Contract Operation Intent", "contract_case": case.name, "subject": "agreement 1", "subject_version": 1, "operation_kind": "Purchase order",
			"operation_key": "k-1", "operation_identity": "CM-TEST-0002|agreement 1|1|Purchase order|k-1", "fixture_namespace": NAMESPACE}
		fixture_insert(frappe.get_doc(row))
		with self.assertRaises(frappe.UniqueValidationError):
			fixture_insert(frappe.get_doc(row))
