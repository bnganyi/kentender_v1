# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 Phase 2 — plan version lifecycle engine.

Covers STR-BR-004, 006, 015-017 and STR-AC-008, 010-015 against the v1.5
2-role/4-status model: Strategy Author submits; Strategy Approver returns
or approves (approve activates in the same transaction, superseding the
plan's previous Active version). Separation of duties is the direct
same-version self-check ("the author cannot approve or return the same
version, even if they also hold Strategy Approver") — not a capability-pair
Separation of Duties Rule table any more (Phase 3 seeds no such rule for
Strategy under v1.5)."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services.authorization_role_registry import CAPABILITY_ROLE_MAP
from kentender_strategy.services.strategy_authorization import CAP_APPROVE, CAP_AUTHOR
from kentender_strategy.services.strategy_transitions import available_actions, transition_plan_version

PE = "PE-MOH"
FY = "FY-2027-2028"


class TestPlanVersionLifecycle(FrappeTestCase):
	def setUp(self):
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
		email = f"str.lifecycle.{label}.{self.suffix}@test.local"
		self._track(
			frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		)
		return email

	def _actor(self, label: str, capabilities: list[str]) -> str:
		user = self._user(label)
		for capability in capabilities:
			role = CAPABILITY_ROLE_MAP[capability]
			if not frappe.db.exists("Role", role):
				frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)
			frappe.get_doc("User", user).add_roles(role)
		self._track(
			frappe.get_doc(
				{"doctype": "User Permission", "user": user, "allow": "Procuring Entity", "for_value": PE}
			).insert(ignore_permissions=True)
		)
		return user

	def _plan_and_version(self, **version_kwargs) -> tuple[str, str]:
		plan = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan",
					"title": f"Lifecycle Test Plan {self.suffix}",
					"procuring_entity_id": PE,
					"plan_role": version_kwargs.pop("plan_role", "Primary"),
					"period_start": "2040-07-01",
					"period_end": "2045-06-30",
				}
			).insert(ignore_permissions=True)
		)
		data = {
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": "2040-07-01",
			"effective_to": "2045-06-30",
		}
		data.update(version_kwargs)
		version = self._track(frappe.get_doc(data).insert(ignore_permissions=True))
		return plan.name, version.name

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
					"financial_year_id": FY,
					"comparison": "At least",
					"target_value": 80,
				}
			).insert(ignore_permissions=True)
		)

	def test_full_lifecycle_happy_path_with_distinct_actors(self):
		author = self._actor("author", [CAP_AUTHOR])
		approver = self._actor("approver", [CAP_APPROVE])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)

		frappe.set_user(author)
		self.assertEqual(available_actions(version, author), ["Submit for approval"])
		out = transition_plan_version(version, "Submit for approval")
		self.assertEqual(out["status"], "Submitted for approval")

		frappe.set_user(approver)
		self.assertCountEqual(available_actions(version, approver), ["Return", "Approve"])
		out = transition_plan_version(version, "Approve")
		self.assertEqual(out["status"], "Active")
		self.assertEqual(available_actions(version, approver), [])

	def test_return_reason_length_enforced(self):
		approver = self._actor("approver2", [CAP_APPROVE])
		author = self._actor("author2", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(author)
		transition_plan_version(version, "Submit for approval")

		frappe.set_user(approver)
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(version, "Return", reason="too short")
		out = transition_plan_version(version, "Return", reason="A properly detailed return reason.")
		self.assertEqual(out["status"], "Draft")

		frappe.set_user(author)
		self.assertEqual(available_actions(version, author), ["Submit for approval"])

	def test_submit_blocked_when_not_ready(self):
		author = self._actor("author3", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		frappe.set_user(author)
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(version, "Submit for approval")

	def test_author_cannot_return_or_approve_own_version_even_with_approver_role(self):
		"""§6.2/§13.4/§18.1: same-version self-check, not a capability-pair
		rule — a dual-role actor is blocked only on the version they
		themselves submitted."""
		dual = self._actor("dual", [CAP_AUTHOR, CAP_APPROVE])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(dual)
		transition_plan_version(version, "Submit for approval")
		self.assertCountEqual(available_actions(version, dual), [])
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Approve")
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Return", reason="A properly detailed return reason.")

	def test_dual_role_actor_may_approve_a_version_someone_else_submitted(self):
		dual = self._actor("dual2", [CAP_AUTHOR, CAP_APPROVE])
		author = self._actor("author4b", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(author)
		transition_plan_version(version, "Submit for approval")
		frappe.set_user(dual)
		out = transition_plan_version(version, "Approve")
		self.assertEqual(out["status"], "Active")

	def test_stale_write_rejected(self):
		author = self._actor("author4", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(author)
		stale_token = str(frappe.db.get_value("Strategic Plan Version", version, "modified"))
		# Any subsequent save (even unrelated) moves `modified` forward.
		frappe.db.set_value("Strategic Plan Version", version, "return_reason", "")
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(version, "Submit for approval", expected_version=stale_token)

	def test_invalid_transition_rejected(self):
		author = self._actor("author5", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		frappe.set_user(author)
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(version, "Approve")

	def test_activate_supersedes_previous_active_version_of_same_plan(self):
		approver = self._actor("approver2", [CAP_APPROVE])
		plan, v1 = self._plan_and_version()
		v1_doc = frappe.get_doc("Strategic Plan Version", v1)
		v1_doc.status = "Active"
		v1_doc.save(ignore_permissions=True)
		v2 = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan Version",
					"plan_id": plan,
					"version_number": 2,
					"based_on_plan_version_id": v1,
					"effective_from": "2040-07-01",
					"effective_to": "2045-06-30",
					"status": "Submitted for approval",
				}
			).insert(ignore_permissions=True)
		)
		frappe.set_user(approver)
		out = transition_plan_version(v2.name, "Approve")
		self.assertEqual(out["status"], "Active")
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", v1, "status"), "Superseded")

	def test_activate_rejects_overlapping_primary_plan(self):
		approver = self._actor("approver3", [CAP_APPROVE])
		_, v1 = self._plan_and_version(plan_role="Primary")
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")
		_, v2 = self._plan_and_version(plan_role="Primary", status="Submitted for approval")
		frappe.set_user(approver)
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(v2, "Approve")
