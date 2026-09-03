# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 Phase 3 roles/permissions, reworked for AUTH-ADR-001
v1.6 (CU-301/CU-308): authority is an Enabled Site-wide User Responsibility
Assignment resolved by `kentender_core.services.authorization` — no
capability map, no User Permission scope, no Procuring Entity dimension.

Covers STR-BR-001-004 and STR-AC-003, 004, 010, 021, 022 at the service
layer. Denials surface as the closed §10 vocabulary
(`ResponsibilityError`), not `frappe.PermissionError`.

This runner has no per-test rollback: every record this suite creates is
tracked and deleted in tearDown, and grants flow through the real
administration command so the Role projection is created and removed the
production way.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services import responsibility_administration as administration
from kentender_core.services.business_role_registry import REGISTRY, SCOPE_SITE
from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_strategy.services.strategy_authorization import (
	ROLE_STRATEGY_APPROVER,
	ROLE_STRATEGY_AUTHOR,
	ensure_strategy_governance_roles,
)
from kentender_strategy.services.strategy_transitions import available_actions, transition_plan_version

FIXTURE_NS = "STR_CU3XX_TESTS"


class TestGovernanceSeed(FrappeTestCase):
	def test_roles_exist_and_registry_binds_them_site_wide(self):
		ensure_strategy_governance_roles()
		second_run = ensure_strategy_governance_roles()
		self.assertEqual(second_run, {"roles": [], "sod_rules": []})

		for role in (ROLE_STRATEGY_AUTHOR, ROLE_STRATEGY_APPROVER):
			self.assertTrue(frappe.db.exists("Role", role))
			# v1.6 — the business role is registered Site-wide and projects
			# its same-named Frappe Role.
			entry = REGISTRY[role]
			self.assertEqual(entry.scope_type, SCOPE_SITE)
			self.assertIn(role, entry.frappe_roles)


class TestGovernanceEnforcement(FrappeTestCase):
	"""Grants through the real v1.6 administration command; the transition
	service must honour exactly the granted responsibility and nothing else."""

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
		email = f"kt.test.str.gov.{label}.{self.suffix}@test.local"
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": label,
				"enabled": 1,
				"send_welcome_email": 0,
				# v1.6 §4.2 — only a System User can hold a responsibility;
				# Frappe flips a role-less user back to Website User on save,
				# so Desk User is always added (same as core's v16 fixtures).
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
		self._track(doc)
		return email

	def _grant(self, user: str, business_role: str) -> None:
		outcome = administration.grant(
			user=user,
			business_role=business_role,
			organisation_unit="",
			fixture_namespace=FIXTURE_NS,
			actor="Administrator",
		)
		self._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))

	def _plan_and_version(self) -> str:
		plan = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan",
					"title": f"Governance Test Plan {self.suffix}",
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
					# CU-305 — targets bind the canonical ERPNext Fiscal Year.
					"financial_year_id": "2027-2028",
					"comparison": "At least",
					"target_value": 80,
				}
			).insert(ignore_permissions=True)
		)

	def test_author_assignment_grants_only_author_capability(self):
		author = self._user("author")
		self._grant(author, ROLE_STRATEGY_AUTHOR)
		version = self._plan_and_version()
		self._fill_hierarchy(version)

		frappe.set_user(author)
		self.assertEqual(available_actions(version, author), ["Submit for approval"])
		out = transition_plan_version(version, "Submit for approval")
		self.assertEqual(out["status"], "Submitted for approval")
		with self.assertRaises(ResponsibilityError):
			transition_plan_version(version, "Approve")

	def test_unassigned_user_denied_stc_ac_004(self):
		outsider = self._user("outsider")
		version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(outsider)
		self.assertEqual(available_actions(version, outsider), [])
		with self.assertRaises(ResponsibilityError):
			transition_plan_version(version, "Submit for approval")

	def test_administrator_without_assignment_has_no_workflow_capability(self):
		"""STR-CHG-001 §1.1/§19 + AUTH-AC-018 — no technical fallback authority."""
		version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user("Administrator")
		self.assertEqual(available_actions(version, "Administrator"), [])
		with self.assertRaises(ResponsibilityError):
			transition_plan_version(version, "Submit for approval")

	def test_approver_assignment_does_not_author(self):
		"""v1.6 replacement for the retired cross-PE denial (the PE dimension
		is gone): holding the *other* strategy responsibility never authors."""
		approver = self._user("approver")
		self._grant(approver, ROLE_STRATEGY_APPROVER)
		version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(approver)
		self.assertEqual(available_actions(version, approver), [])
		with self.assertRaises(ResponsibilityError):
			transition_plan_version(version, "Submit for approval")
