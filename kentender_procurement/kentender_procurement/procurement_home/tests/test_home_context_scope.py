"""CTX-CHG-001 v1.1 §2 — Home shows the site's one Procuring Entity and never asks anyone to choose it.
(Before v1.1 the offer was derived from User Permission rows and a global working-entity preference; those are retired.)"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_home.services.home_context import (
	list_available_entities,
	resolve_home_context,
)


class TestHomeContextScope(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.addCleanup(frappe.set_user, "Administrator")
		self.pe = self._pe("A")
		self.other = self._pe("B")
		self.user = self._user("scoped")
		self._permit(self.user, self.pe)
		for key in ("kt_working_procuring_entity", "kt_home_financial_year"):
			frappe.defaults.clear_user_default(key, self.user)
			self.addCleanup(frappe.defaults.clear_user_default, key, self.user)

	def _user(self, label: str) -> str:
		email = f"homectx.{label}.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", email, force=True, ignore_permissions=True)
		return email

	def _pe(self, label: str) -> str:
		code = f"PE-HOME{label}-{self.suffix}".upper()
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": code,
				"legal_name": f"Home Test Entity {label}",
				"reporting_currency": "KES",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "Procuring Entity", code, force=True, ignore_permissions=True)
		return code

	def _permit(self, user: str, pe: str) -> None:
		name = frappe.get_doc(
			{"doctype": "User Permission", "user": user, "allow": "Procuring Entity", "for_value": pe}
		).insert(ignore_permissions=True).name
		self.addCleanup(frappe.delete_doc, "User Permission", name, force=True, ignore_permissions=True)
		frappe.clear_cache(user=user)
		self.addCleanup(frappe.clear_cache, user=user)

	def site_entity(self) -> str:
		return frappe.db.get_single_value("Site Procuring Entity", "pe_code")

	def test_every_user_is_offered_the_sites_one_entity_and_nothing_else(self):
		# CTX-CHG-001 v1.1 §2: the site's own entity is shown, never chosen; no User Permission is needed or read
		for user in (self.user, "Administrator"):
			offered = [e["id"] for e in list_available_entities(user)]
			self.assertEqual(offered, [self.site_entity()], user)
			self.assertNotIn(self.pe, offered)
			self.assertNotIn(self.other, offered)

	def test_the_context_shows_no_entity_selector(self):
		resolved = resolve_home_context(user=self.user)
		self.assertEqual(resolved["procuring_entity"]["id"], self.site_entity())
		self.assertFalse(resolved["show_entity_selector"])
		self.assertEqual(len(resolved["available_entities"]), 1)

	def test_a_request_for_another_entity_is_refused(self):
		with self.assertRaises(frappe.PermissionError):
			resolve_home_context(procuring_entity=self.other, user=self.user)

	def test_the_old_global_preference_is_neither_read_nor_written(self):
		frappe.defaults.set_user_default("kt_working_procuring_entity", self.other, user=self.user)
		self.assertEqual(resolve_home_context(user=self.user)["procuring_entity"]["id"], self.site_entity())
		frappe.defaults.clear_user_default("kt_working_procuring_entity", self.user)
		resolve_home_context(procuring_entity=self.site_entity(), user=self.user)
		self.assertIsNone(frappe.defaults.get_user_default("kt_working_procuring_entity", user=self.user))

	def test_a_user_with_no_entity_permission_still_resolves_home(self):
		bare = self._user("bare")
		self.assertEqual(resolve_home_context(user=bare)["procuring_entity"]["id"], self.site_entity())

	def test_migration_patch_copies_and_retires_idempotently(self):
		from kentender_core.patches.migrate_kt_procuring_entity_to_working_pe import execute

		if frappe.db.has_column("User", "kt_procuring_entity"):
			frappe.db.set_value("User", self.user, "kt_procuring_entity", self.pe, update_modified=False)
		execute()
		execute()
		self.assertFalse(
			frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "kt_procuring_entity"})
		)
