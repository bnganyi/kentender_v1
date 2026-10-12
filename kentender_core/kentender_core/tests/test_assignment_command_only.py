"""AUD-XC-013 (assignment records) and AUD-XC-136 (who may grant to whom).

A `User Responsibility Assignment` is created, changed and revoked only by
`responsibility_administration` (AUTH-ADR-001 §9.2, §15): Administrator and
System Manager hold read, never write, create or delete on it, and the
controller refuses the same writes for Administrator, who passes Frappe's own
permission check regardless of DocPerm. The administration commands also
refuse a self-grant and a grant to a technical account.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_assignment_command_only
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import responsibility_administration as administration
from kentender_core.services.command_write_guard import CommandWriteError
from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_ASGN_GUARD"
GUARDED = (
	"User Responsibility Assignment",
	"Operational Scope Assignment",
	"Capability Profile",
	"Workflow Queue",
	"Workflow Queue Membership",
	"Workflow Routing Rule",
	"Workflow Task",
	"Authorization Delegation",
	"Separation of Duties Rule",
)


class AssignmentGuardCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		fx.ensure_site_configured()
		cls.unit = fx.unit("KT Test Asgn Guard Unit", namespace=NS)
		cls.admin = fx.user("asgn.admin", roles=("System Manager",))
		cls.admin_two = fx.user("asgn.admin.two", roles=("System Manager",))
		cls.holder = fx.user("asgn.holder")
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")

	def _assignment(self) -> str:
		return administration.grant(
			user=self.holder, business_role="Departmental Author", organisation_unit=self.unit, fixture_namespace=NS, actor="Administrator"
		)["assignment"]


class TestAssignmentRecordIsCommandOnly(AssignmentGuardCase):
	def test_no_role_holds_write_create_or_delete_on_a_guarded_doctype(self):
		"""The first lock: DocPerm. Read stays, the write path is gone."""
		for doctype in GUARDED:
			for permission in frappe.get_meta(doctype).permissions:
				self.assertFalse(
					permission.write or permission.create or permission.delete,
					f"{doctype}: {permission.role} still holds write/create/delete",
				)

	def test_a_system_manager_cannot_change_or_delete_an_assignment_through_the_api(self):
		name = self._assignment()
		frappe.set_user(self.admin)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.set_value("User Responsibility Assignment", name, "status", "Revoked")
		with self.assertRaises(frappe.PermissionError):
			frappe.client.delete("User Responsibility Assignment", name)
		self.assertEqual(frappe.db.get_value("User Responsibility Assignment", name, "status"), "Enabled")
		self.assertTrue(frappe.db.exists("User Responsibility Assignment", name))

	def test_the_controller_refuses_the_same_writes_for_administrator(self):
		"""Administrator passes Frappe's permission check whatever DocPerm says,
		so this is the lock that actually holds for that account."""
		name = self._assignment()
		with self.assertRaises(CommandWriteError) as saved:
			frappe.client.set_value("User Responsibility Assignment", name, "status", "Revoked")
		self.assertEqual(saved.exception.code, "COMMAND_ONLY_WRITE")
		with self.assertRaises(CommandWriteError) as deleted:
			frappe.client.delete("User Responsibility Assignment", name)
		self.assertEqual(deleted.exception.code, "COMMAND_ONLY_DELETE")
		with self.assertRaises(CommandWriteError) as inserted:
			frappe.get_doc(
				{"doctype": "User Responsibility Assignment", "user": self.holder, "business_role": "Auditor", "appointment_type": "Permanent", "status": "Enabled"}
			).insert()
		self.assertEqual(inserted.exception.code, "COMMAND_ONLY_WRITE")
		self.assertEqual(frappe.db.get_value("User Responsibility Assignment", name, "status"), "Enabled")

	def test_the_administration_commands_still_work(self):
		name = self._assignment()
		self.assertEqual(frappe.db.get_value("User Responsibility Assignment", name, "status"), "Enabled")
		result = administration.revoke(name, reason="Revoked inside the command-only test.", actor="Administrator")
		self.assertTrue(result["revoked"])
		self.assertEqual(frappe.db.get_value("User Responsibility Assignment", name, "status"), "Revoked")


class TestGrantRules(AssignmentGuardCase):
	def test_an_administrator_cannot_assign_a_responsibility_to_themselves(self):
		with self.assertRaises(ResponsibilityError) as caught:
			administration.grant(user=self.admin, business_role="Departmental Author", organisation_unit=self.unit, fixture_namespace=NS, actor=self.admin)
		self.assertEqual(caught.exception.code, "AUTH_SEGREGATION_BLOCKED")
		self.assertFalse(frappe.db.exists("User Responsibility Assignment", {"user": self.admin}))

	def test_a_grant_to_a_technical_account_is_refused(self):
		for technical in ("Administrator", self.admin_two):
			with self.assertRaises(ResponsibilityError) as caught:
				administration.grant(user=technical, business_role="Auditor", fixture_namespace=NS, actor=self.admin)
			self.assertEqual(caught.exception.code, "AUTH_CONFIGURATION_INVALID", technical)
		self.assertFalse(frappe.db.exists("User Responsibility Assignment", {"user": ("in", ("Administrator", self.admin_two))}))

	def test_a_technical_account_may_hold_a_technical_operation_responsibility(self):
		"""The canonical seed's technical operator is a System Manager who holds the Technical Operator responsibility."""
		for role in ("Technical Operator", "Release Operator", "Evaluation Technical Support"):
			result = administration.grant(user=self.admin_two, business_role=role, fixture_namespace=NS, actor=self.admin)
			self.assertTrue(result["created"], role)

	def test_one_administrator_can_assign_another_person(self):
		person = fx.user("asgn.person")
		result = administration.grant(user=person, business_role="Departmental Author", organisation_unit=self.unit, fixture_namespace=NS, actor=self.admin)
		self.assertTrue(result["created"])

	def test_the_preview_names_the_refusal_before_anything_is_saved(self):
		frappe.set_user(self.admin)
		own = administration.preview_assignment(user=self.admin, business_role="Departmental Author", organisation_unit=self.unit)
		self.assertFalse(own["ok"])
		self.assertEqual([p["field"] for p in own["problems"]], ["user"])
		technical = administration.preview_assignment(user=self.admin_two, business_role="Departmental Author", organisation_unit=self.unit)
		self.assertFalse(technical["ok"])
		ordinary = administration.preview_assignment(user=self.holder, business_role="Departmental Author", organisation_unit=self.unit)
		self.assertTrue(ordinary["ok"], ordinary)

	def test_a_scheduled_assignment_cannot_be_moved_to_the_administrator_or_a_technical_account(self):
		future = "2097-01-01 00:00:00"
		name = administration.grant(
			user=self.holder, business_role="Departmental Author", organisation_unit=self.unit, effective_from=future, fixture_namespace=NS, actor="Administrator"
		)["assignment"]
		for target in (self.admin, self.admin_two):
			with self.assertRaises(ResponsibilityError):
				administration.update_scheduled(
					name, user=target, business_role="Departmental Author", organisation_unit=self.unit, effective_from=future, actor=self.admin
				)
		self.assertEqual(frappe.db.get_value("User Responsibility Assignment", name, "user"), self.holder)
