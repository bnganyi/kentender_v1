# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The `coming-soon` Page is the shell's Home placeholder — the Procurement app
tile on Frappe's apps screen and the rail's "Home" entry both route to
`/desk/coming-soon?feature=Home`. It carried a hand-maintained role list that
predated the KT-STD-001 §8 register, so a Budget Approver (Beatrice Kamau)
landed on a "Not permitted" modal over the bare Frappe desk (2026-09-11). Like
every KenTender Vue-in-Desk page it now has no role restriction: reaching Desk
at all is the only gate, and each module's own contracts decide what a role
may do once inside."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup


class TestHomePlaceholderPageAccess(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_home_placeholder_has_no_role_restriction(self):
		page = frappe.get_doc("Page", "coming-soon")
		self.assertEqual([r.role for r in page.roles], [], "coming-soon must be open to every Desk user")

	def test_every_seeded_register_actor_may_open_home(self):
		"""Every actor the site seed registers (KT-STD-001 §8.3) reaches Home.
		Only actors present on this site are exercised; the role-list assertion
		above is the structural guarantee."""
		page = frappe.get_doc("Page", "coming-soon")
		exercised = 0
		for local, _label in site_setup.ACTORS:
			email = f"{local}@moh.example.test"
			if not frappe.db.exists("User", email):
				continue
			frappe.set_user(email)
			self.assertTrue(page.is_permitted(), f"{email} cannot open the Home placeholder")
			exercised += 1
		frappe.set_user("Administrator")
		self.assertGreater(exercised, 0, "no register actor found on this site — seed KT-STD-001 §8 first")
