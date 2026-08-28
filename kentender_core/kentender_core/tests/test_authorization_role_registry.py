"""AUTH-ADR-001 — capability-to-Role registry and new-Role provisioning.

Covers the resolved mapping table (docs/mvp-1-r1/00_common/AUTH-ADR-001-capability-mapping.md
§9) — every capability the engine will resolve after cutover maps to exactly
one Frappe Role with an explicit scope classification, and the handful of new
Roles this migration introduces are created idempotently.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.authorization_role_registry import (
	CAPABILITY_ROLE_MAP,
	NEW_ROLES,
	ROLE_CLASSIFICATIONS,
	ensure_roles,
)


class TestAuthorizationRoleRegistry(IntegrationTestCase):
	def test_new_roles_are_created_idempotently(self):
		ensure_roles()
		ensure_roles()
		for role in NEW_ROLES:
			self.assertTrue(frappe.db.exists("Role", role), f"{role} should exist after ensure_roles()")
			self.assertEqual(frappe.db.count("Role", {"role_name": role}), 1)

	def test_every_mapped_role_has_a_classification(self):
		for capability, role in CAPABILITY_ROLE_MAP.items():
			self.assertIn(role, ROLE_CLASSIFICATIONS, f"{capability} maps to {role!r}, which has no scope classification")

	def test_reference_data_is_not_mapped_through_capability_strings(self):
		"""CFG-CHG-002 v0.4 / AUTH-AC-019 — Reference Data reads no
		reference_data.* capability string; it checks the Reference Data
		Manager Role directly (reference_data_permissions)."""
		for capability in CAPABILITY_ROLE_MAP:
			self.assertFalse(capability.startswith("reference_data."))
		self.assertEqual(ROLE_CLASSIFICATIONS["Reference Data Manager"], "global_central")

	def test_retired_reference_data_roles_have_no_classification(self):
		for role in (
			"Central Reference Data Steward",
			"Central Configuration Approver",
			"PE Configuration Steward",
			"Professional Configuration Reviewer / HoPF",
		):
			self.assertNotIn(role, ROLE_CLASSIFICATIONS)

	def test_budget_revision_apply_and_reserve_are_retired_not_mapped(self):
		self.assertNotIn("budget.revision.apply", CAPABILITY_ROLE_MAP)
		self.assertNotIn("budget.reserve", CAPABILITY_ROLE_MAP)

	def test_budget_approve_maps_to_activation_authority(self):
		self.assertEqual(CAPABILITY_ROLE_MAP["budget.approve"], "Budget Activation Authority")

	def test_departmental_needs_oversight_read_maps_to_auditor_not_budget_officer(self):
		self.assertEqual(CAPABILITY_ROLE_MAP["departmental_needs.oversight_read"], "Auditor")

	def test_dead_literals_are_absent(self):
		for literal in ("plan.item.complete", "demand.business.review", "demand.enrich", "demand.funding.confirm", "demand.approve"):
			self.assertNotIn(literal, CAPABILITY_ROLE_MAP)

	def test_diagnostic_view_removed_not_mapped(self):
		self.assertNotIn("authorization.diagnostic.view", CAPABILITY_ROLE_MAP)

	def test_support_record_view_maps_to_support_analyst(self):
		self.assertEqual(CAPABILITY_ROLE_MAP["support.record.view"], "KenTender Support Analyst")

	def test_task_reassign_maps_to_task_administrator(self):
		self.assertEqual(CAPABILITY_ROLE_MAP["authorization.task.reassign"], "KenTender Task Administrator")

	def test_plan_capabilities_are_out_of_engine_scope(self):
		"""plan.* stays on planning_permissions.py's own native Role model — the
		engine must not claim it, or the dual-path conflict recurs."""
		for capability in CAPABILITY_ROLE_MAP:
			self.assertFalse(capability.startswith("plan."), f"{capability} must not be mapped here — plan.* is Procurement Planning's own domain")

	def test_std_configuration_is_out_of_engine_scope(self):
		for capability in CAPABILITY_ROLE_MAP:
			self.assertFalse(capability.startswith("std_configuration."))
