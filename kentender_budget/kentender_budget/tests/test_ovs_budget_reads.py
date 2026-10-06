# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Accounting Officer and the Head of Procurement Function read approved Budget
(OVS-CHG-001 v0.6 §4.1; plan Phase 10; tracker OVS6-1002; acceptance OVS-AC-008, OVS-AC-009).

"AO/HOPF can read approved current/historical allocations and authoritative commitment/reservation
position." Approved means a version that is Active, Superseded or Closed. A Draft or a version submitted
for approval, the approval task and every command stay with the people who hold them. The Head of User
Department's half of the row waits for the owner's "existing consumer relationship" (FU-OVS-30) and is
not built here."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services.budget_authorization import ensure_budget_governance_roles
from kentender_core.services import responsibility_administration as administration


class TestApprovedBudgetReads(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_governance_roles()
		frappe.set_user("Administrator")
		cls.suffix = uuid4().hex[:6]
		cls._cleanup: list[tuple[str, str]] = []
		base = 2900 + int(cls.suffix, 16) % 40 * 2
		cls.fy_active, cls.budget_active, cls.active = cls._budget(base, "Active")
		cls.fy_draft, cls.budget_draft, cls.draft = cls._budget(base + 1, "Draft")
		cls.users = {}
		for label, role in (("ao", "Accounting Officer"), ("hopf", "Head of Procurement Function")):
			cls.users[label] = cls._user(label)
			outcome = administration.grant(user=cls.users[label], business_role=role, organisation_unit="", fixture_namespace="BUD_OVS_TESTS", actor="Administrator")
			cls._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))
		cls.outsider = cls._user("outsider")
		frappe.db.commit()

	@classmethod
	def _budget(cls, year: int, status: str):
		fy = frappe.get_doc({"doctype": "Fiscal Year", "year": f"{year}-{year + 1}", "year_start_date": f"{year}-07-01", "year_end_date": f"{year + 1}-06-30"}).insert(ignore_permissions=True)
		cls._cleanup.append(("Fiscal Year", fy.name))
		budget = frappe.get_doc({"doctype": "Procurement Budget", "generated_reference": f"OVS-BUD-{year}-{cls.suffix}", "fiscal_year": fy.name, "currency": "KES"}).insert(ignore_permissions=True)
		cls._cleanup.append(("Procurement Budget", budget.name))
		version = frappe.get_doc({"doctype": "Procurement Budget Version", "generated_reference": f"OVS-BUD-{year}-{cls.suffix}-V1", "budget": budget.name, "version_number": 1,
			"status": status, "approval_reference": f"OVS-{year}", "approval_date": "2020-01-01", "authorised_total": 1, "approval_document": "/files/ovs.pdf", "currency": "KES"}).insert(ignore_permissions=True)
		cls._cleanup.append(("Procurement Budget Version", version.name))
		return fy.name, budget.name, version.name

	@classmethod
	def _user(cls, label: str) -> str:
		email = f"bud.ovs.{label}.{cls.suffix}@test.local"
		doc = frappe.get_doc({"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0, "user_type": "System User"}).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
		cls._cleanup.append(("User", doc.name))
		return email

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for doctype, name in reversed(cls._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDownClass()

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_both_offices_list_and_open_an_approved_budget_version(self):
		for label, user in self.users.items():
			frappe.set_user(user)
			self.assertIn(self.active, frappe.get_list("Procurement Budget Version", pluck="name"), label)
			self.assertIn(self.budget_active, frappe.get_list("Procurement Budget", pluck="name"), label)
			self.assertTrue(frappe.has_permission("Procurement Budget Version", "read", self.active, user=user), label)
			self.assertIsNone(contracts.forbidden_verdict(user), label)

	def test_a_draft_or_submitted_version_is_not_theirs_to_read(self):
		for label, user in self.users.items():
			frappe.set_user(user)
			self.assertNotIn(self.draft, frappe.get_list("Procurement Budget Version", pluck="name"), label)
			self.assertNotIn(self.budget_draft, frappe.get_list("Procurement Budget", pluck="name"), label)
			self.assertFalse(frappe.has_permission("Procurement Budget Version", "read", self.draft, user=user), label)
			self.assertFalse(frappe.has_permission("Procurement Budget", "read", self.budget_draft, user=user), label)
			self.assertEqual(contracts.get_budget_version_draft(self.draft), {"outcome": "NOT_FOUND"}, label)
		frappe.db.set_value("Procurement Budget Version", self.draft, "status", "Submitted for approval")
		for label, user in self.users.items():
			frappe.set_user(user)
			self.assertFalse(frappe.has_permission("Procurement Budget Version", "read", self.draft, user=user), label)
		frappe.set_user("Administrator")
		frappe.db.set_value("Procurement Budget Version", self.draft, "status", "Draft")

	def test_the_workspace_of_a_year_with_only_a_pending_budget_shows_no_pending_version(self):
		for label, user in self.users.items():
			frappe.set_user(user)
			workspace = contracts.get_budget_workspace(self.fy_draft)
			self.assertNotIn("pending_version", workspace, label)
			self.assertEqual(workspace.get("available_actions"), [], label)

	def test_the_line_doctypes_follow_the_version_they_belong_to(self):
		from kentender_budget.services import budget_read_scope as scope

		for label, user in self.users.items():
			for doctype in ("Procurement Budget Line", "Procurement Budget Line Version"):
				self.assertIn("status in", scope.permission_query_conditions(user, doctype), f"{label} {doctype}")

	def test_a_person_with_no_responsibility_and_the_existing_readers_are_unchanged(self):
		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Procurement Budget Version", pluck="name")
		self.assertIsNotNone(contracts.forbidden_verdict(self.outsider))
		frappe.set_user("Administrator")
		self.assertIn(self.draft, frappe.get_list("Procurement Budget Version", pluck="name"))
