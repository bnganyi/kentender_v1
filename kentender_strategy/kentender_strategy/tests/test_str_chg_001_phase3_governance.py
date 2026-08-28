# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 Phase 3 — roles and permissions on authorization_policy.

Covers STR-BR-001-004 and STR-AC-003, 004, 010, 021, 022 at the service
layer (contract/UI-level verification of AC-021/022 is Phase 4/7/9 scope).
Rebuilt for v1.5's 2-role model: no Separation of Duties Rule is seeded any
more for Strategy — the only remaining rule is the direct same-version
self-check in strategy_authorization._blocked_by_self_approval (see Phase 2).
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services.authorization_role_registry import CAPABILITY_ROLE_MAP
from kentender_strategy.services.strategy_authorization import (
	CAP_APPROVE,
	CAP_AUTHOR,
	ROLE_STRATEGY_APPROVER,
	ROLE_STRATEGY_AUTHOR,
	ensure_strategy_governance_roles,
)
from kentender_strategy.services.strategy_transitions import available_actions, transition_plan_version

PE_MOH = "PE-MOH"
PE_CGKIS = "PE-CGKIS"


class TestGovernanceSeed(FrappeTestCase):
	def test_seed_is_idempotent_and_creates_expected_rows(self):
		ensure_strategy_governance_roles()
		second_run = ensure_strategy_governance_roles()
		self.assertEqual(second_run, {"roles": [], "sod_rules": []})

		for role in (ROLE_STRATEGY_AUTHOR, ROLE_STRATEGY_APPROVER):
			self.assertTrue(frappe.db.exists("Role", role))

		# AUTH-ADR-001 — authority is the Role + a native User Permission, not
		# a Capability Profile; confirm the registry maps each capability to
		# its expected Role instead of asserting on a retired profile record.
		self.assertEqual(CAPABILITY_ROLE_MAP[CAP_AUTHOR], ROLE_STRATEGY_AUTHOR)
		self.assertEqual(CAPABILITY_ROLE_MAP[CAP_APPROVE], ROLE_STRATEGY_APPROVER)


class TestSeededProfileEnforcement(FrappeTestCase):
	"""Uses the real, production-named CAP-STRATEGY-* profiles seeded above
	(not throwaway Phase 2 fixtures) to confirm the seed itself grants the
	right capability and nothing else."""

	def setUp(self):
		ensure_strategy_governance_roles()
		self.suffix = uuid4().hex[:8]
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def _track(self, doc):
		self._cleanup.append((doc.doctype, doc.name))
		return doc

	def _user(self, label: str) -> str:
		email = f"str.gov.{label}.{self.suffix}@test.local"
		self._track(
			frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		)
		return email

	def _grant(self, user: str, capability: str, pe: str) -> None:
		role = CAPABILITY_ROLE_MAP[capability]
		frappe.get_doc("User", user).add_roles(role)
		self._track(
			frappe.get_doc(
				{"doctype": "User Permission", "user": user, "allow": "Procuring Entity", "for_value": pe}
			).insert(ignore_permissions=True)
		)

	def _plan_and_version(self, pe: str) -> str:
		plan = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan",
					"title": f"Governance Test Plan {self.suffix}",
					"procuring_entity_id": pe,
					"plan_role": "Primary",
					"period_start": "2027-07-01",
					"period_end": "2032-06-30",
				}
			).insert(ignore_permissions=True)
		)
		version = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan Version",
					"plan_id": plan.name,
					"version_number": 1,
					"effective_from": "2027-07-01",
					"effective_to": "2032-06-30",
				}
			).insert(ignore_permissions=True)
		)
		return version.name

	def _fill_hierarchy(self, plan_version: str) -> None:
		pillar = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Pillar",
					"title": "Pillar",
					"display_order": 1,
				}
			).insert(ignore_permissions=True)
		)
		programme = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Programme",
					"title": "Programme",
					"display_order": 2,
					"parent_node_id": pillar.name,
				}
			).insert(ignore_permissions=True)
		)
		objective = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Strategic Objective",
					"title": "Objective",
					"display_order": 3,
					"parent_node_id": programme.name,
				}
			).insert(ignore_permissions=True)
		)
		indicator = self._track(
			frappe.get_doc(
				{
					"doctype": "Performance Indicator",
					"plan_version_id": plan_version,
					"measures_node_id": objective.name,
					"indicator_name": "Indicator",
					"definition": "Definition",
					"unit": "Percentage",
				}
			).insert(ignore_permissions=True)
		)
		self._track(
			frappe.get_doc(
				{
					"doctype": "Performance Target",
					"indicator_id": indicator.name,
					"financial_year_id": "FY-2027-2028",
					"comparison": "At least",
					"target_value": 80,
				}
			).insert(ignore_permissions=True)
		)

	def test_author_profile_grants_only_author_capability(self):
		author = self._user("author")
		self._grant(author, CAP_AUTHOR, PE_MOH)
		version = self._plan_and_version(PE_MOH)
		self._fill_hierarchy(version)

		frappe.set_user(author)
		self.assertEqual(available_actions(version, author), ["Submit for approval"])
		out = transition_plan_version(version, "Submit for approval")
		self.assertEqual(out["status"], "Submitted for approval")
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Approve")

	def test_unassigned_user_denied_stc_ac_004(self):
		outsider = self._user("outsider")
		version = self._plan_and_version(PE_MOH)
		self._fill_hierarchy(version)
		frappe.set_user(outsider)
		self.assertEqual(available_actions(version, outsider), [])
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Submit for approval")

	def test_administrator_without_assignment_has_no_workflow_capability(self):
		"""STR-CHG-001 §1.1/§19 — no Administrator fallback authority."""
		version = self._plan_and_version(PE_MOH)
		self._fill_hierarchy(version)
		frappe.set_user("Administrator")
		self.assertEqual(available_actions(version, "Administrator"), [])
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Submit for approval")

	def test_assignment_scoped_to_other_pe_denied_stc_br_001(self):
		author = self._user("author2")
		self._grant(author, CAP_AUTHOR, PE_CGKIS)
		version = self._plan_and_version(PE_MOH)
		self._fill_hierarchy(version)
		frappe.set_user(author)
		self.assertEqual(available_actions(version, author), [])
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Submit for approval")
