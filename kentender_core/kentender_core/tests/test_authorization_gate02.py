"""AUTH-G02 deterministic routing and atomic Workflow Task lifecycle evidence."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.services.workflow_routing import ASSIGNEE_NOT_AVAILABLE, ROUTING_AMBIGUOUS, ROUTING_NOT_CONFIGURED, RoutingContext, WorkflowRoutingError, resolve_routing
from kentender_core.services.workflow_tasks import TASK_ALREADY_CLAIMED, TASK_CONCURRENCY_CONFLICT, TASK_NOT_CURRENT, TASK_REASSIGNEE_NOT_ELIGIBLE, TaskSpec, WorkflowTaskError, claim_task, create_routed_task, execute_routed_transition, reassign_task, release_task, transition_task


class TestAuthorizationGate02(IntegrationTestCase):
	def setUp(self):
		self._remove_stale_gate02_fixtures()
		self.suffix = uuid4().hex[:8]
		self.user = self._user("actor")
		self.other = self._user("other")
		self.ineligible = self._user("ineligible")
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.profile = frappe.get_doc({"doctype": "Capability Profile", "profile_id": f"CAP-G02-{self.suffix}", "profile_name": "Gate 02", "capabilities": json.dumps(["plan.finance.confirm", "plan.view", "authorization.task.reassign"]), "allows_entity_wide": 1, "status": "Active", "effective_from": add_days(now_datetime(), -1), "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		for user in (self.user, self.other):
			frappe.get_doc({"doctype": "Operational Scope Assignment", "assignment_id": f"OSA-{user.split('@')[0]}-{self.suffix}", "user_id": user, "capability_profile_id": self.profile.name, "procuring_entity_id": self.pe, "effective_from": add_days(now_datetime(), -1), "status": "Active", "assigned_by": "Administrator", "assigned_at": now_datetime(), "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		self.context = RoutingContext("Procurement Planning", "plan.finance.confirm", self.pe, "2027/28")

	def _remove_stale_gate02_fixtures(self):
		users = frappe.get_all("Workflow Routing Rule", filters=[["assignee_user_id", "like", "auth.g02.%"]], pluck="name")
		queues = frappe.get_all("Workflow Queue", filters={"queue_name": "Gate 02 Queue"}, pluck="name")
		queue_rules = frappe.get_all("Workflow Routing Rule", filters={"queue_id": ["in", queues]}, pluck="name") if queues else []
		frappe.db.delete("Workflow Routing Rule", {"name": ["in", users + queue_rules]}) if users or queue_rules else None
		frappe.db.delete("Workflow Queue Membership", {"queue_id": ["in", queues]}) if queues else None
		frappe.db.delete("Workflow Queue", {"name": ["in", queues]}) if queues else None

	def tearDown(self):
		for doctype in ("Audit Event", "Workflow Task", "Workflow Routing Rule", "Workflow Queue Membership", "Workflow Queue", "Separation of Duties Rule", "Operational Scope Assignment", "Capability Profile"):
			filters = [["name", "like", f"%{self.suffix}%"]]
			if doctype == "Audit Event":
				filters = [["document_name", "like", f"%{self.suffix}%"]]
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.user, self.other, self.ineligible):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"auth.g02.{label}.{self.suffix}@test.local"
		frappe.get_doc({"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}).insert(ignore_permissions=True)
		return email

	def _rule(self, *, user=None, queue=None, priority=10, rule_id=None, status="Active", fallback=""):
		strategy = "Named claimable queue" if queue else "Named user"
		return frappe.get_doc({"doctype": "Workflow Routing Rule", "routing_version_id": f"RTV-G02-{self.suffix}-{uuid4().hex[:6]}", "routing_rule_id": rule_id or f"RTR-G02-{self.suffix}-{uuid4().hex[:6]}", "version": 1, "module_name": self.context.module_name, "task_type": self.context.task_type, "procuring_entity_id": self.pe, "required_capability": "plan.finance.confirm", "assignee_strategy": strategy, "assignee_user_id": user, "queue_id": queue, "priority": priority, "effective_from": add_days(now_datetime(), -1), "fallback_rule_id": fallback, "status": status, "approved_by": "Administrator" if status == "Active" else None, "approved_at": now_datetime() if status == "Active" else None}).insert(ignore_permissions=True)

	def _queue(self):
		queue = frappe.get_doc({"doctype": "Workflow Queue", "queue_id": f"QUE-{self.suffix}", "queue_name": "Gate 02 Queue", "module_name": self.context.module_name, "required_capability": "plan.finance.confirm", "procuring_entity_id": self.pe, "status": "Active", "effective_from": add_days(now_datetime(), -1), "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		for user in (self.user, self.other):
			frappe.get_doc({"doctype": "Workflow Queue Membership", "membership_id": f"QMB-G02-{self.suffix}-{uuid4().hex[:6]}", "queue_id": queue.name, "user_id": user, "effective_from": add_days(now_datetime(), -1), "status": "Active", "concurrency_token": uuid4().hex}).insert(ignore_permissions=True)
		return queue

	def _spec(self, key=None):
		return TaskSpec(self.context, "Procuring Entity", self.pe, key or f"IDEM-{self.suffix}", task_id=f"TSK-{self.suffix}-{uuid4().hex[:6]}")

	def test_named_user_route_creates_complete_idempotent_task(self):
		rule = self._rule(user=self.user)
		route = resolve_routing(self.context)
		self.assertEqual(route.routing_rule_id, rule.routing_rule_id)
		spec = self._spec()
		first = create_routed_task(spec, actor="Administrator")
		frappe.db.set_value("Workflow Routing Rule", rule.name, "status", "Ended", update_modified=False)
		second = create_routed_task(spec, actor="Administrator")
		self.assertEqual(first.name, second.name)
		self.assertEqual(first.assigned_user_id, self.user)
		self.assertEqual(first.routing_rule_version, 1)

	def test_missing_ambiguous_and_ineligible_routes_have_stable_failures(self):
		with self.assertRaises(WorkflowRoutingError) as missing:
			resolve_routing(self.context)
		self.assertEqual(missing.exception.code, ROUTING_NOT_CONFIGURED)
		first = self._rule(user=self.user, priority=10)
		second = self._rule(user=self.other, priority=20)
		frappe.db.set_value("Workflow Routing Rule", second.name, "priority", 10, update_modified=False)
		with self.assertRaises(WorkflowRoutingError) as ambiguous:
			resolve_routing(self.context)
		self.assertEqual(ambiguous.exception.code, ROUTING_AMBIGUOUS)
		frappe.db.set_value("Workflow Routing Rule", first.name, "status", "Ended", update_modified=False)
		frappe.db.set_value("Workflow Routing Rule", second.name, {"priority": 20, "assignee_user_id": self.ineligible}, update_modified=False)
		with self.assertRaises(WorkflowRoutingError) as unavailable:
			resolve_routing(self.context)
		self.assertEqual(unavailable.exception.code, ASSIGNEE_NOT_AVAILABLE)

	def test_explicit_fallback_only_is_used_when_primary_is_ineligible(self):
		fallback = self._rule(user=self.other, priority=20)
		self._rule(user=self.ineligible, priority=10, fallback=fallback.routing_rule_id)
		self.assertEqual(resolve_routing(self.context).assigned_user_id, self.other)

	def test_routing_failure_occurs_before_business_transition(self):
		called = []
		with self.assertRaises(WorkflowRoutingError):
			execute_routed_transition(self._spec(), lambda: called.append(True))
		self.assertEqual(called, [])

	def test_queue_claim_has_one_winner_and_stale_token_is_rejected(self):
		queue = self._queue()
		self._rule(queue=queue.name)
		task = create_routed_task(self._spec(), actor="Administrator")
		original = task.concurrency_token
		claimed = claim_task(task.name, user=self.user, expected_token=original)
		with self.assertRaises(WorkflowTaskError) as stale:
			claim_task(task.name, user=self.other, expected_token=original)
		self.assertEqual(stale.exception.code, TASK_CONCURRENCY_CONFLICT)
		with self.assertRaises(WorkflowTaskError) as owned:
			claim_task(task.name, user=self.other, expected_token=claimed.concurrency_token)
		self.assertEqual(owned.exception.code, TASK_ALREADY_CLAIMED)
		released = release_task(task.name, user=self.user, expected_token=claimed.concurrency_token, reason="Return to queue")
		self.assertFalse(released.claimed_by)

	def test_reassignment_requires_authorized_actor_and_eligible_target(self):
		self._rule(user=self.user)
		task = create_routed_task(self._spec(), actor="Administrator")
		reassigned = reassign_task(task.name, actor=self.user, new_user=self.other, expected_token=task.concurrency_token, reason="Coverage")
		self.assertEqual(reassigned.assigned_user_id, self.other)
		frappe.get_doc({"doctype": "Separation of Duties Rule", "rule_id": f"SOD-G02-{self.suffix}", "rule_name": "View versus finance", "first_capability": "plan.view", "second_capability": "plan.finance.confirm", "enforcement_level": "Workflow instance", "status": "Active", "effective_from": add_days(now_datetime(), -1)}).insert(ignore_permissions=True)
		with self.assertRaises(WorkflowTaskError) as sod:
			reassign_task(task.name, actor=self.user, new_user=self.other, expected_token=reassigned.concurrency_token, reason="SoD", prior_actions=[{"user": self.other, "capability": "plan.view"}])
		self.assertEqual(sod.exception.code, TASK_REASSIGNEE_NOT_ELIGIBLE)
		with self.assertRaises(WorkflowTaskError) as invalid:
			reassign_task(task.name, actor=self.user, new_user=self.ineligible, expected_token=reassigned.concurrency_token, reason="Invalid")
		self.assertEqual(invalid.exception.code, TASK_REASSIGNEE_NOT_ELIGIBLE)

	def test_terminal_transition_invalidates_task_immediately(self):
		self._rule(user=self.user)
		task = create_routed_task(self._spec(), actor="Administrator")
		completed = transition_task(task.name, actor=self.user, capability="plan.finance.confirm", target_state="Completed", expected_token=task.concurrency_token)
		self.assertEqual(completed.state, "Completed")
		with self.assertRaises(WorkflowTaskError) as stale:
			transition_task(task.name, actor=self.user, capability="plan.finance.confirm", target_state="Returned", expected_token=completed.concurrency_token)
		self.assertEqual(stale.exception.code, TASK_NOT_CURRENT)
