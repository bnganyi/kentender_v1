"""AUTH-G01 shared records and deny-by-default policy evidence."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.services.authorization_policy import (
	ALLOW,
	DENY_CAPABILITY,
	DENY_SCOPE,
	DENY_SOD,
	DENY_TASK,
	DENY_TASK_STATE,
	ResourceContext,
	evaluate_capability,
)


class TestAuthorizationGate01(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.user = self._user("actor")
		self.other = self._user("other")
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.profile = frappe.get_doc({"doctype": "Capability Profile", "profile_id": f"CAP-{self.suffix}", "profile_name": "Test Finance", "capabilities": json.dumps(["plan.finance.confirm", "plan.view"]), "allows_entity_wide": 1, "status": "Active", "effective_from": add_days(now_datetime(), -1), "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		self.assignment = frappe.get_doc({"doctype": "Operational Scope Assignment", "assignment_id": f"OSA-{self.suffix}", "user_id": self.user, "capability_profile_id": self.profile.name, "procuring_entity_id": self.pe, "effective_from": add_days(now_datetime(), -1), "status": "Active", "assigned_by": "Administrator", "assigned_at": now_datetime(), "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		self.ctx = ResourceContext("Procurement Plan Item", f"PPI-{self.suffix}", self.pe, "2027/28")

	def tearDown(self):
		for doctype in ("Workflow Task", "Authorization Delegation", "Separation of Duties Rule", "Operational Scope Assignment", "Capability Profile"):
			for name in frappe.get_all(doctype, filters=[["name", "like", f"%{self.suffix}%"]], pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.user, self.other):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"auth.g01.{label}.{self.suffix}@test.local"
		frappe.get_doc({"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}).insert(ignore_permissions=True)
		return email

	def _task(self, assignee=None, state="Open"):
		return frappe.get_doc({"doctype": "Workflow Task", "task_id": f"TSK-{self.suffix}", "task_iteration": 1, "module_name": "Procurement Planning", "task_type": "plan.finance.confirm", "subject_type": "Procuring Entity", "subject_id": self.pe, "procuring_entity_id": self.pe, "financial_year_id": "2027/28", "routing_rule_id": f"RTR-{self.suffix}", "routing_rule_version": 1, "assignee_type": "User", "assigned_user_id": assignee or self.user, "state": state, "created_by_actor": "Administrator", "created_at": now_datetime(), "concurrency_token": uuid4().hex, "idempotency_key": f"IDEM-{self.suffix}"}).insert(ignore_permissions=True)

	def test_capability_and_scope_are_both_required(self):
		allowed = evaluate_capability(self.user, "plan.finance.confirm", self.ctx)
		self.assertTrue(allowed.allowed)
		self.assertEqual(allowed.reason_code, ALLOW)
		missing = evaluate_capability(self.user, "plan.approve", self.ctx)
		self.assertFalse(missing.allowed)
		self.assertEqual(missing.reason_code, DENY_CAPABILITY)
		wrong_scope = evaluate_capability(self.user, "plan.finance.confirm", ResourceContext("Procurement Plan Item", "OTHER", "PE-NOT-ASSIGNED"))
		self.assertFalse(wrong_scope.allowed)
		self.assertEqual(wrong_scope.reason_code, DENY_SCOPE)

	def test_task_requires_current_exact_assignment(self):
		task = self._task()
		self.assertTrue(evaluate_capability(self.user, "plan.finance.confirm", self.ctx, task_id=task.name).allowed)
		wrong = evaluate_capability(self.other, "plan.finance.confirm", self.ctx, task_id=task.name)
		self.assertEqual(wrong.reason_code, DENY_CAPABILITY)
		self.assignment.user_id = self.other
		self.assignment.save(ignore_permissions=True)
		wrong = evaluate_capability(self.other, "plan.finance.confirm", self.ctx, task_id=task.name)
		self.assertEqual(wrong.reason_code, DENY_TASK)
		self.assignment.user_id = self.user
		self.assignment.save(ignore_permissions=True)
		task.state = "Completed"
		task.save(ignore_permissions=True)
		self.assertEqual(evaluate_capability(self.user, "plan.finance.confirm", self.ctx, task_id=task.name).reason_code, DENY_TASK_STATE)

	def test_resource_scope_is_enforced(self):
		self.assignment.resource_scope_type = "Procuring Entity"
		self.assignment.resource_scope_id = self.pe
		self.assignment.save(ignore_permissions=True)
		matching = ResourceContext("Procurement Plan Item", f"PPI-{self.suffix}", self.pe, resource_scope_type="Procuring Entity", resource_scope_id=self.pe)
		self.assertTrue(evaluate_capability(self.user, "plan.finance.confirm", matching).allowed)
		mismatch = ResourceContext("Procurement Plan Item", f"PPI-{self.suffix}", self.pe, resource_scope_type="Procuring Entity", resource_scope_id="OTHER")
		self.assertEqual(evaluate_capability(self.user, "plan.finance.confirm", mismatch).reason_code, DENY_SCOPE)

	def test_active_delegation_requires_scope_and_allows_assigned_task(self):
		task = self._task()
		frappe.get_doc({"doctype": "Authorization Delegation", "delegation_id": f"DEL-{self.suffix}", "delegator_user_id": self.user, "delegate_user_id": self.other, "capability_profile_id": self.profile.name, "procuring_entity_id": self.pe, "effective_from": add_days(now_datetime(), -1), "effective_to": add_days(now_datetime(), 1), "reason": "Coverage", "status": "Active", "approved_by": "Administrator", "approved_at": now_datetime(), "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		decision = evaluate_capability(self.other, "plan.finance.confirm", self.ctx, task_id=task.name)
		self.assertTrue(decision.allowed)
		self.assertTrue(decision.delegation_ids)

	def test_overlapping_active_assignment_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "Operational Scope Assignment", "assignment_id": f"OSA-DUP-{self.suffix}", "user_id": self.user, "capability_profile_id": self.profile.name, "procuring_entity_id": self.pe, "effective_from": now_datetime(), "status": "Active", "assigned_by": "Administrator", "assigned_at": now_datetime(), "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)

	def test_separation_of_duties_blocks_incompatible_second_action(self):
		frappe.get_doc({"doctype": "Separation of Duties Rule", "rule_id": f"SOD-{self.suffix}", "rule_name": "Finance versus approval", "first_capability": "plan.finance.confirm", "second_capability": "plan.view", "enforcement_level": "Workflow instance", "status": "Active", "effective_from": add_days(now_datetime(), -1)}).insert(ignore_permissions=True)
		ctx = ResourceContext("Procurement Plan Item", f"PPI-{self.suffix}", self.pe, prior_actions=[{"user": self.user, "capability": "plan.view"}])
		decision = evaluate_capability(self.user, "plan.finance.confirm", ctx)
		self.assertFalse(decision.allowed)
		self.assertEqual(decision.reason_code, DENY_SOD)

	def test_administrator_has_no_implicit_operational_capability(self):
		decision = evaluate_capability("Administrator", "plan.finance.confirm", self.ctx)
		self.assertFalse(decision.allowed)
		self.assertEqual(decision.reason_code, DENY_CAPABILITY)
