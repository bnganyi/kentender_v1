"""Gate 05 evidence for canonical Planning task authorization."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_procurement.procurement_planning.services.planning_tasks import (
	authorize_planning_task,
	create_governed_planning_task,
	planning_task_action_allowed,
	transition_planning_task,
)


class TestPlanningAuthorizationGate05(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:10].upper()
		self.pe = frappe.db.get_value("Procuring Entity", {}, "name")
		if not self.pe:
			self.skipTest("A Procuring Entity is required for authorization integration tests")
		self.subject = frappe.db.get_value("Procurement Plan Version", {}, "name")
		if not self.subject:
			self.skipTest("A Procurement Plan Version is required for authorization integration tests")
		self.user = self._user("actor")
		self.other = self._user("other")
		self.profile = self._profile(
			["plan.review", "plan.recommend", "plan.return", "plan.approve"]
		)
		self._assignment(self.user, self.profile)

	def tearDown(self):
		frappe.db.delete("Audit Event", {"performed_by": ["in", [self.user, self.other, "Administrator"]]})
		for doctype in (
			"Workflow Task",
			"Workflow Routing Rule",
			"Separation of Duties Rule",
			"Operational Scope Assignment",
			"Capability Profile",
		):
			field = "name"
			for name in frappe.get_all(
				doctype,
				filters=[[field, "like", f"%{self.suffix}%"]],
				pluck="name",
			):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.user, self.other):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.rollback()

	def _user(self, label: str) -> str:
		email = f"g05-{label}-{self.suffix.lower()}@example.test"
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": f"Gate05 {label}",
				"enabled": 1,
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		return email

	def _profile(self, capabilities: list[str]) -> str:
		profile = frappe.get_doc(
			{
				"doctype": "Capability Profile",
				"profile_id": f"CP-G05-{self.suffix}",
				"profile_name": f"Planning Gate 05 {self.suffix}",
				"capabilities": json.dumps(capabilities),
				"allows_entity_wide": 1,
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
			}
		).insert(ignore_permissions=True)
		return profile.name

	def _assignment(self, user: str, profile: str) -> None:
		frappe.get_doc(
			{
				"doctype": "Operational Scope Assignment",
				"assignment_id": f"OSA-G05-{self.suffix}",
				"user_id": user,
				"capability_profile_id": profile,
				"procuring_entity_id": self.pe,
				"include_descendants": 1,
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
				"assigned_by": "Administrator",
				"assigned_at": now_datetime(),
			}
		).insert(ignore_permissions=True)

	def _rule(self, task_type: str, capability: str) -> None:
		code = task_type.replace(".", "-").upper()
		frappe.get_doc(
			{
				"doctype": "Workflow Routing Rule",
				"routing_version_id": f"RTV-G05-{code}-{self.suffix}",
				"routing_rule_id": f"RTR-G05-{code}-{self.suffix}",
				"version": 1,
				"module_name": "Procurement Planning",
				"task_type": task_type,
				"procuring_entity_id": self.pe,
				"required_capability": capability,
				"assignee_strategy": "Named user",
				"assignee_user_id": self.user,
				"priority": 10,
				"effective_from": add_days(now_datetime(), -1),
				"status": "Active",
				"approved_by": "Administrator",
				"approved_at": now_datetime(),
			}
		).insert(ignore_permissions=True)

	def _task(self, task_type: str, capability: str):
		self._rule(task_type, capability)
		record = frappe._dict(
			name=self.subject,
			version_code=f"VER-G05-{self.suffix}",
			review_task_iteration=0,
		)
		return create_governed_planning_task(
			prefix="PLN-G05",
			record=record,
			id_field="review_task_id",
			iteration_field="review_task_iteration",
			task_type=task_type,
			subject_type="Procurement Plan Version",
			subject_id=self.subject,
			procuring_entity=self.pe,
			financial_year="2027/28",
			idempotency_key=f"g05:{task_type}:{self.suffix}",
			actor="Administrator",
		)[0]

	def test_current_assignment_controls_loader_action_and_stale_task(self):
		task = self._task("plan.review", "plan.review")
		loaded = authorize_planning_task(
			task_id=task.name,
			actor=self.user,
			capability="plan.review",
			subject_type="Procurement Plan Version",
			subject_id=task.subject_id,
		)
		self.assertEqual(loaded.name, task.name)
		self.assertTrue(
			planning_task_action_allowed(
				task_id=task.name, actor=self.user, capability="plan.approve"
			)
		)
		for unauthorized in (self.other, "Administrator"):
			with self.assertRaises(frappe.PermissionError):
				authorize_planning_task(
					task_id=task.name,
					actor=unauthorized,
					capability="plan.review",
					subject_type="Procurement Plan Version",
				)
		with self.assertRaises(frappe.PermissionError):
			authorize_planning_task(
				task_id=task.name,
				actor=self.user,
				capability="plan.review",
				subject_type="Procurement Plan Item Version",
			)
		transition_planning_task(
			task_id=task.name,
			actor=self.user,
			capability="plan.review",
			target_state="Completed",
			expected_token=task.concurrency_token,
		)
		self.assertFalse(
			planning_task_action_allowed(
				task_id=task.name, actor=self.user, capability="plan.approve"
			)
		)

	def test_sod_blocks_incompatible_current_task_decision(self):
		task = self._task("plan.approve", "plan.approve")
		frappe.get_doc(
			{
				"doctype": "Separation of Duties Rule",
				"rule_id": f"SOD-G05-{self.suffix}",
				"rule_name": f"Recommendation versus approval {self.suffix}",
				"first_capability": "plan.recommend",
				"second_capability": "plan.approve",
				"enforcement_level": "Workflow instance",
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			transition_planning_task(
				task_id=task.name,
				actor=self.user,
				capability="plan.approve",
				target_state="Completed",
				expected_token=task.concurrency_token,
				prior_actions=[{"user": self.user, "capability": "plan.recommend"}],
			)
		self.assertEqual(frappe.db.get_value("Workflow Task", task.name, "state"), "Open")
