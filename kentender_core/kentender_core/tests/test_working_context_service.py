"""CTX-CHG-001 Phase A — working-context service: global PE preference,
per-module FY/OU memory, scrub-stable keys, per-user isolation.

The durable rule under test: permissions determine access; context only
filters current work — never authoritative, revalidated on every resolution,
and an invalid saved value resolves to "prompt again", never to access and
never to an error.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.org_scope_access import permitted_procuring_entities
from kentender_core.services import working_context as wc


class WorkingContextCase(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.addCleanup(frappe.set_user, "Administrator")
		self.pe_a = self._pe("A")
		self.pe_b = self._pe("B")
		self.user_one = self._user("one")
		self.user_two = self._user("two")

	def _user(self, label: str) -> str:
		email = f"ctxchg.{label}.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", email, force=True, ignore_permissions=True)
		return email

	def _pe(self, label: str) -> str:
		code = f"PE-CTX{label}-{self.suffix}".upper()
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": code,
				"legal_name": f"Context Test Entity {label}",
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


class TestKeyDiscipline(WorkingContextCase):
	def test_keys_are_scrub_stable(self):
		"""The frappe.defaults Title-Case trap must be unreachable."""
		key = wc._module_key("needs", "financial_year")
		self.assertEqual(key, frappe.scrub(key))
		with self.assertRaises(ValueError):
			wc._module_key("My Module", "financial_year")
		with self.assertRaises(ValueError):
			wc._module_key("needs", "colour")

	def test_defaults_round_trip_through_get_user_default(self):
		"""Regression for is_a_user_permission_key: a stored value must come
		back through the exact API the resolvers read with."""
		key = wc._module_key("needs", "financial_year")
		frappe.defaults.set_user_default(key, "FY-2222-2223", user=self.user_one)
		self.assertEqual(
			frappe.defaults.get_user_default(key, user=self.user_one), "FY-2222-2223"
		)


class TestEligibilityRule(WorkingContextCase):
	def test_multiple_user_permission_rows_all_count(self):
		"""permitted_procuring_entities must return EVERY User Permission PE.

		The previous fallback read one arbitrary row (frappe.db.get_value), so
		a user permitted three entities was silently narrowed to one — the
		exact class of defect rule 1 forbids.
		"""
		self._permit(self.user_one, self.pe_a)
		self._permit(self.user_one, self.pe_b)
		self.assertEqual(permitted_procuring_entities(self.user_one), {self.pe_a, self.pe_b})


class TestWorkingPe(WorkingContextCase):
	def test_modes_none_single_multiple_unrestricted(self):
		self.assertEqual(wc.get_working_pe(self.user_one)["mode"], "none")
		self._permit(self.user_one, self.pe_a)
		single = wc.get_working_pe(self.user_one)
		self.assertEqual(single["mode"], "single")
		# Rule 5.1 — a single eligible option auto-selects.
		self.assertEqual(single["selected"]["id"], self.pe_a)
		self.assertFalse(single["can_switch"])
		self._permit(self.user_one, self.pe_b)
		multiple = wc.get_working_pe(self.user_one)
		self.assertEqual(multiple["mode"], "multiple")
		self.assertTrue(multiple["can_switch"])
		self.assertTrue(multiple["selection_required"])
		unrestricted = wc.get_working_pe("Administrator")
		self.assertEqual(unrestricted["mode"], "unrestricted")
		self.assertTrue(unrestricted["can_switch"])
		offered = {opt["id"] for opt in unrestricted["options"]}
		self.assertIn(self.pe_a, offered)
		self.assertIn(self.pe_b, offered)

	def test_selection_persists_and_revalidates(self):
		self._permit(self.user_one, self.pe_a)
		self._permit(self.user_one, self.pe_b)
		wc.select_working_pe(self.pe_b, self.user_one)
		# Rule 5.2 — the last valid selection resolves on the next request.
		self.assertEqual(wc.get_working_pe(self.user_one)["selected"]["id"], self.pe_b)

	def test_out_of_set_selection_is_refused(self):
		self._permit(self.user_one, self.pe_a)
		with self.assertRaises(frappe.PermissionError):
			wc.select_working_pe(self.pe_b, self.user_one)

	def test_invalid_saved_preference_prompts_again(self):
		"""Rule 5.3 — a saved selection that is no longer valid re-prompts;
		it never errors and never resolves."""
		self._permit(self.user_one, self.pe_a)
		self._permit(self.user_one, self.pe_b)
		frappe.defaults.set_user_default(wc.GLOBAL_PE_KEY, "PE-GONE", user=self.user_one)
		resolved = wc.get_working_pe(self.user_one)
		self.assertIsNone(resolved["selected"])
		self.assertTrue(resolved["selection_required"])

	def test_preferences_are_per_user(self):
		"""The localStorage cross-user leak class must be impossible here."""
		for user in (self.user_one, self.user_two):
			self._permit(user, self.pe_a)
			self._permit(user, self.pe_b)
		wc.select_working_pe(self.pe_a, self.user_one)
		wc.select_working_pe(self.pe_b, self.user_two)
		self.assertEqual(wc.get_working_pe(self.user_one)["selected"]["id"], self.pe_a)
		self.assertEqual(wc.get_working_pe(self.user_two)["selected"]["id"], self.pe_b)


class TestModuleDimensions(WorkingContextCase):
	OFFER = ["FY-2222-2223", "FY-2223-2224"]

	def test_membership_validation_and_persistence(self):
		wc.select_module_fy("needs", self.OFFER[1], self.user_one, offered=self.OFFER)
		resolved = wc.get_module_fy("needs", self.user_one, offered=self.OFFER)
		self.assertEqual(resolved["selected"]["id"], self.OFFER[1])
		with self.assertRaises(frappe.PermissionError):
			wc.select_module_fy("needs", "FY-9999-0000", self.user_one, offered=self.OFFER)

	def test_single_offered_auto_selects(self):
		resolved = wc.get_module_fy("needs", self.user_one, offered=[self.OFFER[0]])
		self.assertEqual(resolved["selected"]["id"], self.OFFER[0])
		self.assertFalse(resolved["selection_required"])

	def test_modules_remember_independently(self):
		"""Rule 3 — Budget and Needs legitimately work in different years."""
		wc.select_module_fy("needs", self.OFFER[1], self.user_one, offered=self.OFFER)
		wc.select_module_fy("budget", self.OFFER[0], self.user_one, offered=self.OFFER)
		self.assertEqual(
			wc.get_module_fy("needs", self.user_one, offered=self.OFFER)["selected"]["id"],
			self.OFFER[1],
		)
		self.assertEqual(
			wc.get_module_fy("budget", self.user_one, offered=self.OFFER)["selected"]["id"],
			self.OFFER[0],
		)

	def test_saved_value_outside_offer_prompts_again(self):
		wc.select_module_fy("needs", self.OFFER[0], self.user_one, offered=self.OFFER)
		narrowed = wc.get_module_fy("needs", self.user_one, offered=[self.OFFER[1]])
		# Auto-select of the single remaining option beats a stale memory.
		self.assertEqual(narrowed["selected"]["id"], self.OFFER[1])
		several = wc.get_module_fy(
			"needs", self.user_one, offered=["FY-3000-3001", "FY-3001-3002"]
		)
		self.assertIsNone(several["selected"])
		self.assertTrue(several["selection_required"])

	def test_org_unit_dimension(self):
		units = ["OU-ONE", "OU-TWO"]
		wc.select_module_ou("needs", "OU-TWO", self.user_one, offered=units)
		self.assertEqual(
			wc.get_module_ou("needs", self.user_one, offered=units)["selected"]["id"], "OU-TWO"
		)
		with self.assertRaises(frappe.PermissionError):
			wc.select_module_ou("needs", "OU-ELSEWHERE", self.user_one, offered=units)
