# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §17.10 (CFG row), FU-CM-48, plan D7 (tracker CM8-308): the configuration the native adapter and guards depend on is
checked, and every gap names the missing mapping and who recovers it. Settings are changed for a test and put back."""

from __future__ import annotations

import unittest
from contextlib import contextmanager

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.native import fields, readiness
from kentender_contracts.tests import native_world as world
from kentender_core.services import business_role_registry as registry

COMPANY = world.COMPANY


def setUpModule():
	if frappe.db.db_type != "mariadb":
		raise unittest.SkipTest("readiness reads ERPNext configuration on the MariaDB test site")
	fields.ensure()


@contextmanager
def setting(doctype, field, value):
	previous = frappe.db.get_single_value(doctype, field)
	frappe.db.set_single_value(doctype, field, value)
	try:
		yield
	finally:
		frappe.db.set_single_value(doctype, field, previous)


def keys(gaps):
	return {g["key"] for g in gaps}


class TestReadiness(IntegrationTestCase):
	def setUp(self):
		world.suspend_workflows()  # a site with the canonical world holds a Finance workflow of its own; these tests read a site that has none

	def tearDown(self):
		world.drop_workflow()

	def test_every_gap_names_the_problem_the_owner_and_where_to_fix_it(self):
		with setting("Stock Settings", "enable_serial_and_batch_no_for_item", 0), setting("Accounts Settings", "check_supplier_invoice_uniqueness", 0):
			gaps = readiness.check(COMPANY)
		self.assertTrue(gaps)
		for gap in gaps:
			self.assertTrue(all(gap[k] for k in ("key", "problem", "owner", "fix")), gap)

	def test_serial_numbers_and_invoice_uniqueness_are_global_settings_and_are_named_when_off(self):
		with setting("Stock Settings", "enable_serial_and_batch_no_for_item", 0), setting("Accounts Settings", "check_supplier_invoice_uniqueness", 0):
			gaps = {g["key"]: g for g in readiness.check(COMPANY)}
		self.assertIn("stock_serial_and_batch", gaps)
		self.assertIn("invoice_uniqueness", gaps)
		self.assertIn("Stock", gaps["stock_serial_and_batch"]["owner"])
		with setting("Stock Settings", "enable_serial_and_batch_no_for_item", 1), setting("Accounts Settings", "check_supplier_invoice_uniqueness", 1):
			self.assertTrue({"stock_serial_and_batch", "invoice_uniqueness"}.isdisjoint(keys(readiness.check(COMPANY))))

	def test_a_missing_payment_entry_workflow_is_named_and_a_self_approving_one_is_too(self):
		self.assertIn("payment_workflow", keys(readiness.check(COMPANY)))
		world.ensure_workflow()
		self.assertNotIn("payment_workflow", keys(readiness.check(COMPANY)))
		frappe.db.set_value("Workflow Transition", {"parent": world.WORKFLOW, "action": "Approve"}, "allow_self_approval", 1)
		gaps = {g["key"]: g for g in readiness.check(COMPANY)}
		self.assertIn("payment_workflow", gaps)
		self.assertIn("self-approval", gaps["payment_workflow"]["problem"])

	def test_a_payment_mode_with_no_account_for_the_company_is_named(self):
		if not frappe.db.exists("Mode of Payment", "CM Test Mode"):
			frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "CM Test Mode", "type": "Bank"}).insert(ignore_permissions=True)
		try:
			gaps = {g["key"]: g for g in readiness.check(COMPANY, mode_of_payment="CM Test Mode")}
			self.assertIn("payment_mode_account", gaps)
			self.assertIn("CM Test Mode", gaps["payment_mode_account"]["problem"])
			self.assertNotIn("payment_mode_account", keys(readiness.check(COMPANY)))  # nothing to check when no mode is named
		finally:
			frappe.delete_doc("Mode of Payment", "CM Test Mode", force=True, ignore_permissions=True)

	def test_the_contract_fields_on_native_documents_are_checked(self):
		self.assertNotIn("custom_fields", keys(readiness.check(COMPANY)))
		name = frappe.db.get_value("Custom Field", {"dt": "Asset", "fieldname": "cm_unit_reference"})
		frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
		try:
			gaps = {g["key"]: g for g in readiness.check(COMPANY)}
			self.assertIn("custom_fields", gaps)
			self.assertIn("Asset.cm_unit_reference", gaps["custom_fields"]["problem"])
		finally:
			fields.ensure()
		self.assertNotIn("custom_fields", keys(readiness.check(COMPANY)))

	def test_a_company_with_no_payable_account_is_named(self):
		previous = frappe.db.get_value("Company", COMPANY, "default_payable_account")
		frappe.db.set_value("Company", COMPANY, "default_payable_account", None)
		try:
			self.assertIn("payable_account", keys(readiness.check(COMPANY)))
		finally:
			frappe.db.set_value("Company", COMPANY, "default_payable_account", previous)

	def test_the_workflow_must_give_the_maker_step_to_finance_preparation_and_the_approving_step_to_finance_approval(self):
		registry.ensure_roles()
		world.ensure_workflow()  # the fixture workflow is allowed to Accounts User / Accounts Manager, not to the registered responsibilities
		gaps = {g["key"]: g for g in readiness.check(COMPANY)}
		self.assertIn("finance_role_mapping", gaps)
		self.assertIn("Finance approval", gaps["finance_role_mapping"]["problem"])
		self.assertIn("System setup", gaps["finance_role_mapping"]["owner"] + gaps["finance_role_mapping"]["fix"])
		frappe.db.set_value("Workflow Transition", {"parent": world.WORKFLOW, "action": "Submit for approval"}, "allowed", "Finance preparation")
		frappe.db.set_value("Workflow Transition", {"parent": world.WORKFLOW, "action": ["in", ["Approve", "Return"]]}, "allowed", "Finance approval")
		self.assertNotIn("finance_role_mapping", keys(readiness.check(COMPANY)))
		frappe.db.set_value("Workflow Transition", {"parent": world.WORKFLOW, "action": "Approve"}, "allowed", "Finance preparation")  # the maker's own role approves
		self.assertIn("finance_role_mapping", keys(readiness.check(COMPANY)))

