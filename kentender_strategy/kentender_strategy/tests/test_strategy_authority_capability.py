# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §5/§8 / SCL-502..504 — explicit Strategy capability checks,
not Administrator/System-Manager identity stand-ins or silent fallbacks."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_permissions import (
	ensure_strategy_roles,
	has_cross_entity_authority,
)
from kentender_strategy.services.strategy_reference import resolve_pe_for_doc


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_strategy_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	for role in ("Strategy Officer", "Strategy Manager", "Planning Authority"):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


class TestStrategyAuthorityCapability(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_planning_authority_has_cross_entity_authority(self):
		"""SCL-502 — a real Planning Authority assignment grants cross-entity
		context switch, with no dependence on the Administrator identity."""
		email = _ensure_user("str.cross.planning@example.com", ["Planning Authority"], self.pe)
		self.assertTrue(has_cross_entity_authority(email))

	def test_officer_has_no_cross_entity_authority(self):
		"""SCL-502 — a Strategy Officer (no elevated role) is scoped to their own PE."""
		email = _ensure_user("str.cross.officer@example.com", ["Strategy Officer"], self.pe)
		self.assertFalse(has_cross_entity_authority(email))

	def test_resolve_pe_for_doc_fails_closed(self):
		"""SCL-504 — no procuring_entity, no resolvable plan_version: raise, don't
		silently return None for the caller to trip over later."""
		doc = frappe._dict({"doctype": "Performance Measurement"})
		with self.assertRaises(frappe.ValidationError):
			resolve_pe_for_doc(doc)

	def test_resolve_pe_for_doc_resolves_via_plan_version(self):
		plan_id = self.seed["plan"]
		doc = frappe._dict({"doctype": "Strategy Programme", "plan_version": plan_id})
		self.assertEqual(resolve_pe_for_doc(doc), self.pe)
