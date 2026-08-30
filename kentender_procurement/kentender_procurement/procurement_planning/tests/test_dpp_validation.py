# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §4.6/§5 validation-decision tests (Phase 2)."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class ValidationCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		for target, value in (
			(budget_gateway, "eligible_line_ids"),
			(needs_intake, "current_accepted_sources"),
		):
			patched = patch.object(
				target, value,
				return_value={fx.BUDGET_LINE} if value == "eligible_line_ids" else [],
			)
			patched.start()
			self.addCleanup(patched.stop)

	def submitted_task(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		self.entry_id = added["entry_id"]
		return task

	def accept(self, task, *, user=fx.PLANNER, classifications=None, idem=None):
		frappe.set_user(user)
		return dpp_validation.accept_departmental_plan(
			task=task.name,
			classifications=classifications
			if classifications is not None
			else {self.entry_id: "Consulting services"},
			task_token=task.task_token,
			idempotency_key=idem or key(),
		)


class TestAcceptance(ValidationCase):
	def test_acceptance_requires_a_classification_for_every_entry(self):
		task = self.submitted_task()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.accept(task, classifications={})
		self.assertEqual(caught.exception.code, "PLN_CLASSIFICATION_INCOMPLETE")

	def test_acceptance_rejects_a_retired_requirement_type(self):
		task = self.submitted_task()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.accept(task, classifications={self.entry_id: "Not a governed type"})
		self.assertEqual(caught.exception.code, "PLN_CLASSIFICATION_INCOMPLETE")

	def test_acceptance_records_decision_and_creates_the_draft_annual_plan(self):
		task = self.submitted_task()
		result = self.accept(task)
		self.assertEqual(result["action"], "accepted")
		self.assertTrue(result["annual_plan"].startswith("PLN-PLNT-2098-"))
		self.assertTrue(result["annual_plan_version"].endswith("-V1"))
		decision = frappe.get_doc(
			"Departmental Plan Validation Decision",
			{"decision_reference": result["decision_reference"]},
		)
		self.assertEqual(decision.decision, "Accept departmental plan")
		self.assertIn("Consulting services", decision.classifications)
		root = frappe.get_doc("Departmental Plan", {"dpp_reference": result["dpp_reference"]})
		self.assertEqual(root.current_state, "Accepted")
		self.assertEqual(root.current_accepted_version, root.current_version)
		self.assertEqual(
			frappe.db.get_value(
				"Departmental Plan Validation Task", task.name, "status"
			),
			"Completed",
		)
		# no Plan Item, no reservation from acceptance (PLN-AC-012/023)
		self.assertEqual(frappe.db.count("Annual Plan Item", {"fixture_namespace": fx.NS}), 0)

	def test_second_acceptance_reuses_the_one_annual_plan_root(self):
		task = self.submitted_task()
		first = self.accept(task)
		frappe.set_user(fx.HOD)
		update = dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=first["dpp_reference"],
			expected_record_version=frappe.db.get_value(
				"Departmental Plan", {"dpp_reference": first["dpp_reference"]}, "record_version"
			),
			idempotency_key=key(),
		)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=update["current_version"], certification_confirmed=True,
			expected_record_version=update["record_version"], idempotency_key=key(),
		)
		task2 = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		second = self.accept(task2)
		self.assertEqual(second["annual_plan"], first["annual_plan"])
		self.assertEqual(frappe.db.count("Annual Plan", {"fixture_namespace": fx.NS}), 1)

	def test_hod_submitter_cannot_accept_their_own_submission(self):
		"""The HYBRID persona legitimately holds HoD + Planner (§6.1); what is
		blocked is deciding the submission they themselves certified."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HYBRID)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		entry = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"]}, "entry_id",
		)
		with self.assertRaises(ProcurementPlanningError) as caught:
			frappe.set_user(fx.HYBRID)
			dpp_validation.accept_departmental_plan(
				task=task.name, classifications={entry: "Goods"},
				task_token=task.task_token, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_SEGREGATION_CONFLICT")
		# a different Planner may decide it
		result = self.accept_named(task, entry)
		self.assertEqual(result["action"], "accepted")

	def accept_named(self, task, entry_id):
		frappe.set_user(fx.PLANNER)
		return dpp_validation.accept_departmental_plan(
			task=task.name, classifications={entry_id: "Goods"},
			task_token=task.task_token, idempotency_key=key(),
		)

	def test_stale_task_token_is_refused(self):
		task = self.submitted_task()
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_validation.accept_departmental_plan(
				task=task.name,
				classifications={self.entry_id: "Goods"},
				task_token="not-the-token",
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")

	def test_acceptance_replays_idempotently(self):
		task = self.submitted_task()
		idem = key()
		first = self.accept(task, idem=idem)
		replay = self.accept(task, idem=idem)
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["decision_reference"], first["decision_reference"])

	def test_unscoped_actor_gets_not_found(self):
		task = self.submitted_task()
		with self.assertRaises(frappe.DoesNotExistError):
			self.accept(task, user=fx.OUTSIDER)


class TestReturn(ValidationCase):
	def test_return_requires_structured_issues(self):
		task = self.submitted_task()
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_validation.return_departmental_plan(
				task=task.name, issues=[{"entry_id": self.entry_id, "problem": "", "correction": ""}],
				task_token=task.task_token, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

	def test_return_preserves_snapshot_and_creates_the_correction_draft(self):
		task = self.submitted_task()
		frappe.set_user(fx.PLANNER)
		result = dpp_validation.return_departmental_plan(
			task=task.name,
			issues=[{
				"entry_id": self.entry_id,
				"problem": "Amount looks wrong",
				"correction": "Confirm the indicative amount against the budget line.",
			}],
			task_token=task.task_token,
			idempotency_key=key(),
		)
		self.assertEqual(result["action"], "returned")
		submitted_version = frappe.get_doc("Departmental Plan Version", task.dpp_version)
		self.assertEqual(submitted_version.version_status, "Returned")
		self.assertTrue(submitted_version.submission)  # snapshot preserved
		correction = frappe.get_doc(
			"Departmental Plan Version", {"version_reference": result["correction_version"]}
		)
		self.assertEqual(correction.version_status, "Draft")
		self.assertEqual(correction.returned_from_submission, task.submission)
		copied = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": correction.name},
			pluck="entry_id",
		)
		self.assertEqual(copied, [self.entry_id])  # stable entry id carried over
		root = frappe.get_doc("Departmental Plan", correction.departmental_plan)
		self.assertEqual(root.current_state, "Returned")
		self.assertEqual(root.current_version, correction.name)

	def test_corrected_draft_resubmits_after_the_window_closes(self):
		task = self.submitted_task()
		frappe.set_user(fx.PLANNER)
		result = dpp_validation.return_departmental_plan(
			task=task.name,
			issues=[{
				"entry_id": self.entry_id,
				"problem": "Description too thin",
				"correction": "Expand the requirement description.",
			}],
			task_token=task.task_token, idempotency_key=key(),
		)
		correction = frappe.get_doc(
			"Departmental Plan Version", {"version_reference": result["correction_version"]}
		)
		root = frappe.get_doc("Departmental Plan", correction.departmental_plan)
		# close the window under the correction, then resubmit — §5.1 allows it
		window = frappe.get_doc(
			"Departmental Plan Submission Window", {"pe_fy_context": fx.CTX_OPEN}
		)
		original_close = window.closes_at
		frappe.db.set_value(
			"Departmental Plan Submission Window", window.name,
			"closes_at", "2020-02-01 00:00:00", update_modified=False,
		)
		self.addCleanup(
			frappe.db.set_value,
			"Departmental Plan Submission Window", window.name,
			"closes_at", original_close,
		)
		frappe.set_user(fx.HOD)
		resubmitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=correction.name, certification_confirmed=True,
			expected_record_version=root.record_version, idempotency_key=key(),
		)
		self.assertEqual(resubmitted["action"], "submitted")
