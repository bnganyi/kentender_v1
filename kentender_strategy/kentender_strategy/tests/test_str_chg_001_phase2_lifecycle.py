# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 2 — plan version lifecycle engine.

Covers STR-BR-004, 006, 015-017 and STR-AC-008, 010-015. Capability Profiles/
Operational Scope Assignments/Separation of Duties Rules are self-contained
test fixtures (Phase 3 seeds the production versions of these for real
Strategy Author/Reviewer/Approval Authority actors) — same pattern as
kentender_core's own CFG-CHG-002 lifecycle tests.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from kentender_strategy.services.strategy_authorization import CAP_APPROVE, CAP_AUTHOR, CAP_REVIEW
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

	def _profile(self, label: str, capabilities: list[str]) -> str:
		doc = self._track(
			frappe.get_doc(
				{
					"doctype": "Capability Profile",
					"profile_id": f"CAP-STR-{label}-{self.suffix}",
					"profile_name": f"Test Strategy {label}",
					"capabilities": json.dumps(capabilities),
					"allows_entity_wide": 1,
					"status": "Active",
					"concurrency_token": uuid4().hex,
				}
			).insert(ignore_permissions=True)
		)
		return doc.name

	def _assign(self, user: str, profile: str) -> str:
		doc = self._track(
			frappe.get_doc(
				{
					"doctype": "Operational Scope Assignment",
					"assignment_id": f"OSA-STR-{uuid4().hex[:10]}-{self.suffix}",
					"user_id": user,
					"capability_profile_id": profile,
					"procuring_entity_id": PE,
					"effective_from": add_days(now_datetime(), -1),
					"status": "Active",
					"assigned_by": "Administrator",
					"assigned_at": now_datetime(),
					"concurrency_token": uuid4().hex,
				}
			).insert(ignore_permissions=True)
		)
		return doc.name

	def _sod_rule(self, first: str, second: str) -> str:
		doc = self._track(
			frappe.get_doc(
				{
					"doctype": "Separation of Duties Rule",
					"rule_id": f"SOD-STR-{uuid4().hex[:8]}-{self.suffix}",
					"rule_name": f"Test {first} vs {second}",
					"first_capability": first,
					"second_capability": second,
					"enforcement_level": "Workflow instance",
					"status": "Active",
					"effective_from": add_days(now_datetime(), -1),
				}
			).insert(ignore_permissions=True)
		)
		return doc.name

	def _actor(self, label: str, capabilities: list[str]) -> str:
		user = self._user(label)
		profile = self._profile(label, capabilities)
		self._assign(user, profile)
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
		reviewer = self._actor("reviewer", [CAP_REVIEW])
		approver = self._actor("approver", [CAP_APPROVE])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)

		frappe.set_user(author)
		self.assertEqual(available_actions(version, author), ["Submit for review"])
		out = transition_plan_version(version, "Submit for review")
		self.assertEqual(out["status"], "In Review")

		frappe.set_user(reviewer)
		self.assertCountEqual(available_actions(version, reviewer), ["Return", "Recommend for approval"])
		out = transition_plan_version(version, "Recommend for approval")
		self.assertEqual(out["status"], "Awaiting Approval")

		frappe.set_user(approver)
		self.assertCountEqual(available_actions(version, approver), ["Return", "Approve"])
		out = transition_plan_version(version, "Approve")
		self.assertEqual(out["status"], "Approved")

		out = transition_plan_version(version, "Activate")
		self.assertEqual(out["status"], "Active")
		self.assertEqual(available_actions(version, approver), [])

	def test_return_reason_length_enforced(self):
		reviewer = self._actor("reviewer2", [CAP_REVIEW])
		author = self._actor("author2", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(author)
		transition_plan_version(version, "Submit for review")

		frappe.set_user(reviewer)
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(version, "Return", reason="too short")
		out = transition_plan_version(version, "Return", reason="A properly detailed return reason.")
		self.assertEqual(out["status"], "Returned")

		frappe.set_user(author)
		self.assertEqual(available_actions(version, author), ["Revise"])
		out = transition_plan_version(version, "Revise")
		self.assertEqual(out["status"], "Draft")

	def test_submit_blocked_when_not_ready(self):
		author = self._actor("author3", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		frappe.set_user(author)
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(version, "Submit for review")

	def test_reviewer_cannot_recommend_own_submission(self):
		dual = self._actor("dual", [CAP_AUTHOR, CAP_REVIEW])
		self._sod_rule(CAP_AUTHOR, CAP_REVIEW)
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(dual)
		transition_plan_version(version, "Submit for review")
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Recommend for approval")

	def test_author_cannot_approve_own_version(self):
		dual = self._actor("dual2", [CAP_AUTHOR, CAP_APPROVE])
		reviewer = self._actor("reviewer3", [CAP_REVIEW])
		self._sod_rule(CAP_AUTHOR, CAP_APPROVE)
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(dual)
		transition_plan_version(version, "Submit for review")
		frappe.set_user(reviewer)
		transition_plan_version(version, "Recommend for approval")
		frappe.set_user(dual)
		with self.assertRaises(frappe.PermissionError):
			transition_plan_version(version, "Approve")

	def test_stale_write_rejected(self):
		author = self._actor("author4", [CAP_AUTHOR])
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(author)
		stale_token = str(frappe.db.get_value("Strategic Plan Version", version, "modified"))
		# Any subsequent save (even unrelated) moves `modified` forward.
		frappe.db.set_value("Strategic Plan Version", version, "return_reason", "")
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(version, "Submit for review", expected_version=stale_token)

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
					"status": "Approved",
				}
			).insert(ignore_permissions=True)
		)
		frappe.set_user(approver)
		out = transition_plan_version(v2.name, "Activate")
		self.assertEqual(out["status"], "Active")
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", v1, "status"), "Superseded")

	def test_activate_rejects_overlapping_primary_plan(self):
		approver = self._actor("approver3", [CAP_APPROVE])
		_, v1 = self._plan_and_version(plan_role="Primary")
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")
		_, v2 = self._plan_and_version(plan_role="Primary", status="Approved")
		frappe.set_user(approver)
		with self.assertRaises(frappe.ValidationError):
			transition_plan_version(v2, "Activate")
