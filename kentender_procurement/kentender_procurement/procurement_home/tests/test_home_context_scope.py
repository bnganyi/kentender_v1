"""CTX-CHG-001 Phase E — Home's entity offer is permission-derived and its
context resolves from the corrected server-side preferences."""

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

	def test_a_scoped_user_sees_only_their_entities(self):
		offered = {e["id"] for e in list_available_entities(self.user)}
		self.assertEqual(offered, {self.pe})

	def test_an_unrestricted_user_still_gets_the_operational_list(self):
		offered = list_available_entities("Administrator")
		self.assertTrue(offered)

	def test_an_out_of_scope_selection_is_refused(self):
		with self.assertRaises(frappe.PermissionError):
			resolve_home_context(procuring_entity=self.other, user=self.user)

	def test_the_global_working_pe_is_the_default(self):
		self._permit(self.user, self.other)
		frappe.defaults.set_user_default(
			"kt_working_procuring_entity", self.other, user=self.user
		)
		resolved = resolve_home_context(user=self.user)
		self.assertEqual(resolved["procuring_entity"]["id"], self.other)

	def test_an_explicit_selection_persists_globally(self):
		self._permit(self.user, self.other)
		resolve_home_context(procuring_entity=self.other, user=self.user)
		self.assertEqual(
			frappe.defaults.get_user_default("kt_working_procuring_entity", user=self.user),
			self.other,
		)

	def test_migration_patch_copies_and_retires_idempotently(self):
		from kentender_core.patches.migrate_kt_procuring_entity_to_working_pe import execute

		if frappe.db.has_column("User", "kt_procuring_entity"):
			frappe.db.set_value("User", self.user, "kt_procuring_entity", self.pe, update_modified=False)
		execute()
		execute()
		self.assertFalse(
			frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "kt_procuring_entity"})
		)
