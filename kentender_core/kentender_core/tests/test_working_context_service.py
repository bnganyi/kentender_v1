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


class TestLegacyResolverShim(WorkingContextCase):
	"""CTX-CHG-001 Phase D — resolve/select_working_context keep their response
	contract but store the corrected model: global PE + per-module FY."""

	def setUp(self):
		super().setUp()
		self.fy = self._fy(2222)
		self.ctx_a = self._context(self.pe_a, self.fy)
		self.ctx_b = self._context(self.pe_b, self.fy)
		self._permit(self.user_one, self.pe_a)
		self._permit(self.user_one, self.pe_b)

	def _fy(self, start_year: int) -> str:
		name = f"FY-{start_year}-{start_year + 1}"
		if not frappe.db.exists("Financial Year", name):
			doc = frappe.get_doc(
				{
					"doctype": "Financial Year",
					"start_year": start_year,
					"label": f"{start_year}/{str(start_year + 1)[-2:]}",
					"start_date": f"{start_year}-07-01",
					"end_date": f"{start_year + 1}-06-30",
					"record_status": "Available",
				}
			)
			doc.name = name
			doc.insert(ignore_permissions=True)
		self.addCleanup(
			frappe.delete_doc, "Financial Year", name, force=True,
			ignore_missing=True, ignore_permissions=True,
		)
		return name

	def _context(self, pe: str, fy: str) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": pe,
				"financial_year": fy,
				"context_status": "Active",
				"active_from": "2020-01-01 00:00:00",
				"active_to": "2099-12-31 23:59:59",
			}
		).insert(ignore_permissions=True)
		self.addCleanup(
			frappe.delete_doc, "PE Fiscal Year Context", doc.name, force=True,
			ignore_missing=True, ignore_permissions=True,
		)
		return doc.name

	def test_selecting_a_context_moves_the_global_pe_and_module_fy(self):
		from kentender_core.services.reference_data_resolver import select_working_context

		select_working_context("budget", self.ctx_b, self.user_one)
		self.assertEqual(wc.get_working_pe(self.user_one)["selected"]["id"], self.pe_b)
		self.assertEqual(
			frappe.defaults.get_user_default("kt_budget_financial_year", user=self.user_one),
			self.fy,
		)

	def test_resolution_follows_a_pe_switched_elsewhere(self):
		from kentender_core.services.reference_data_resolver import (
			resolve_working_context,
			select_working_context,
		)

		select_working_context("budget", self.ctx_a, self.user_one)
		# The rail (or any other module) moves the global working PE…
		wc.select_working_pe(self.pe_b, self.user_one)
		resolved = resolve_working_context("budget", self.user_one)
		# …and Budget's next resolution lands in the same entity, keeping its
		# own remembered year.
		self.assertIsNotNone(resolved["selected"])
		self.assertEqual(resolved["selected"]["procuring_entity"]["id"], self.pe_b)
		self.assertEqual(resolved["selected"]["financial_year"]["id"], self.fy)


class TestBudgetDefaultsMigration(WorkingContextCase):
	def test_patch_splits_and_is_idempotent(self):
		from kentender_budget.patches.migrate_budget_working_context_defaults import execute

		fy = "FY-2223-2224"
		if not frappe.db.exists("Financial Year", fy):
			doc = frappe.get_doc(
				{
					"doctype": "Financial Year",
					"start_year": 2223,
					"label": "2223/24",
					"start_date": "2223-07-01",
					"end_date": "2224-06-30",
					"record_status": "Available",
				}
			)
			doc.name = fy
			doc.insert(ignore_permissions=True)
		self.addCleanup(
			frappe.delete_doc, "Financial Year", fy, force=True,
			ignore_missing=True, ignore_permissions=True,
		)
		ctx = frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": self.pe_a,
				"financial_year": fy,
				"context_status": "Active",
				"active_from": "2020-01-01 00:00:00",
				"active_to": "2099-12-31 23:59:59",
			}
		).insert(ignore_permissions=True)
		self.addCleanup(
			frappe.delete_doc, "PE Fiscal Year Context", ctx.name, force=True,
			ignore_missing=True, ignore_permissions=True,
		)
		frappe.defaults.set_user_default("kt_budget_working_context", ctx.name, user=self.user_one)
		# Dangling id for the second user — dropped without migrating anything.
		frappe.defaults.set_user_default("kt_budget_working_context", "CTX-GONE", user=self.user_two)

		execute()
		execute()  # idempotent

		self.assertEqual(
			frappe.defaults.get_user_default("kt_budget_financial_year", user=self.user_one), fy
		)
		self.assertEqual(
			frappe.defaults.get_user_default("kt_working_procuring_entity", user=self.user_one),
			self.pe_a,
		)
		for user in (self.user_one, self.user_two):
			self.assertFalse(
				frappe.defaults.get_user_default("kt_budget_working_context", user=user)
			)
			self.addCleanup(
				frappe.defaults.clear_user_default, "kt_budget_financial_year", user
			)
			self.addCleanup(
				frappe.defaults.clear_user_default, "kt_working_procuring_entity", user
			)
