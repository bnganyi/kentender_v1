"""AUD-XC-021 — a Frappe User Permission is not a fallback for which Procuring
Entity a user may work in (AUTH-ADR-001 §11.5 and §19). The site has one
entity; a user with a responsibility in force works in it, a user with only a
User Permission row works in none."""

from __future__ import annotations

from uuid import uuid4

import frappe

from kentender_core.services.command_write_guard import maintenance_write
from frappe.tests import IntegrationTestCase

from kentender_core.services import working_context as wc
from kentender_core.services.org_scope_access import permitted_procuring_entities


class TestPeScopeWithoutUserPermission(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.site_pe = frappe.db.get_single_value("Site Procuring Entity", "pe_code")
		if not self.site_pe or not frappe.db.exists("Procuring Entity", self.site_pe):
			self.skipTest("site has no configured Procuring Entity row")
		self.user = f"kt.test.upscope.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": self.user, "first_name": "UP", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		self.addCleanup(self._purge)

	def _purge(self):
		frappe.set_user("Administrator")
		for dt in ("User Permission", "User Responsibility Assignment"):
			frappe.db.delete(dt, {"user": self.user})
		if frappe.db.exists("User", self.user):
			frappe.delete_doc("User", self.user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user_permission(self):
		frappe.get_doc(
			{"doctype": "User Permission", "user": self.user, "allow": "Procuring Entity", "for_value": self.site_pe}
		).insert(ignore_permissions=True)
		frappe.clear_cache(user=self.user)

	def _responsibility(self):
		doc = frappe.get_doc(
			{
				"doctype": "User Responsibility Assignment",
				"user": self.user,
				"business_role": "Auditor",
				"appointment_type": "Permanent",
				"status": "Enabled",
				"fixture_namespace": "KT_TEST_UPSCOPE",
			}
		)
		with maintenance_write("Responsibility", reason="test fixture: a bare assignment row"):
			doc.insert(ignore_permissions=True)

	def test_user_permission_alone_offers_no_entity(self):
		self._user_permission()
		self.assertEqual(permitted_procuring_entities(self.user), set())
		self.assertEqual(wc.pe_options(self.user)["mode"], "none")

	def test_a_responsibility_in_force_works_in_the_site_entity(self):
		self._responsibility()
		self.assertEqual(permitted_procuring_entities(self.user), {self.site_pe})
		self.assertEqual(wc.pe_options(self.user)["mode"], "single")

	def test_user_with_neither_works_nowhere(self):
		self.assertEqual(permitted_procuring_entities(self.user), set())
