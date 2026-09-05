# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 GetDepartmentalPlan / editor read-model tests (Phase 4)."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	dpp_read,
	dpp_validation,
	needs_intake,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class DppReadCase(IntegrationTestCase):
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
		for target, attr, value in (
			(budget_gateway, "eligible_line_ids", {fx.BUDGET_LINE}),
			(budget_gateway, "list_eligible_budget_lines",
			 [{"id": fx.BUDGET_LINE, "reference": fx.BUDGET_LINE_REF, "title": "Test line", "approved": 100000000}]),
			(needs_intake, "current_accepted_sources", []),
		):
			patched = patch.object(target, attr, return_value=value)
			patched.start()
			self.addCleanup(patched.stop)

	def opened(self):
		frappe.set_user(fx.AUTHOR)
		return dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)


class TestGetDepartmentalPlan(DppReadCase):
	def test_draft_with_incomplete_funding_reads_as_des02(self):
		self._sources.stop() if hasattr(self, "_sources") else None
		patched = patch.object(
			needs_intake, "current_accepted_sources",
			return_value=[fx.accepted_source()],
		)
		patched.start()
		self.addCleanup(patched.stop)
		opened = self.opened()
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		result = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		self.assertEqual(result["header"]["title"], f"{fx.OU_ALPHA_NAME} departmental plan")
		self.assertEqual(result["header"]["badge"], "Draft")
		self.assertEqual(result["readiness"]["title"], "1 requirement needs funding details")
		self.assertIn("Select a Procurement Budget Line and enter the indicative amount",
		              result["readiness"]["text"])
		by_origin = {row["source_origin"]: row for row in result["entries"]}
		need_row = by_origin["Accepted Departmental Need"]
		self.assertEqual(need_row["source_label"], "Accepted Need · NEED-PLNT-0001")
		self.assertEqual(need_row["budget_line_display"], "Not selected")
		self.assertEqual(need_row["amount_display"], "—")
		self.assertEqual(need_row["status"], "Funding incomplete")
		self.assertEqual(need_row["action"], "Complete")
		direct_row = by_origin["Direct departmental requirement"]
		self.assertEqual(direct_row["status"], "Ready")
		self.assertEqual(direct_row["action"], "Edit")
		self.assertEqual(result["totals_caption"], "2 requirements · KES 1,000,000 specified")
		self.assertIn("Open until", result["context"]["window"]["display"])
		self.assertFalse(result["can_submit"])
		self.assertFalse(result["certification"]["show"])

	def test_ready_plan_reads_as_des05_for_the_hod_only(self):
		opened = self.opened()
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		author_view = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		self.assertEqual(author_view["header"]["badge"], "Ready to submit")
		self.assertIsNone(author_view["readiness"])
		self.assertFalse(author_view["can_submit"])  # author is not the HoD
		frappe.set_user(fx.HOD)
		hod_view = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		self.assertTrue(hod_view["can_submit"])
		self.assertTrue(hod_view["certification"]["show"])
		self.assertIn(fx.OU_ALPHA_NAME, hod_view["certification"]["text"])
		self.assertIn("FY 2101/02", hod_view["certification"]["text"])
		self.assertEqual(hod_view["totals_caption"], "1 requirement · KES 1,000,000")

	def test_returned_plan_attaches_issues_to_their_entries(self):
		opened = self.opened()
		frappe.set_user(fx.AUTHOR)
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
		frappe.set_user(fx.PLANNER)
		dpp_validation.return_departmental_plan(
			task=task.name,
			issues=[{
				"entry_id": added["entry_id"],
				"problem": "Amount unsupported",
				"correction": "Align the amount with the budget line.",
			}],
			task_token=task.task_token, idempotency_key=key(),
		)
		frappe.set_user(fx.AUTHOR)
		result = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		self.assertTrue(result["has_returned_issues"])
		row = next(r for r in result["entries"] if r["entry_id"] == added["entry_id"])
		self.assertEqual(row["issues"][0]["problem"], "Amount unsupported")
		self.assertEqual(
			row["issues"][0]["correction"], "Align the amount with the budget line."
		)

	def test_out_of_scope_actor_gets_not_found(self):
		opened = self.opened()
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])

	def test_planner_reads_without_edit_actions(self):
		opened = self.opened()
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		result = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		self.assertEqual(result["access"], "planner")
		self.assertEqual([row["action"] for row in result["entries"]], [""])
		self.assertFalse(result["can_submit"])


class TestEntryEditorRead(DppReadCase):
	def test_need_entry_editor_carries_the_six_facts_and_funding_only(self):
		patched = patch.object(
			needs_intake, "current_accepted_sources",
			return_value=[fx.accepted_source()],
		)
		patched.start()
		self.addCleanup(patched.stop)
		opened = self.opened()
		entry_id = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"]}, "entry_id",
		)
		frappe.set_user(fx.AUTHOR)
		result = dpp_read.get_dpp_entry_editor(
			dpp_reference=opened["dpp_reference"], entry_id=entry_id
		)
		entry = result["entry"]
		self.assertEqual(entry["title"], "Test requirement")
		self.assertEqual(entry["quantity_display"], "1 each")
		self.assertEqual(entry["required_by_display"], "31 May 2102")
		self.assertEqual(entry["need_reference_line"], "NEED-PLNT-0001 · Version 1")
		self.assertEqual(result["currency"], "KES")
		self.assertEqual(result["budget_lines"][0]["id"], fx.BUDGET_LINE)
		self.assertIn("approved_display", result["budget_lines"][0])

	def test_direct_editor_offers_units_and_eligible_lines(self):
		opened = self.opened()
		frappe.set_user(fx.AUTHOR)
		result = dpp_read.get_dpp_entry_editor(dpp_reference=opened["dpp_reference"])
		self.assertNotIn("entry", result)
		self.assertTrue(any(u["id"] == fx.UNIT for u in result["units"]))
		self.assertEqual(len(result["budget_lines"]), 1)

	def test_planner_cannot_open_the_editor(self):
		opened = self.opened()
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			dpp_read.get_dpp_entry_editor(dpp_reference=opened["dpp_reference"])


class TestValidationTaskRead(DppReadCase):
	def submitted_task(self):
		opened = self.opened()
		frappe.set_user(fx.AUTHOR)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		return frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		), added

	def test_task_read_serves_the_immutable_snapshot_not_live_rows(self):
		task, added = self.submitted_task()
		# mutate the live entry AFTER submission (only possible as Administrator
		# here — the point is the read must not follow it)
		frappe.set_user("Administrator")
		frappe.db.set_value(
			"Departmental Plan Entry",
			{"entry_id": added["entry_id"]},
			"title", "TAMPERED TITLE", update_modified=False,
		)
		frappe.set_user(fx.PLANNER)
		result = dpp_read.get_dpp_validation_task(task=task.name)
		self.assertEqual(result["entries"][0]["title"], "Direct requirement")
		self.assertEqual(result["context"]["requirements"], 1)
		self.assertEqual(result["context"]["total_display"], "KES 1,000,000")
		self.assertEqual(result["header"]["badge"], "Awaiting validation")
		self.assertIn("Certified by", result["certification"]["signed_line"])
		self.assertIn("Goods", result["requirement_types"])
		self.assertFalse(result["maker_checker_blocked"])
		self.assertEqual(result["task_token"], task.task_token)

	def test_the_certifier_is_flagged_maker_checker_blocked(self):
		task, _ = self.submitted_task()
		frappe.set_user(fx.HYBRID)
		result = dpp_read.get_dpp_validation_task(task=task.name)
		self.assertFalse(result["maker_checker_blocked"])  # HYBRID did not certify this one
		# now a submission the HYBRID certified themselves
		fx.wipe_planning_rows()
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
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
		own_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		result = dpp_read.get_dpp_validation_task(task=own_task.name)
		self.assertTrue(result["maker_checker_blocked"])

	def test_non_planner_gets_not_found(self):
		task, _ = self.submitted_task()
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(frappe.DoesNotExistError):
			dpp_read.get_dpp_validation_task(task=task.name)
