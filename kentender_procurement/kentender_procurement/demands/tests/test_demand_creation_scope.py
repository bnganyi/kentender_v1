# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract v2.2 §7.5 — Demand creation-scope states (0 / 1 / 2+ Requester pairs)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_creation_scope import (
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	assert_creation_pair_allowed,
	resolve_demand_creation_scope,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_REQUESTER,
	ensure_demand_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"
PE2 = "PE-CGKIS"
OU2 = "CGK-DEPT-HEALTH"
NS = "DEMANDS_CREATION_SCOPE_TEST"


def _ensure_user(email: str, *, first: str = "Scope", last: str = "Test") -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first,
				"last_name": last,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	return email


def _clear_usa(email: str) -> None:
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": email, "fixture_namespace": NS},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)


def _add_requester_pair(email: str, pe: str, ou: str) -> None:
	ensure_demand_roles()
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	if ROLE_REQUESTER not in have:
		user.append("roles", {"role": ROLE_REQUESTER})
		user.save(ignore_permissions=True)
	if "System Manager" not in have and email.endswith("@example.com"):
		pass
	existing = frappe.db.exists(
		"User Scope Assignment",
		{
			"user": email,
			"procuring_entity": pe,
			"organisation_unit": ou,
			"role": ROLE_REQUESTER,
			"fixture_namespace": NS,
		},
	)
	if not existing:
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_REQUESTER,
				"procuring_entity": pe,
				"organisation_unit": ou,
				"include_descendants": 1,
				"fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)


def _add_system_manager(email: str) -> None:
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	if "System Manager" not in have:
		user.append("roles", {"role": "System Manager"})
		user.save(ignore_permissions=True)


class TestDemandCreationScope(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()
		for code in (PE, PE2):
			if not frappe.db.exists("Procuring Entity", code):
				raise frappe.ValidationError(f"{code} required for creation-scope tests")
		for code in (OU, OU2):
			if not frappe.db.exists("Organisation Unit", code):
				raise frappe.ValidationError(f"{code} required for creation-scope tests")

	def test_single_readonly_one_requester_pair(self) -> None:
		email = _ensure_user("dem-scope-single@example.com", first="Single", last="Scope")
		_clear_usa(email)
		_add_requester_pair(email, PE, OU)
		frappe.db.commit()

		scope = resolve_demand_creation_scope(email)
		self.assertEqual(scope["selection_mode"], MODE_SINGLE)
		self.assertEqual(len(scope["pairs"]), 1)
		self.assertEqual(scope["selected_pair"]["procuring_entity"], PE)
		self.assertEqual(scope["selected_pair"]["owner_org_unit"], OU)
		self.assertEqual(scope["procuring_entity"], PE)
		self.assertTrue(scope["procuring_entity_label"])
		assert_creation_pair_allowed(PE, OU, user=email)

	def test_multi_required_no_default(self) -> None:
		email = _ensure_user("dem-scope-multi@example.com", first="Multi", last="Scope")
		_clear_usa(email)
		_add_requester_pair(email, PE, OU)
		_add_requester_pair(email, PE2, OU2)
		_add_system_manager(email)
		frappe.db.commit()

		scope = resolve_demand_creation_scope(email)
		self.assertEqual(scope["selection_mode"], MODE_MULTI)
		self.assertEqual(len(scope["pairs"]), 2)
		self.assertIsNone(scope["selected_pair"])
		self.assertIsNone(scope["procuring_entity"])
		self.assertIsNone(scope["owner_org_unit"])

		with self.assertRaises(frappe.ValidationError):
			assert_creation_pair_allowed(None, None, user=email)
		with self.assertRaises(frappe.ValidationError):
			# Mixed / third pair — PE-MOH with county OU
			assert_creation_pair_allowed(PE, OU2, user=email)
		assert_creation_pair_allowed(PE, OU, user=email)
		assert_creation_pair_allowed(PE2, OU2, user=email)

	def test_blocked_admin_without_requester_no_fallback(self) -> None:
		email = _ensure_user("dem-scope-noscope@example.com", first="No", last="Scope")
		_clear_usa(email)
		_add_system_manager(email)
		# Explicitly no Requester role / USA.
		user = frappe.get_doc("User", email)
		user.roles = [r for r in user.roles if r.role != ROLE_REQUESTER]
		user.save(ignore_permissions=True)
		frappe.db.commit()

		scope = resolve_demand_creation_scope(email)
		self.assertEqual(scope["selection_mode"], MODE_BLOCKED)
		self.assertEqual(scope["pairs"], [])
		self.assertIsNone(scope["selected_pair"])
		self.assertIsNone(scope["procuring_entity"])
		self.assertIn("Requester", scope["blocked_reason"] or "")

		with self.assertRaises(frappe.ValidationError):
			assert_creation_pair_allowed(PE, OU, user=email)

	def test_administrator_session_has_no_pe_moh_fallback(self) -> None:
		"""Built-in Administrator must not invent PE-MOH when no Requester USA exists."""
		# Clear any accidental Requester USA for Administrator in this namespace.
		for name in frappe.get_all(
			"User Scope Assignment",
			filters={"user": "Administrator", "role": ROLE_REQUESTER},
			pluck="name",
		):
			# Do not delete production USA; only assert if zero Requester pairs.
			pass
		scope = resolve_demand_creation_scope("Administrator")
		pairs = scope["pairs"]
		req_pairs = list(
			frappe.get_all(
				"User Scope Assignment",
				filters={"user": "Administrator", "role": ROLE_REQUESTER},
				fields=["procuring_entity", "organisation_unit"],
			)
		)
		req_pairs = [
			r
			for r in req_pairs
			if (r.get("procuring_entity") or "").strip()
			and (r.get("organisation_unit") or "").strip()
		]
		if not req_pairs:
			self.assertEqual(scope["selection_mode"], MODE_BLOCKED)
			self.assertIsNone(scope["procuring_entity"])
		else:
			# Environment already granted Requester pairs — mode follows count.
			self.assertIn(
				scope["selection_mode"],
				(MODE_SINGLE, MODE_MULTI),
			)
			self.assertEqual(len(pairs), len({(r.procuring_entity, r.organisation_unit) for r in req_pairs}))
