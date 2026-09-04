# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 Phase 4 (BUD-409, D6) — proof of effect for Budget's
registration in `kentender_scope_map` (AUTH-ADR-001 v1.6 §5.3), the first
production consumer of that mechanism anywhere in the codebase.

The scenario that actually distinguishes this from plain DocPerm: a user who
holds the `Budget Officer` Frappe Role directly (a stale grant, or one made
outside the real administration command) but has no Enabled `User
Responsibility Assignment`. Native DocPerm alone would let this user read a
Procurement Budget Version; the registered `has_permission` /
`permission_query_conditions` hooks close that gap by requiring a real,
active assignment underneath the Role.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services import responsibility_administration as administration
from kentender_budget.services.budget_authorization import ensure_budget_governance_roles


class TestScopeMapProofOfEffect(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_governance_roles()
		frappe.set_user("Administrator")
		cls.suffix = uuid4().hex[:6]
		cls._cleanup: list[tuple[str, str]] = []

		start_year = 2900 + int(cls.suffix, 16) % 90
		fy_doc = frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": f"{start_year}-{start_year + 1}",
				"year_start_date": f"{start_year}-07-01",
				"year_end_date": f"{start_year + 1}-06-30",
			}
		).insert(ignore_permissions=True)
		cls.fy = fy_doc.name
		cls._cleanup.append(("Fiscal Year", cls.fy))

		budget = frappe.get_doc(
			{
				"doctype": "Procurement Budget",
				"generated_reference": f"SCOPEMAP-BUD-{cls.suffix}",
				"fiscal_year": cls.fy,
				"currency": "KES",
			}
		).insert(ignore_permissions=True)
		cls.budget = budget.name
		cls._cleanup.append(("Procurement Budget", cls.budget))

		version = frappe.get_doc(
			{
				"doctype": "Procurement Budget Version",
				"generated_reference": f"SCOPEMAP-BUD-{cls.suffix}-V1",
				"budget": cls.budget,
				"version_number": 1,
				"status": "Draft",
				"approval_reference": f"SCOPEMAP-{cls.suffix}",
				"approval_date": "2020-01-01",
				"authorised_total": 1,
				"approval_document": "/files/scopemap-test.pdf",
				"currency": "KES",
			}
		).insert(ignore_permissions=True)
		cls.version = version.name
		cls._cleanup.append(("Procurement Budget Version", cls.version))

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for doctype, name in reversed(cls._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		super().tearDownClass()

	def _user_with_stale_role(self, label: str) -> str:
		"""A user with the `Budget Officer` Frappe Role granted directly
		(add_roles) — never through `responsibility_administration.grant`, so
		no `User Responsibility Assignment` backs it. Native DocPerm alone
		would treat this exactly like a real Budget Officer."""
		email = f"bud.scopemap.{label}.{self.suffix}@test.local"
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles("Desk User", "Budget Officer")
		self.__class__._cleanup.append(("User", email))
		return email

	def test_stale_role_without_assignment_is_denied_direct_read(self):
		"""D6 — the exact proof of effect: a Frappe Role without a matching
		Enabled assignment must not grant read via `has_permission`."""
		user = self._user_with_stale_role("stale")
		frappe.set_user(user)
		self.assertFalse(
			frappe.has_permission("Procurement Budget Version", doc=self.version, user=user),
			"a Budget Officer Role with no User Responsibility Assignment must not read directly",
		)
		with self.assertRaises(frappe.PermissionError):
			frappe.has_permission("Procurement Budget Version", doc=self.version, user=user, throw=True)

	def test_stale_role_without_assignment_is_excluded_from_list(self):
		"""The same gap, via `permission_query_conditions` — this is the list/
		count path §5.3 requires alongside `has_permission`."""
		user = self._user_with_stale_role("stalelist")
		frappe.set_user(user)
		rows = frappe.get_list(
			"Procurement Budget Version", filters={"name": self.version}, fields=["name"]
		)
		self.assertEqual(rows, [])

	def test_real_assignment_grants_direct_read(self):
		"""The positive case: an Enabled assignment through the real
		administration command grants exactly what the stale-Role case above
		was denied — proving the denial above is the assignment's absence,
		not something else."""
		email = f"bud.scopemap.real.{self.suffix}@test.local"
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "Real", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles("Desk User")
		self.__class__._cleanup.append(("User", email))
		outcome = administration.grant(
			user=email,
			business_role="Budget Officer",
			organisation_unit="",
			fixture_namespace="BUD_CHG_001_TESTS",
			actor="Administrator",
		)
		self.__class__._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))

		frappe.set_user(email)
		self.assertTrue(
			frappe.has_permission("Procurement Budget Version", doc=self.version, user=email),
			"an Enabled Budget Officer assignment must grant direct read",
		)

	def test_technical_reader_bypasses_the_scope_map(self):
		"""§8 — Administrator reads everything without any assignment,
		confirming the scope map never blocks a technical reader."""
		frappe.set_user("Administrator")
		self.assertTrue(
			frappe.has_permission("Procurement Budget Version", doc=self.version, user="Administrator")
		)
