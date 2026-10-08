# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-ACCESS-REV-001 v0.2 §2 / P01–P06 — the read-only Plan-source reader.

BUILT AHEAD OF APPROVAL: the Plan-source clarification is the proposed PLN-R2
(PLN v1.30 candidate); only PLN18-AC-025 is approved. Reading is the whole
grant: an Accounting Officer, Head of Procurement Function, statutory approver
or Finance Confirmation Officer reads the exact submission a plan under their
review consumed, and nothing else. Nothing here widens a command.

A reviewer's right is the review task that exists (the real record the Plan
flow creates), never a caller-supplied parent id and never an approval state
written by the test.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_classification,
	dpp_lifecycle,
	dpp_read,
	dpp_validation,
	needs_intake,
	plan_governance,
	plan_read,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_governance import GovernanceCase


def key() -> str:
	return uuid4().hex


class PlanSourceCase(GovernanceCase):
	def submission_of(self, item_id: str) -> str:
		"""The DPP submission whose entry feeds this Plan item."""
		entry = frappe.db.get_value("Plan Source Allocation", {"plan_item_id": item_id}, "dpp_entry")
		version = frappe.db.get_value("Departmental Plan Entry", entry, "dpp_version")
		return frappe.db.get_value("Departmental Plan Version", version, "submission")

	def read_classification(self, user: str, submission: str) -> dict:
		frappe.set_user(user)
		return dpp_classification.get_accepted_dpp_classification(dpp_submission=submission)

	def assertMasked(self, user: str, submission: str) -> None:
		with self.assertRaises(frappe.DoesNotExistError):
			self.read_classification(user, submission)


class TestPlanSourceReaders(PlanSourceCase):
	def test_the_accounting_officer_reads_the_source_of_the_plan_awaiting_adoption(self):
		accepted, item_id = self.confirmed_item()
		self.submit(accepted["annual_plan"])
		result = self.read_classification(fx.ACCOUNTING_OFFICER, self.submission_of(item_id))
		self.assertTrue(result["ok"])
		self.assertEqual(len(result["rows"]), 1)
		self.assertFalse(result["can_correct"])

	def test_the_head_of_procurement_function_reads_the_source_once_funding_is_checked(self):
		accepted, item_id = self.confirmed_item()
		result = self.read_classification(fx.HOPF, self.submission_of(item_id))
		self.assertTrue(result["ok"])
		self.assertFalse(result["can_correct"])

	def test_the_finance_confirmation_officer_reads_the_source_of_the_plan_they_confirmed(self):
		accepted, item_id = self.confirmed_item()
		result = self.read_classification(fx.FINANCE_OFFICER, self.submission_of(item_id))
		self.assertTrue(result["ok"])
		self.assertFalse(result["can_correct"])

	def test_the_statutory_approver_reads_only_once_the_plan_reaches_them(self):
		accepted, item_id = self.confirmed_item()
		submitted = self.submit(accepted["annual_plan"])
		submission = self.submission_of(item_id)
		self.assertMasked(fx.STATUTORY, submission)

		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
		result = self.read_classification(fx.STATUTORY, submission)
		self.assertTrue(result["ok"])
		self.assertFalse(result["can_correct"])

	def test_the_planner_keeps_the_working_read_and_the_correction_offer(self):
		accepted, item_id = self.confirmed_item()
		result = self.read_classification(fx.PLANNER, self.submission_of(item_id))
		self.assertTrue(result["can_correct"])


class TestReaderBoundaries(PlanSourceCase):
	def test_a_draft_plan_with_no_review_task_is_not_readable_by_the_accounting_officer(self):
		accepted, item_id = self.formed_item()
		self.assertMasked(fx.ACCOUNTING_OFFICER, self.submission_of(item_id))

	def test_an_accepted_submission_no_plan_consumed_is_masked(self):
		"""P04 — acceptance alone grants no read."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
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
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(
			task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=key(),
		)
		for user in (fx.ACCOUNTING_OFFICER, fx.HOPF, fx.STATUTORY, fx.FINANCE_OFFICER):
			self.assertMasked(user, task.submission)

	def test_a_person_with_no_planning_responsibility_is_masked_even_for_a_consumed_source(self):
		accepted, item_id = self.confirmed_item()
		self.submit(accepted["annual_plan"])
		self.assertMasked(fx.OUTSIDER, self.submission_of(item_id))

	def test_an_unknown_submission_is_masked(self):
		self.assertMasked(fx.ACCOUNTING_OFFICER, "DPPS-DOES-NOT-EXIST")

	def test_the_reader_cannot_correct_the_classification_through_the_service(self):
		accepted, item_id = self.confirmed_item()
		self.submit(accepted["annual_plan"])
		submission = self.submission_of(item_id)
		evidence = dpp_classification.effective_classification(
			submission, frappe.db.get_value("Departmental Plan Entry", frappe.db.get_value("Plan Source Allocation", {"plan_item_id": item_id}, "dpp_entry"), "entry_id")
		)["evidence_id"]
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with self.assertRaises(Exception):
			dpp_classification.correct_accepted_requirement_classification(
				dpp_submission=submission,
				dpp_entry_id=frappe.db.get_value("Departmental Plan Entry", frappe.db.get_value("Plan Source Allocation", {"plan_item_id": item_id}, "dpp_entry"), "entry_id"),
				expected_evidence_id=evidence, new_requirement_type="Works",
				reason="The requirement is for construction work and not for goods at all.", idempotency_key=key(),
			)


class TestDepartmentalPlanSourceRead(PlanSourceCase):
	def test_the_accounting_officer_opens_the_consumed_departmental_plan_read_only(self):
		accepted, item_id = self.confirmed_item()
		self.submit(accepted["annual_plan"])
		entry = frappe.db.get_value("Plan Source Allocation", {"plan_item_id": item_id}, "dpp_entry")
		version = frappe.db.get_value("Departmental Plan Entry", entry, "dpp_version")
		root = frappe.db.get_value("Departmental Plan Version", version, "departmental_plan")
		reference = frappe.db.get_value("Departmental Plan", root, "dpp_reference")
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		result = dpp_read.get_departmental_plan(dpp_reference=reference)
		self.assertTrue(result["entries"])
		self.assertFalse(result["mutable"])
		self.assertFalse(result["can_submit"])
		self.assertFalse(result["can_create_update"])
		# no link into the editor, which the reader cannot open (§12.1 dead-end rule)
		self.assertEqual({row["action"] for row in result["entries"]}, {""})

	def test_an_unsent_draft_departmental_plan_stays_masked(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		reference = frappe.db.get_value("Departmental Plan", opened["departmental_plan"], "dpp_reference") if opened.get("departmental_plan") else opened["dpp_reference"]
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with self.assertRaises(frappe.DoesNotExistError):
			dpp_read.get_departmental_plan(dpp_reference=reference)


class TestEmittedClassificationLink(PlanSourceCase):
	"""The Plan item's "View classification details" is offered only where the
	destination opens for that viewer (no dead-end link)."""

	def readable(self, user: str, item_id: str) -> list[bool]:
		frappe.set_user(user)
		return [row["classification_readable"] for row in plan_read.get_plan_item(plan_item_id=item_id)["sources"]]

	def test_the_link_is_offered_exactly_to_those_who_can_open_the_page(self):
		accepted, item_id = self.confirmed_item()
		self.submit(accepted["annual_plan"])
		self.assertEqual(self.readable(fx.PLANNER, item_id), [True])
		self.assertEqual(self.readable(fx.ACCOUNTING_OFFICER, item_id), [True])
		self.assertEqual(self.readable(fx.HOPF, item_id), [True])
		# the statutory approver has no review of this plan yet; the auditor holds no source read
		self.assertEqual(self.readable(fx.STATUTORY, item_id), [False])
		self.assertEqual(self.readable(fx.AUDITOR, item_id), [False])

	def test_every_offered_link_opens_and_every_withheld_link_is_masked(self):
		accepted, item_id = self.confirmed_item()
		self.submit(accepted["annual_plan"])
		submission = self.submission_of(item_id)
		for user in (fx.PLANNER, fx.ACCOUNTING_OFFICER, fx.HOPF, fx.STATUTORY, fx.AUDITOR):
			offered = all(self.readable(user, item_id))
			frappe.set_user(user)
			if offered:
				self.assertTrue(dpp_classification.get_accepted_dpp_classification(dpp_submission=submission)["ok"])
			else:
				with self.assertRaises(frappe.DoesNotExistError):
					dpp_classification.get_accepted_dpp_classification(dpp_submission=submission)
