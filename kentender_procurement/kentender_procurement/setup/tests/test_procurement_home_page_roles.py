# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`kt-procurement-home` must admit every current KenTender business role.

Replaces `test_procurement_home_demands_roles.py`, which asserted the *retired*
Demand-era role set. That test passed continuously while **42 enabled users
across 5 modules were locked out of the entire Desk** with "Not permitted",
because it only ever checked that seven specific legacy roles were still
present — never that the roles the module rebuilds had introduced were.

The important test here is `test_no_kentender_role_holder_is_locked_out`. It is
deliberately **data-driven rather than list-driven**: a test that compares the
page against a hard-coded list can only fail when someone edits the list, which
is the same failure the original had. This one looks at who actually holds a
role on the site, so the next module rebuild that renames a role and forgets
this page fails here, naming the role.
"""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.setup.procurement_home_page import (
	LANDING_ROLES,
	PAGE_NAME,
	RETIRED_ROLES,
)

# Roles that legitimately do not reach the procurement Desk home: Frappe/ERPNext
# stock roles that ship with the bench, and the supplier-portal roles, which use
# the portal rather than the Desk. Anything outside this set that ends up locked
# out is a KenTender role that was forgotten — which is the defect being guarded.
_NOT_KENTENDER_DESK_ROLES: frozenset[str] = frozenset(
	{
		# Framework
		"All", "Guest", "Desk User", "Report Manager", "Script Manager",
		"Translator", "Website Manager", "Workspace Manager", "Newsletter Manager",
		"Blogger", "Dashboard Manager", "Knowledge Base Contributor",
		"Knowledge Base Editor", "Prepared Report User", "Inbox User",
		# ERPNext stock roles
		"Academics User", "Accounts Manager", "Accounts User", "Analytics",
		"Customer", "Delivery Manager", "Delivery User", "Employee",
		"Fleet Manager", "HR Manager", "HR User", "Item Manager",
		"Maintenance Manager", "Maintenance User", "Manufacturing Manager",
		"Manufacturing User", "Marketing Manager", "Projects Manager",
		"Projects User", "Purchase Manager", "Purchase Master Manager",
		"Purchase User", "Quality Manager", "Sales Manager",
		"Sales Master Manager", "Sales User", "Stock Manager", "Stock User",
		"Supplier", "Support Team",
		# Supplier portal — portal users, not Desk users
		"KenTender External Supplier",
	}
)


def _fixture_roles() -> set[str]:
	app_path = frappe.get_app_path("kentender_procurement")
	for candidate in (
		os.path.join(app_path, "kentender_procurement", "page", "kt_procurement_home", "kt_procurement_home.json"),
		os.path.join(app_path, "page", "kt_procurement_home", "kt_procurement_home.json"),
	):
		if os.path.isfile(candidate):
			return {row["role"] for row in json.loads(open(candidate).read())["roles"]}
	raise AssertionError("kt_procurement_home.json not found")


class TestProcurementHomePageRoles(IntegrationTestCase):
	def live_roles(self) -> set[str]:
		return {row.role for row in frappe.get_doc("Page", PAGE_NAME).roles}

	def test_the_checked_in_fixture_matches_the_declared_list(self):
		"""The JSON is generated from `LANDING_ROLES`; drift means a hand-edit.

		Checked because a fresh install imports the fixture before any
		`after_migrate` reconcile runs, so a stale JSON is a real lockout on a
		new environment even when existing ones are fine.
		"""
		self.assertEqual(_fixture_roles(), set(LANDING_ROLES))

	def test_the_live_record_matches_the_declared_list(self):
		self.assertEqual(self.live_roles(), set(LANDING_ROLES))

	def test_no_retired_role_survives_on_the_page(self):
		"""Reconciliation removes, it does not merge.

		`Demand Viewer` sat here with zero holders because the fixture was only
		ever added to; NDS-BR-020 forbids retaining a Demand-era role.
		"""
		self.assertEqual(self.live_roles() & RETIRED_ROLES, set())

	def test_no_kentender_role_holder_is_locked_out(self):
		"""The regression this whole module exists for.

		Data-driven on purpose: this fails when a rebuild introduces a role and
		forgets the landing page, without anyone having to remember to update a
		list in a test.
		"""
		allowed = self.live_roles()
		enabled = set(
			frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
		)
		held: dict[str, set[str]] = {}
		for row in frappe.get_all(
			"Has Role", filters={"parenttype": "User"}, fields=["parent", "role"], limit_page_length=0
		):
			if row.parent in enabled:
				held.setdefault(row.parent, set()).add(row.role)

		orphaned: dict[str, set[str]] = {}
		for user, roles in held.items():
			if user == "Administrator" or (roles & allowed):
				continue
			unexplained = roles - _NOT_KENTENDER_DESK_ROLES
			if unexplained:
				orphaned[user] = unexplained

		self.assertEqual(
			orphaned,
			{},
			msg=(
				"these users hold a KenTender role but cannot open "
				f"/desk/{PAGE_NAME} — add the role to LANDING_ROLES in "
				"kentender_procurement/setup/procurement_home_page.py: "
				+ "; ".join(f"{u} ({', '.join(sorted(r))})" for u, r in sorted(orphaned.items()))
			),
		)

	def test_every_declared_role_actually_opens_the_page(self):
		"""Asserted through Frappe's own resolver, not by reading the list back.

		`get_allowed_pages` is what the Desk consults, so this catches a role
		that is present on the record but rejected for another reason.
		"""
		from frappe.boot import get_allowed_pages

		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": "home.roles.probe@kentender.test",
				"first_name": "Home Roles Probe",
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", user.name, force=True, ignore_permissions=True)

		for role in sorted(set(LANDING_ROLES) - {"Administrator"}):
			with self.subTest(role=role):
				# Declaring a role that is missing, disabled, or portal-only is
				# itself the defect: it reads as granted and is refused. This
				# caught `Tender Manager`, which `mvp1_role_user_cleanup` had
				# disabled while it still sat on the page.
				self.assertTrue(frappe.db.exists("Role", role), f"{role} does not exist")
				flags = frappe.db.get_value(
					"Role", role, ["disabled", "desk_access"], as_dict=True
				)
				self.assertFalse(flags.disabled, f"{role} is disabled")
				self.assertTrue(flags.desk_access, f"{role} has no desk access")
				user.set("roles", [{"role": "Desk User"}, {"role": role}])
				user.save(ignore_permissions=True)
				frappe.clear_cache(user=user.name)
				frappe.set_user(user.name)
				try:
					self.assertIn(
						PAGE_NAME,
						set(get_allowed_pages()),
						msg=f"{role} is on the Page record but cannot open it",
					)
				finally:
					frappe.set_user("Administrator")

	def test_the_guard_is_not_vacuous(self):
		"""Prove the lockout check can fail, using the real defect's shape."""
		allowed = set(LANDING_ROLES) - {"Departmental Author"}
		roles = {"Desk User", "Departmental Author"}
		self.assertFalse(roles & allowed, "removing the role must orphan its holder")
		self.assertTrue(
			roles - _NOT_KENTENDER_DESK_ROLES,
			"a KenTender role must not be explained away as a stock role",
		)
