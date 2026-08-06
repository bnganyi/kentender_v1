# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""XMOD-STR-009 — Strategy workflow Notification Log."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_notification_service import (
	EVENT_CA_ASSIGNED,
	EVENT_MEASUREMENT_SUBMITTED,
	EVENT_MEASUREMENT_VERIFIED,
	EVENT_PLAN_RETURNED,
	EVENT_PLAN_SUBMITTED,
	notify_strategy_users,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import transition_measurement
from kentender_strategy.services.strategy_writes import save_measurement_draft


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
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
		"Performance Officer",
		"Performance Verifier",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
		if not frappe.db.exists(
			"User Permission",
			{"user": email, "allow": "Procuring Entity", "for_value": procuring_entity},
		):
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": email,
					"allow": "Procuring Entity",
					"for_value": procuring_entity,
					"is_default": 1,
				}
			).insert(ignore_permissions=True)
	return email


def _cleanup_measurement(name: str | None) -> None:
	if not name or not frappe.db.exists("Performance Measurement", name):
		return
	for ca in frappe.get_all(
		"Strategy Corrective Action",
		filters={"performance_measurement": name},
		pluck="name",
	):
		frappe.delete_doc("Strategy Corrective Action", ca, force=True, ignore_permissions=True)
	frappe.delete_doc("Performance Measurement", name, force=True, ignore_permissions=True)


class TestStrategyNotifications(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan_id = cls.seed["plan"]
		cls.target_id = cls.seed["target"]
		if cls.plan_id:
			status = frappe.db.get_value("Strategic Plan", cls.plan_id, "status")
			if status != "Active":
				frappe.db.set_value("Strategic Plan", cls.plan_id, "status", "Active")
		cls.reviewer = _ensure_user(
			"str.notify.reviewer@example.com", ["Strategy Reviewer"], cls.pe
		)
		cls.planning = _ensure_user(
			"str.notify.planning@example.com", ["Planning Authority"], cls.pe
		)
		cls.manager = _ensure_user(
			"str.notify.manager@example.com", ["Strategy Manager"], cls.pe
		)
		cls.officer = _ensure_user(
			"str.notify.officer@example.com", ["Performance Officer"], cls.pe
		)
		cls.verifier = _ensure_user(
			"str.notify.verifier@example.com", ["Performance Verifier"], cls.pe
		)

	def setUp(self):
		for name in frappe.get_all(
			"Notification Log",
			filters={"email_header": ["like", "kt-strategy:%"]},
			pluck="name",
		):
			frappe.delete_doc("Notification Log", name, force=True, ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _count_event(self, event_type: str, for_user: str | None = None) -> int:
		filters = {"email_header": ["like", f"kt-strategy:{event_type}:%"]}
		if for_user:
			filters["for_user"] = for_user
		return frappe.db.count("Notification Log", filters)

	def test_plan_submit_notifies_reviewer_and_planning(self):
		plan = frappe.get_doc("Strategic Plan", self.plan_id)
		notify_strategy_users(
			EVENT_PLAN_SUBMITTED,
			document_type="Strategic Plan",
			document_name=plan.name,
			procuring_entity=self.pe,
			plan_code=plan.plan_code,
			submitted_by=self.manager,
			label=plan.plan_code,
			correlation_suffix="test-submit",
		)
		self.assertGreaterEqual(self._count_event(EVENT_PLAN_SUBMITTED, self.reviewer), 1)
		self.assertGreaterEqual(self._count_event(EVENT_PLAN_SUBMITTED, self.planning), 1)

	def test_plan_submit_idempotent(self):
		plan = frappe.get_doc("Strategic Plan", self.plan_id)
		kwargs = dict(
			document_type="Strategic Plan",
			document_name=plan.name,
			procuring_entity=self.pe,
			plan_code=plan.plan_code,
			submitted_by=self.manager,
			label=plan.plan_code,
			correlation_suffix="idempotent-submit",
		)
		first = notify_strategy_users(EVENT_PLAN_SUBMITTED, **kwargs)
		second = notify_strategy_users(EVENT_PLAN_SUBMITTED, **kwargs)
		self.assertTrue(first)
		self.assertEqual(first, second)
		self.assertEqual(self._count_event(EVENT_PLAN_SUBMITTED, self.reviewer), 1)

	def test_plan_return_notifies_submitter(self):
		plan = frappe.get_doc("Strategic Plan", self.plan_id)
		notify_strategy_users(
			EVENT_PLAN_RETURNED,
			document_type="Strategic Plan",
			document_name=plan.name,
			procuring_entity=self.pe,
			plan_code=plan.plan_code,
			submitted_by=self.manager,
			label=plan.plan_code,
			correlation_suffix="test-return",
		)
		self.assertGreaterEqual(self._count_event(EVENT_PLAN_RETURNED, self.manager), 1)

	def test_measurement_submit_and_verify_notify(self):
		frappe.set_user(self.officer)
		saved = save_measurement_draft(
			{
				"performance_target": self.target_id,
				"plan_version": self.plan_id,
				"measurement_period_start": "2028-01-01",
				"measurement_period_end": "2028-01-31",
				"measurement_date": "2028-01-31",
				"actual_numeric": 99.95,
				"evidence_source": "Notify test",
				"evidence_reference": "NOTIFY-MEAS",
			}
		)
		mid = saved["id"]
		self.addCleanup(lambda: _cleanup_measurement(mid))
		tr = transition_measurement(mid, "Submit")
		self.assertEqual(tr["workflow_status"], "Submitted")
		self.assertGreaterEqual(
			self._count_event(EVENT_MEASUREMENT_SUBMITTED, self.verifier), 1
		)

		frappe.set_user(self.verifier)
		transition_measurement(mid, "Verify")
		self.assertGreaterEqual(
			self._count_event(EVENT_MEASUREMENT_VERIFIED, self.officer), 1
		)

	def test_off_track_verify_assigns_ca_notification(self):
		frappe.set_user(self.officer)
		saved = save_measurement_draft(
			{
				"performance_target": self.target_id,
				"plan_version": self.plan_id,
				"measurement_period_start": "2028-02-01",
				"measurement_period_end": "2028-02-28",
				"measurement_date": "2028-02-28",
				"actual_numeric": 10.0,
				"evidence_source": "Notify CA test",
				"evidence_reference": "NOTIFY-CA",
			}
		)
		mid = saved["id"]
		self.addCleanup(lambda: _cleanup_measurement(mid))
		transition_measurement(mid, "Submit")
		frappe.set_user(self.verifier)
		transition_measurement(mid, "Verify")
		self.assertGreaterEqual(self._count_event(EVENT_CA_ASSIGNED, self.officer), 1)

	def test_notify_failure_does_not_break_transition(self):
		frappe.set_user(self.officer)
		saved = save_measurement_draft(
			{
				"performance_target": self.target_id,
				"plan_version": self.plan_id,
				"measurement_period_start": "2028-03-01",
				"measurement_period_end": "2028-03-31",
				"measurement_date": "2028-03-31",
				"actual_numeric": 99.9,
				"evidence_source": "Notify isolate",
				"evidence_reference": "NOTIFY-ISO",
			}
		)
		mid = saved["id"]
		self.addCleanup(lambda: _cleanup_measurement(mid))
		with patch(
			"kentender_strategy.services.strategy_notification_service.emit_notification_log",
			side_effect=RuntimeError("boom"),
		):
			tr = transition_measurement(mid, "Submit")
		self.assertEqual(tr["workflow_status"], "Submitted")
		# Target code still resolvable for sanity
		self.assertTrue(frappe.db.exists("Performance Target", {"target_code": TARGET_CODE}))
