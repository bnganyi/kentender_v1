# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.1 command tests (Phase 2).

Commands run as the real fixture actors via `frappe.set_user`; the Budget
eligibility and Needs intake contracts are patched at the gateway seam (the
live contracts are exercised at the Phase 12 cross-module checkpoint)."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	needs_intake,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class PlanningCommandCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		self._eligible = patch.object(
			budget_gateway, "eligible_line_ids", return_value={fx.BUDGET_LINE}
		)
		self._eligible.start()
		self.addCleanup(self._eligible.stop)
		self._sources = patch.object(
			needs_intake, "current_accepted_sources", return_value=[]
		)
		self._sources.start()
		self.addCleanup(self._sources.stop)

	def open_alpha(self, *, user=fx.AUTHOR, fy=fx.FY_OPEN):
		frappe.set_user(user)
		return dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fy,
			idempotency_key=key(),
			fixture_namespace=fx.NS,
		)

	def add_direct(self, opened, *, user=fx.AUTHOR, **overrides):
		frappe.set_user(user)
		return dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(**overrides),
			expected_record_version=opened["record_version"],
			idempotency_key=key(),
		)

	def submit(self, opened, *, user=fx.HOD, confirmed=True):
		frappe.set_user(user)
		return dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"],
			certification_confirmed=confirmed,
			expected_record_version=opened["record_version"],
			idempotency_key=key(),
		)


class TestOpenDepartmentalPlan(PlanningCommandCase):
	def test_open_creates_one_root_and_reuses_it(self):
		first = self.open_alpha()
		self.assertTrue(first["dpp_reference"].startswith(fx.dpp_prefix()))
		self.assertEqual(first["current_state"], "Draft")
		again = self.open_alpha()
		self.assertTrue(again["idempotent"])
		self.assertEqual(again["departmental_plan"], first["departmental_plan"])
		self.assertEqual(
			frappe.db.count("Departmental Plan", {"organisation_unit": fx.OU_ALPHA}), 1
		)

	def test_same_idempotency_key_replays_the_original_result(self):
		frappe.set_user(fx.AUTHOR)
		one = key()
		first = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=one, fixture_namespace=fx.NS,
		)
		replay = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=one, fixture_namespace=fx.NS,
		)
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["departmental_plan"], first["departmental_plan"])

	def test_open_projects_current_accepted_needs_once(self):
		self._sources.stop()
		patched = patch.object(
			needs_intake, "current_accepted_sources",
			return_value=[fx.accepted_source()],
		)
		patched.start()
		self.addCleanup(patched.stop)
		self._sources = patched
		opened = self.open_alpha()
		rows = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": opened["current_version"]},
			fields=["source_origin", "need", "title", "quantity", "budget_line"],
		)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].source_origin, "Accepted Departmental Need")
		self.assertEqual(rows[0].need, "NEED-PLNT-0001")
		self.assertFalse(rows[0].budget_line)
		# reopening re-projects idempotently
		again = self.open_alpha()
		self.assertEqual(
			frappe.db.count("Departmental Plan Entry",
			                {"dpp_version": again["current_version"]}),
			1,
		)

	def test_open_without_scope_fails_closed(self):
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.open_departmental_plan(
				organisation_unit=fx.OU_ALPHA,
				fiscal_year=fx.FY_OPEN, idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_NO_CONTEXT")


class TestDirectRequirements(PlanningCommandCase):
	def test_direct_entry_is_limited_to_the_eight_values(self):
		opened = self.open_alpha()
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"],
				values={**fx.direct_values(), "priority": "High"},
				expected_record_version=opened["record_version"],
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

	def test_direct_add_edit_remove(self):
		opened = self.open_alpha()
		added = self.add_direct(opened)
		self.assertEqual(added["action"], "direct_added")
		entry_id = added["entry_id"]
		self.assertTrue(entry_id.startswith(fx.dpp_prefix().replace("DPP-", "DPPE-")))
		frappe.set_user(fx.AUTHOR)
		edited = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(title="Edited direct requirement"),
			entry_id=entry_id,
			expected_record_version=added["record_version"],
			idempotency_key=key(),
		)
		self.assertEqual(edited["action"], "direct_updated")
		removed = dpp_lifecycle.remove_direct_requirement(
			dpp_version=opened["current_version"],
			entry_id=entry_id,
			expected_record_version=edited["record_version"],
			idempotency_key=key(),
		)
		self.assertEqual(removed["action"], "direct_removed")
		self.assertEqual(
			frappe.db.count("Departmental Plan Entry",
			                {"dpp_version": opened["current_version"]}),
			0,
		)

	def test_required_by_must_fall_inside_the_financial_year(self):
		opened = self.open_alpha()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.add_direct(opened, required_by_date="2100-01-01")
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

	def test_ineligible_budget_line_is_refused(self):
		opened = self.open_alpha()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.add_direct(opened, budget_line="BL-NOT-ELIGIBLE")
		self.assertEqual(caught.exception.code, "PLN_BUDGET_LINE_INELIGIBLE")

	def test_stale_record_version_is_refused(self):
		opened = self.open_alpha()
		self.add_direct(opened)
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"],
				values=fx.direct_values(title="Stale write attempt"),
				expected_record_version=opened["record_version"],  # now stale
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_STALE_WRITE")

	def test_outsider_gets_not_found_not_existence_disclosure(self):
		opened = self.open_alpha()
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"],
				values=fx.direct_values(),
				expected_record_version=opened["record_version"],
				idempotency_key=key(),
			)


class TestNeedFunding(PlanningCommandCase):
	def _opened_with_need(self):
		self._sources.stop()
		patched = patch.object(
			needs_intake, "current_accepted_sources",
			return_value=[fx.accepted_source()],
		)
		patched.start()
		self.addCleanup(patched.stop)
		self._sources = patched
		return self.open_alpha()

	def test_need_origin_takes_only_budget_line_and_amount(self):
		opened = self._opened_with_need()
		entry_id = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"]},
			"entry_id",
		)
		frappe.set_user(fx.AUTHOR)
		result = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"],
			entry_id=entry_id,
			budget_line=fx.BUDGET_LINE,
			indicative_amount=80000000,
			expected_record_version=opened["record_version"],
			idempotency_key=key(),
		)
		self.assertEqual(result["action"], "need_funding_saved")
		row = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"], "entry_id": entry_id},
			["budget_line", "indicative_amount", "title"],
			as_dict=True,
		)
		self.assertEqual(row.budget_line, fx.BUDGET_LINE)
		self.assertEqual(int(row.indicative_amount), 80000000)
		self.assertEqual(row.title, "Test requirement")

	def test_direct_entry_refuses_need_funding_command(self):
		opened = self.open_alpha()
		added = self.add_direct(opened)
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"],
				entry_id=added["entry_id"],
				budget_line=fx.BUDGET_LINE,
				indicative_amount=100,
				expected_record_version=added["record_version"],
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")


class TestSubmission(PlanningCommandCase):
	def test_zero_entry_plan_cannot_be_submitted(self):
		opened = self.open_alpha()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.submit(opened)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

	def test_author_without_hod_role_cannot_submit(self):
		opened = self.open_alpha()
		self.add_direct(opened)
		with self.assertRaises(frappe.DoesNotExistError):
			self.submit(
				{**opened, "record_version": opened["record_version"] + 1},
				user=fx.AUTHOR,
			)

	def test_certification_checkbox_is_mandatory(self):
		opened = self.open_alpha()
		added = self.add_direct(opened)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.submit({**opened, "record_version": added["record_version"]},
			            confirmed=False)
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

	def test_coverage_gap_blocks_submission(self):
		opened = self.open_alpha()
		self.add_direct(opened)
		gap = patch.object(
			needs_intake, "coverage_gaps", return_value=["NEED-PLNT-MISSING"]
		)
		gap.start()
		self.addCleanup(gap.stop)
		frappe.set_user(fx.HOD)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.submit_departmental_plan(
				dpp_version=opened["current_version"],
				certification_confirmed=True,
				expected_record_version=opened["record_version"] + 1,
				idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_NEED_COVERAGE_INCOMPLETE")

	def test_submission_locks_snapshot_and_creates_validation_task(self):
		opened = self.open_alpha()
		added = self.add_direct(opened)
		result = self.submit({**opened, "record_version": added["record_version"]})
		self.assertEqual(result["action"], "submitted")
		self.assertEqual(result["current_state"], "Submitted")
		submission = frappe.get_doc(
			"Departmental Plan Submission",
			{"submission_reference": result["submission_reference"]},
		)
		self.assertIn(fx.OU_ALPHA_NAME, submission.attestation_text)
		self.assertIn("FY 2101/02", submission.attestation_text)
		self.assertEqual(submission.submitted_by_user, fx.HOD)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"submission": submission.name}
		)
		self.assertEqual(task.status, "Open")
		self.assertEqual(task.organisation_unit, fx.OU_ALPHA)

	def test_first_submission_outside_window_is_refused(self):
		opened = self.open_alpha(fy=fx.FY_CLOSED)
		added = self.add_direct(opened, required_by_date="2104-05-31")
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.submit({**opened, "record_version": added["record_version"]})
		self.assertEqual(caught.exception.code, "PLN_WINDOW_CLOSED")


class TestWithdrawal(PlanningCommandCase):
	def test_withdraw_then_reopen_only_while_window_open(self):
		opened = self.open_alpha()
		frappe.set_user(fx.HOD)
		withdrawn = dpp_lifecycle.withdraw_departmental_plan_version(
			dpp_version=opened["current_version"],
			expected_record_version=opened["record_version"],
			idempotency_key=key(),
		)
		self.assertEqual(withdrawn["current_state"], "Withdrawn")
		reopened = self.open_alpha()
		self.assertEqual(reopened["action"], "reopened")
		self.assertEqual(reopened["departmental_plan"], opened["departmental_plan"])

	def test_reopen_after_window_close_is_refused(self):
		opened = self.open_alpha(fy=fx.FY_CLOSED)
		frappe.set_user(fx.HOD)
		dpp_lifecycle.withdraw_departmental_plan_version(
			dpp_version=opened["current_version"],
			expected_record_version=opened["record_version"],
			idempotency_key=key(),
		)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.open_alpha(fy=fx.FY_CLOSED)
		self.assertEqual(caught.exception.code, "PLN_WINDOW_CLOSED")
