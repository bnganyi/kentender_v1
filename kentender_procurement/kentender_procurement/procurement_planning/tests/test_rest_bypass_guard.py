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
import frappe.tests

from kentender_core.services.command_write_guard import CommandWriteError
from kentender_procurement.procurement_planning.write_family import PLANNING_WRITE_FAMILY
from kentender_procurement.procurement_planning.services import plan_read, plan_workbench
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_finance import PlanFinanceCase, key

WRITERS = (fx.PLANNER, fx.AUTHOR, fx.HOD, "Administrator")

PLANNING_FAMILY = (
	"Annual Plan", "Annual Plan Version", "Annual Plan Item", "Plan Source Allocation",
	"Departmental Plan", "Departmental Plan Version", "Departmental Plan Entry",
)

RIGHTS = ("write", "create", "delete", "submit", "cancel", "amend", "share")


def rights_held(doctypes):
	"""Every (doctype, role, right) the DocPerm and Custom DocPerm tables grant
	among the write-side rights. Read from the tables, not from meta, so a
	Custom DocPerm added after the last migrate is seen too."""
	held = []
	for table in ("DocPerm", "Custom DocPerm"):
		for row in frappe.get_all(table, filters={"parent": ("in", list(doctypes))}, fields=["parent", "role", *RIGHTS]):
			held.extend((row.parent, row.role, right) for right in RIGHTS if row.get(right))
	return held



class TestPlanningDocPermsGrantNoWrite(frappe.tests.IntegrationTestCase):
	"""The DocPerm is the first lock (AUD-XC-007): after a migrate no role,
	System Manager included, holds a write-side right on a command-only
	Planning record."""

	def test_no_role_holds_a_write_side_right_on_a_planning_record(self):
		self.assertEqual(rights_held(PLANNING_FAMILY), [])


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


# -- RG-02: every other Planning record is command-only too --------------------

# Planning doctypes that are deliberately NOT command-only, with the reason. A new
# Planning doctype must either join the family or be named here.
NOT_COMMAND_ONLY = {
	"Annual Plan Publication Destination": "site configuration of the publication adapter (its sandbox outcome), not approval evidence",
}


def planning_records() -> list[str]:
	"""Every non-child, non-single doctype of the Procurement Planning module that
	is installed on the site, minus the named exceptions."""
	return sorted(
		name for name in frappe.get_all("DocType", filters={"module": "Procurement Planning", "istable": 0, "issingle": 0}, pluck="name")
		if name not in NOT_COMMAND_ONLY
	)


class TestEveryPlanningRecordIsCommandOnly(frappe.tests.IntegrationTestCase):
	"""RG-02 / AUD-XC-013: the Planning decision, task, snapshot, publication,
	finance, signature, treasury, drawdown, correction and journal records are
	what the Planner segregation chain and the allowance arithmetic read. A
	System Manager or Administrator must not be able to write or delete them."""

	def test_the_walk_finds_the_planning_records(self):
		names = planning_records()
		for expected in ("Plan Governance Task", "Approved Plan Snapshot", "Plan Drawdown Reference", "Planning Command Journal", "Plan Item"):
			self.assertIn(expected, names)

	def test_no_role_holds_a_write_side_right_on_any_planning_record(self):
		self.assertEqual(rights_held(planning_records()), [])

	def test_every_planning_record_controller_takes_the_planning_guard(self):
		from frappe.model.base_document import get_controller

		unguarded = [
			name for name in planning_records()
			if getattr(get_controller(name), "command_write_family", "") != PLANNING_WRITE_FAMILY
		]
		self.assertEqual(unguarded, [])

	def test_a_direct_insert_or_delete_is_refused_for_every_planning_record(self):
		frappe.set_user("Administrator")
		for name in planning_records():
			with self.subTest(doctype=name):
				doc = frappe.new_doc(name)
				with self.assertRaises(CommandWriteError) as inserted:
					doc.run_method("validate")
				self.assertEqual(inserted.exception.code, "COMMAND_ONLY_WRITE")
				with self.assertRaises(CommandWriteError) as deleted:
					doc.run_method("on_trash")
				self.assertEqual(deleted.exception.code, "COMMAND_ONLY_DELETE")


class TestPlanningEvidenceRowsCannotBeRewritten(PlanFinanceCase):
	"""The reproductions of REG-STATE-02 against real rows."""

	def setUp(self):
		super().setUp()
		accepted, _item_id = self.ready_item()
		result = self.request(accepted["annual_plan"])
		frappe.set_user("Administrator")
		self.finance_task = result["task"]
		self.validation_task = frappe.get_all("Departmental Plan Validation Task", filters={"fiscal_year": fx.FY_OPEN}, pluck="name")[0]
		self.journal = frappe.get_all("Planning Command Journal", pluck="name", limit=1)[0]

	def cases(self):
		return (
			("Plan Finance Task", self.finance_task, "status", "Completed"),
			("Departmental Plan Validation Task", self.validation_task, "status", "Cancelled"),
			("Planning Command Journal", self.journal, "command", "tampered"),
		)

	def test_a_rewrite_or_delete_is_refused_whoever_asks(self):
		for doctype, name, fieldname, value in self.cases():
			before = frappe.db.get_value(doctype, name, fieldname)
			self.assertTrue(before is not None and before != value, f"{doctype}.{fieldname} fixture")
			with self.subTest(doctype=doctype):
				with self.assertRaises(frappe.PermissionError):
					frappe.client.set_value(doctype, name, fieldname, value)
				with self.assertRaises(CommandWriteError) as caught:
					frappe.delete_doc(doctype, name, ignore_permissions=True)
				self.assertEqual(caught.exception.code, "COMMAND_ONLY_DELETE")
				self.assertEqual(frappe.db.get_value(doctype, name, fieldname), before)
				self.assertTrue(frappe.db.exists(doctype, name))

	def test_a_direct_insert_is_refused(self):
		with self.assertRaises(CommandWriteError) as caught:
			frappe.get_doc(
				{"doctype": "Plan Finance Task", "task_reference": "FNT-REST-BYPASS", "plan_version": frappe.db.get_value("Plan Finance Task", self.finance_task, "plan_version")}
			).insert(ignore_permissions=True)
		self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE")
