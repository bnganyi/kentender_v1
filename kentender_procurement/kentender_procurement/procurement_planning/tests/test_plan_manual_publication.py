# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-01 / AUD-XC-106 — publishing an approved Annual Plan is a manual,
role-gated command (owner decisions D4 and 7 Oct 2026: the Head of Procurement
Function presses Publish).

Before this, an approved Plan waited at "Approved — publication pending" and
only a technical caller could move it. The command reuses the publication
pipeline (`publish_annual_plan`'s body, the frozen manifest, the Treasury and
hold gates, the acknowledgement and activation); it adds who may start it."""

from __future__ import annotations

import inspect

import frappe

from kentender_procurement.procurement_planning import api as planning_api
from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import plan_read, publication_pipeline
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_publication import PublicationCase, key
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn


class ManualPublicationCase(PublicationCase):
	def approved_with_evidence(self, *, evidence: bool = True) -> tuple[dict, str]:
		accepted, _item = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		if evidence:
			self.record_treasury(version)
		return approved, version

	def publish(self, version: str, *, user: str = fx.HOPF, idempotency_key: str | None = None) -> dict:
		frappe.set_user(user)
		return publication_pipeline.publish_approved_plan(plan_version=version, idempotency_key=idempotency_key or key())

	def attempts_of(self, version: str) -> int:
		publication = frappe.db.get_value("Plan Publication", {"plan_version": version}, "name")
		return frappe.db.count("Publication Attempt", {"publication": publication})

	def status(self, version: str) -> str:
		return frappe.db.get_value("Annual Plan Version", version, "version_status")


class TestHeadOfProcurementFunctionPublishes(ManualPublicationCase):
	def test_the_head_publishes_an_approved_plan_and_it_becomes_active(self):
		_approved, version = self.approved_with_evidence()
		self.assertEqual(self.status(version), "Approved — publication pending")
		published = self.publish(version)
		self.assertEqual(published["result"], "Acknowledged")
		self.assertEqual(self.status(version), "Active")
		# the pipeline's own record, not a parallel one
		attempts = frappe.get_all("Publication Attempt", filters={"publication": published["publication"]}, pluck="result")
		self.assertEqual(attempts, ["Acknowledged"])

	def test_only_the_head_may_press_publish(self):
		_approved, version = self.approved_with_evidence()
		for user in (fx.PLANNER, fx.ACCOUNTING_OFFICER, fx.STATUTORY, fx.FINANCE_OFFICER, fx.AUTHOR, fx.HOD, fx.AUDITOR, fx.OUTSIDER, "Administrator"):
			with self.subTest(user=user):
				with self.assertRaises(frappe.DoesNotExistError):
					self.publish(version, user=user)
				self.assertEqual(self.status(version), "Approved — publication pending")
		frappe.set_user("Administrator")
		self.assertEqual(self.attempts_of(version), 0)

	def test_a_user_holding_only_the_system_manager_role_is_refused(self):
		_approved, version = self.approved_with_evidence()
		technical = "plnt.system-manager@example.test"
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", technical):
			frappe.get_doc({"doctype": "User", "email": technical, "first_name": "PLNT SM", "send_welcome_email": 0, "user_type": "System User"}).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc("User", technical, force=True, ignore_permissions=True))
		frappe.get_doc("User", technical).add_roles("System Manager")
		with self.assertRaises(frappe.DoesNotExistError):
			self.publish(version, user=technical)

	def test_it_refuses_until_treasury_evidence_is_recorded(self):
		_approved, version = self.approved_with_evidence(evidence=False)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.publish(version)
		self.assertEqual(caught.exception.code, "PLN_TREASURY_EVIDENCE_REQUIRED")
		self.assertEqual(self.status(version), "Approved — publication pending")

	def test_it_refuses_a_plan_that_is_not_approved_and_waiting(self):
		accepted, _item = self.confirmed_item()  # still a Draft
		version = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["version_reference"]
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.publish(version)
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")

	def test_a_published_plan_is_not_published_twice(self):
		_approved, version = self.approved_with_evidence()
		self.publish(version)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.publish(version)
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")
		self.assertEqual(self.attempts_of(version), 1)

	def test_the_same_key_replays_the_recorded_result(self):
		_approved, version = self.approved_with_evidence()
		one = key()
		first = self.publish(version, idempotency_key=one)
		again = self.publish(version, idempotency_key=one)
		self.assertTrue(again["idempotent"])
		self.assertEqual(again["attempt"], first["attempt"])
		self.assertEqual(self.attempts_of(version), 1)

	def test_another_user_cannot_replay_the_heads_key(self):
		_approved, version = self.approved_with_evidence()
		one = key()
		self.publish(version, idempotency_key=one)
		with self.assertRaises(frappe.DoesNotExistError):
			self.publish(version, user=fx.PLANNER, idempotency_key=one)

	def test_a_failed_publication_is_a_technical_retry_not_a_second_manual_publish(self):
		_approved, version = self.approved_with_evidence()
		destination = frappe.db.get_value("Plan Publication", {"plan_version": version}, "destination")
		frappe.db.set_value("Annual Plan Publication Destination", destination, "sandbox_outcome", "Fail")
		failed = self.publish(version)
		self.assertEqual(failed["result"], "Failed")
		self.assertEqual(self.status(version), "Publication failed")
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.publish(version)
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")
		self.assertEqual(self.attempts_of(version), 1)

	def test_an_unknown_result_is_never_sent_again_by_a_second_press(self):
		_approved, version = self.approved_with_evidence()
		destination = frappe.db.get_value("Plan Publication", {"plan_version": version}, "destination")
		frappe.db.set_value("Annual Plan Publication Destination", destination, "sandbox_outcome", "Indeterminate")
		first = self.publish(version)
		self.assertEqual(first["result"], "Indeterminate")
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.publish(version)
		self.assertEqual(caught.exception.code, "PLN_PUBLICATION_UNKNOWN")
		self.assertEqual(self.attempts_of(version), 1)

	def test_the_whitelisted_endpoint_takes_no_actor_and_is_the_heads_alone(self):
		self.assertNotIn("user", inspect.signature(planning_api.publish_annual_plan).parameters)
		_approved, version = self.approved_with_evidence()
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.DoesNotExistError):
			planning_api.publish_annual_plan(plan_version=version, idempotency_key=key())
		frappe.set_user(fx.HOPF)
		published = planning_api.publish_annual_plan(plan_version=version, idempotency_key=key())
		self.assertEqual(published["result"], "Acknowledged")


class TestSimultaneousPublish(ManualPublicationCase):
	"""Two Heads (or one Head twice) press Publish at once: the plan is sent once.
	Real two-connection tests (MariaDB REPEATABLE READ)."""

	def _commit_world(self) -> str:
		_approved, version = self.approved_with_evidence()
		frappe.db.commit()
		frappe.db.sql("select release_all_locks()")
		self.addCleanup(self._purge)
		return version

	def _purge(self):
		frappe.db.rollback()
		frappe.db.sql("select release_all_locks()")
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		frappe.db.commit()

	def attempts(self, version: str) -> int:
		frappe.db.commit()  # see what the other connections committed
		return self.attempts_of(version)

	def test_two_presses_with_different_keys_send_the_plan_once(self):
		version = self._commit_world()
		first = Conn(fx.HOPF, lambda: publication_pipeline.publish_approved_plan(plan_version=version, idempotency_key=key()), hold=True)
		self.assertTrue(first.ran.wait(WAIT))
		self.assertIsNone(first.error, repr(first.error))
		second = Conn(fx.HOPF, lambda: publication_pipeline.publish_approved_plan(plan_version=version, idempotency_key=key()))
		self.assertFalse(second.finished.wait(BLOCKED_FOR), "the second press must wait for the first")
		first.commit()
		self.assertTrue(second.finished.wait(WAIT))
		self.assertIsInstance(second.error, ProcurementPlanningError, repr(second.error))
		self.assertEqual(second.error.code, "PLN_REVIEW_STALE")
		self.assertEqual(self.attempts(version), 1)
		self.assertEqual(self.status(version), "Active")

	def test_two_presses_with_one_key_send_once_and_both_get_the_result(self):
		version = self._commit_world()
		one = key()
		first = Conn(fx.HOPF, lambda: publication_pipeline.publish_approved_plan(plan_version=version, idempotency_key=one), hold=True)
		self.assertTrue(first.ran.wait(WAIT))
		self.assertIsNone(first.error, repr(first.error))
		second = Conn(fx.HOPF, lambda: publication_pipeline.publish_approved_plan(plan_version=version, idempotency_key=one))
		self.assertFalse(second.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		first.commit()
		self.assertTrue(second.finished.wait(WAIT))
		self.assertIsNone(second.error, repr(second.error))
		self.assertTrue(second.value["idempotent"])
		self.assertEqual(second.value["attempt"], first.value["attempt"])
		self.assertEqual(self.attempts(version), 1)
