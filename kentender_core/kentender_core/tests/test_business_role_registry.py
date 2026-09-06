"""AUTH-ADR-001 v1.6 §4.4 — the code-owned business-role registry.

Administrators assign registered responsibilities; they do not define new
roles, scope types or capability strings in production. These tests hold the
registry to the shape §4.4 requires: exactly two scope types, no technical
role registered, no retired role resurrected.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_business_role_registry
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import business_role_registry as registry
from kentender_core.services.responsibility_errors import ResponsibilityError


class TestBusinessRoleRegistry(IntegrationTestCase):
	def test_exactly_two_scope_types_exist(self):
		"""§4.4 — `Site-wide` or `Organisation Unit`. No other value exists."""
		self.assertEqual(registry.SCOPE_TYPES, ("Site-wide", "Organisation Unit"))
		for name, entry in registry.REGISTRY.items():
			self.assertIn(entry.scope_type, registry.SCOPE_TYPES, f"{name} has no valid scope type")

	def test_scope_type_decides_whether_the_record_names_a_unit(self):
		"""§4.5 — OU required for OU roles, prohibited for Site-wide roles."""
		for entry in registry.REGISTRY.values():
			self.assertEqual(
				entry.requires_organisation_unit, entry.scope_type == registry.SCOPE_OU
			)

	def test_no_procuring_entity_or_global_dimension_survives(self):
		"""§1.1 — the Global and Procuring Entity scope types are removed."""
		self.assertFalse(hasattr(registry, "SCOPE_GLOBAL"))
		self.assertFalse(hasattr(registry, "SCOPE_PE"))
		for entry in registry.REGISTRY.values():
			self.assertFalse(hasattr(entry, "requires_procuring_entity"))

	def test_the_departmental_responsibilities_are_the_organisation_unit_ones(self):
		"""§4.4 — Requisition Preparer stays unregistered until REQ-CHG-001's
		cutover slice names it (KT-STD-001 §7 default-to-omit)."""
		self.assertEqual(
			registry.roles_with_scope_type(registry.SCOPE_OU),
			("Departmental Author", "Head of User Department"),
		)

	def test_reference_data_manager_is_removed(self):
		"""CFG-CHG-002 v0.6 §1.1 — no Reference Data Manager role exists."""
		self.assertNotIn("Reference Data Manager", registry.REGISTRY)

	def test_no_registered_role_declares_an_exclusive_office_yet(self):
		"""§4.7's mechanism exists in the administration service, but the
		KT-STD-001 §8.3 seed places two simultaneous HoUD holders in the same
		unit (Peter + Grace's Cartesian fixture) and ADR §16 marks the
		AUTH-DES-05 conflict as artboard-only — so no entry may declare the
		flag until an owning module document does (tracker D4)."""
		for name, entry in registry.REGISTRY.items():
			self.assertFalse(entry.exclusive_office, f"{name} declares an undocumented exclusive office")

	def test_every_entry_names_the_document_that_owns_its_role_name(self):
		"""§4.4 — the module document is the source of the exact role name."""
		for name, entry in registry.REGISTRY.items():
			self.assertTrue(entry.owning_document, f"{name} does not name its owning document")

	def test_administrator_and_system_manager_are_not_business_responsibilities(self):
		"""§4.4/§8 — technical inspection is not a business assignment."""
		self.assertNotIn("Administrator", registry.REGISTRY)
		self.assertNotIn("System Manager", registry.REGISTRY)
		self.assertEqual(registry.TECHNICAL_ROLES, frozenset({"Administrator", "System Manager"}))

	def test_one_auditor_label_serves_every_module(self):
		"""NDS, Budget and PLN v1.12 all name `Auditor`; the earlier
		`Planning Auditor` label is retired (PLN tracker D6)."""
		self.assertIn("Auditor", registry.REGISTRY)
		self.assertNotIn("Planning Auditor", registry.REGISTRY)
		self.assertEqual(registry.scope_type("Finance Confirmation Officer"), registry.SCOPE_SITE)
		self.assertNotIn("finance_confirmation", registry.REGISTRY["Budget Officer"].sod_tags)

	def test_strategy_roles_are_site_wide(self):
		"""§20 — Strategy Author and Approver bind to Site-wide scope."""
		self.assertEqual(registry.scope_type("Strategy Author"), registry.SCOPE_SITE)
		self.assertEqual(registry.scope_type("Strategy Approver"), registry.SCOPE_SITE)

	def test_an_unregistered_role_is_refused_with_the_configuration_code(self):
		with self.assertRaises(ResponsibilityError) as caught:
			registry.require_registered("Applicable Final Authority")
		self.assertEqual(caught.exception.code, "AUTH_CONFIGURATION_INVALID")

	def test_every_projection_role_exists_after_ensure_roles(self):
		registry.ensure_roles()
		for role in registry.all_projected_frappe_roles():
			self.assertTrue(frappe.db.exists("Role", role), f"Role {role} was not provisioned")

	def test_system_manager_may_administer_every_registered_role(self):
		for name in registry.REGISTRY:
			self.assertTrue(registry.may_administer(name, {"System Manager"}))
			self.assertFalse(registry.may_administer(name, {"Desk User"}))
