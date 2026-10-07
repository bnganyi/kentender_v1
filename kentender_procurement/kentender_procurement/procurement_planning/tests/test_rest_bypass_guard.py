# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-007 — the Annual Plan and Departmental Plan families change only
through the Planning commands.

The audit's reproductions, run through the paths a `PUT /api/resource`,
`DELETE /api/resource` and `frappe.client` call reach, as the Procurement
Planner, Departmental Author and Head of User Department (and an
Administrator, who bypasses DocPerm but not the guard). The command route is
proved to still write the same records."""

from __future__ import annotations

import frappe

from kentender_core.services.command_write_guard import CommandWriteError
from kentender_procurement.procurement_planning.services import plan_read, plan_workbench
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_finance import PlanFinanceCase, key

WRITERS = (fx.PLANNER, fx.AUTHOR, fx.HOD, "Administrator")


class TestPlanningRecordsAreCommandOnly(PlanFinanceCase):
	def setUp(self):
		super().setUp()
		accepted, item_id = self.ready_item()
		frappe.set_user("Administrator")
		self.accepted = accepted
		self.item_id = item_id
		self.version = accepted["annual_plan_version"]
		self.plan = frappe.db.get_value("Annual Plan Version", self.version, "annual_plan")
		self.item = frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id}, "name")
		self.allocation = frappe.get_all("Plan Source Allocation", filters={"plan_item": self.item}, pluck="name")[0]
		root = frappe.get_all("Departmental Plan", filters={"fiscal_year": fx.FY_OPEN, "organisation_unit": fx.OU_ALPHA}, pluck="name")[0]
		self.dpp = root
		self.dpp_version = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": root}, pluck="name")[0]
		self.dpp_entry = frappe.get_all("Departmental Plan Entry", filters={"dpp_version": self.dpp_version}, pluck="name")[0]

	def cases(self):
		return (
			("Annual Plan Version", self.version, {"version_status": "Active"}),
			("Annual Plan", self.plan, {"active_version": self.version}),
			("Annual Plan Item", self.item, {"item_state": "Dissolved", "title": "Rewritten after submission"}),
			("Plan Source Allocation", self.allocation, {"indicative_amount": 1}),
			("Departmental Plan", self.dpp, {"current_accepted_version": self.dpp_version}),
			("Departmental Plan Version", self.dpp_version, {"version_status": "Accepted"}),
			("Departmental Plan Entry", self.dpp_entry, {"indicative_amount": 999}),
		)

	def test_lifecycle_fields_cannot_be_set_over_the_client_api(self):
		for user in WRITERS:
			for doctype, name, values in self.cases():
				fieldname, value = next(iter(values.items()))
				with self.subTest(user=user, doctype=doctype, field=fieldname):
					before = frappe.db.get_value(doctype, name, fieldname)
					frappe.set_user(user)
					with self.assertRaises(frappe.PermissionError):
						frappe.client.set_value(doctype, name, fieldname, value)
					frappe.set_user("Administrator")
					self.assertEqual(frappe.db.get_value(doctype, name, fieldname), before)

	def test_a_document_save_is_refused_by_the_guard_whoever_saves_it(self):
		# The audit's pytest: set the field and save() as the role.
		for user in WRITERS:
			for doctype, name, values in self.cases():
				with self.subTest(user=user, doctype=doctype):
					frappe.set_user("Administrator")
					doc = frappe.get_doc(doctype, name)
					doc.update(values)
					frappe.set_user(user)
					with self.assertRaises(CommandWriteError) as caught:
						doc.save(ignore_permissions=True)
					self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")

	def test_a_direct_delete_is_refused(self):
		for user in WRITERS:
			for doctype, name, _values in self.cases():
				with self.subTest(user=user, doctype=doctype):
					frappe.set_user(user)
					with self.assertRaises(frappe.PermissionError):
						frappe.client.delete(doctype, name)
					with self.assertRaises(CommandWriteError) as caught:
						frappe.delete_doc(doctype, name, ignore_permissions=True)
					self.assertEqual(caught.exception.code, "COMMAND_ONLY_DELETE")
					frappe.set_user("Administrator")
					self.assertTrue(frappe.db.exists(doctype, name))

	def test_a_new_record_cannot_be_inserted_directly(self):
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(CommandWriteError) as caught:
			frappe.get_doc({"doctype": "Plan Source Allocation", "plan_item": self.item, "indicative_amount": 5}).insert(ignore_permissions=True)
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")

	def test_the_command_route_still_writes_the_same_records(self):
		frappe.set_user(fx.PLANNER)
		item = plan_read.get_plan_item(plan_item_id=self.item_id)
		plan_workbench.save_plan_item(
			plan_item=self.item_id, values=fx.item_values(title="Saved through the command route"),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Annual Plan Item", self.item, "title"), "Saved through the command route")
