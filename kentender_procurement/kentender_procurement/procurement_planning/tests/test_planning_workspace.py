# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §12.1 workspace read-model tests (Phase 3).

The read-offer parity rules (NDS-807/NDS-911 class): every open task the
actor may decide appears as a row, nothing is offered that the command layer
would refuse, and a read creates no record."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import formatdate, nowdate

from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	needs_intake,
	workspace,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class WorkspaceCase(IntegrationTestCase):
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
			(needs_intake, "current_accepted_sources", []),
		):
			patched = patch.object(target, attr, return_value=value)
			patched.start()
			self.addCleanup(patched.stop)

	def load(self, user):
		frappe.set_user(user)
		return workspace.get_planning_workspace(financial_year=fx.FY_OPEN, user=user)

	def submitted(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		return dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)


class TestWorkspace(WorkspaceCase):
	def test_no_responsibility_resolves_to_the_forbidden_panel_without_record_creation(self):
		"""PLN-AC-111/112 — the verdict resolves before anything renders."""
		before = frappe.db.count("Departmental Plan")
		nobody = "plnt.nobody@example.test"
		fx._user(nobody, "PLNT Nobody")
		result = self.load(nobody)
		self.assertEqual(result["outcome"], "FORBIDDEN")
		self.assertEqual(result["forbidden"]["heading"], "You do not have access to Procurement Planning")
		self.assertIn("Procurement Planner, Head of Procurement Function, Finance Confirmation Officer, Accounting Officer", result["forbidden"]["text"])
		self.assertIn("KenTender administrator", result["forbidden"]["text"])
		self.assertEqual(frappe.db.count("Departmental Plan"), before)
		# an Author elsewhere sees an OK page with nothing of Alpha's
		other = self.load(fx.OUTSIDER)
		self.assertEqual(other["outcome"], "OK")
		self.assertEqual(other["departmental_plans"], [])

	def test_author_is_offered_their_departments_plan_and_only_theirs(self):
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA,
			fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		result = self.load(fx.AUTHOR)
		self.assertEqual(result["outcome"], "OK")
		departments = [row["department"] for row in result["departmental_plans"]]
		self.assertEqual(departments, [fx.OU_ALPHA_NAME])
		headlines = [row["headline"] for row in result["actionable"]]
		self.assertIn("Continue departmental plan", headlines)
		self.assertIsNone(result["schedule_health"])  # PLN-AC-129: absent, not zero

	def test_every_open_validation_task_is_offered_to_the_planner(self):
		self.submitted()
		result = self.load(fx.PLANNER)
		validate_rows = [row for row in result["actionable"] if row["headline"] == "Validate departmental plan"]
		open_tasks = frappe.db.count("Departmental Plan Validation Task", {"fiscal_year": fx.FY_OPEN, "status": "Open"})
		self.assertEqual(len(validate_rows), open_tasks)
		self.assertGreater(open_tasks, 0)
		# FU-15 — the line says which version, how big, how much, when and by whom
		self.assertEqual(
			validate_rows[0]["supporting"],
			f"{fx.OU_ALPHA_NAME} · Submission 1 · 1 requirement · KES 1,000,000 · submitted {formatdate(nowdate(), 'd MMM yyyy')} by PLNT Head of Department",
		)
		self.assertEqual(validate_rows[0]["route"][1], "dpp-review")

	def test_auditor_sees_rows_but_is_offered_no_work(self):
		self.submitted()
		result = self.load(fx.AUDITOR)
		self.assertEqual(result["outcome"], "OK")
		self.assertEqual(result["actionable"], [])
		self.assertEqual(len(result["departmental_plans"]), 1)

	def test_finance_and_governance_oversight_roles_see_rows_without_a_dead_end_view_link(self):
		"""Finance Confirmation Officer/Accounting Officer/Plan Statutory Approver are
		classified as Site-wide oversight so they see every departmental plan's
		status, but `dpp_read._access` never authorises them to open the DPP
		page itself — offering a route there is the NDS-807 read-offer-vs-
		command class of defect (PLN-CHG-001 v1.2 §6, §12.1 route table)."""
		self.submitted()
		for user in (fx.FINANCE_OFFICER, fx.ACCOUNTING_OFFICER, fx.STATUTORY):
			with self.subTest(user=user):
				result = self.load(user)
				self.assertEqual(result["outcome"], "OK")
				self.assertEqual(len(result["departmental_plans"]), 1)
				self.assertFalse(result["departmental_plans"][0].get("route"))

	def test_planner_and_auditor_keep_the_dpp_view_route(self):
		self.submitted()
		for user in (fx.PLANNER, fx.AUDITOR):
			with self.subTest(user=user):
				result = self.load(user)
				self.assertTrue(result["departmental_plans"][0].get("route"))

	def test_the_validate_actionable_card_carries_u01d_labelled_facts(self):
		"""U01-D — the Planner's "Your actions" card shows labelled facts, not
		one prose line (the free-text `supporting` line is kept too, for
		whatever does not yet have a frame-specified fact set)."""
		self.submitted()
		planner_row = next(r for r in self.load(fx.PLANNER)["actionable"] if r["headline"] == "Validate departmental plan")
		self.assertEqual([f["label"] for f in planner_row["facts"]], ["Submitted by", "Submitted", "Requirements", "Value"])

	def test_the_continue_actionable_card_carries_u01e_labelled_facts(self):
		"""U01-E — the Departmental Author's own "Your actions" card."""
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		author_row = next(r for r in self.load(fx.AUTHOR)["actionable"] if r["headline"] == "Continue departmental plan")
		self.assertEqual([f["label"] for f in author_row["facts"]], ["Submission", "Requirements", "Specified value"])

	def test_the_governance_decision_actionable_card_carries_u01f_labelled_facts(self):
		submitted = self.submitted()
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		entry = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": submitted["current_version"]}, ["name", "entry_id"], as_dict=True)
		frappe.set_user(fx.PLANNER)
		from kentender_procurement.procurement_planning.services import dpp_validation, plan_finance, plan_governance, plan_read, plan_workbench

		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			classifications={entry.entry_id: "Consulting services"},
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=plan["version_reference"], dpp_entries=[entry.name], mode="each",
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item = plan_read.get_plan_item(plan_item_id=formed["created_items"][0])
		plan_workbench.save_plan_item(
			plan_item=formed["created_items"][0], values=fx.item_values(), expected_record_version=item["record_version"], idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		finance_task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=finance_task.name, task_token=finance_task.task_token, idempotency_key=key())
		frappe.set_user(fx.HOPF)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)

		ao_row = next(r for r in self.load(fx.ACCOUNTING_OFFICER)["actionable"] if r["action"] == "Open decision")
		self.assertEqual([f["label"] for f in ao_row["facts"]], ["Version", "Plan Items", "Value", "Submitted by", "Submitted"])
		self.assertEqual(dict((f["label"], f["value"]) for f in ao_row["facts"])["Version"], "1")

	def test_departmental_plans_use_the_single_submission_shape_before_anything_is_accepted(self):
		"""U01-D — nothing accepted yet this FY: one Submission count, no
		Accepted/Open split (there is nothing accepted to split), no route to
		view (a submitted-not-yet-validated plan has nothing to view)."""
		self.submitted()
		result = self.load(fx.PLANNER)
		self.assertEqual(result["departmental_plans_shape"], "submission")
		row = result["departmental_plans"][0]
		self.assertEqual(row["version"], 1)
		self.assertIsNone(row["accepted_submission"])
		self.assertIsNone(row["open_submission"])

	def test_departmental_plans_switch_to_the_accepted_shape_once_one_plan_is_accepted(self):
		"""U01-A/B/C — once any departmental plan this FY has been accepted,
		every row carries an explicit Accepted Submission number (None where
		that department itself has none) instead of the single Submission
		count."""
		from kentender_procurement.procurement_planning.services import dpp_validation

		submitted = self.submitted()
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": submitted["current_version"]}, "entry_id")
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			classifications={entry_id: "Consulting services"},
		)
		result = self.load(fx.PLANNER)
		self.assertEqual(result["departmental_plans_shape"], "accepted")
		row = result["departmental_plans"][0]
		self.assertEqual(row["accepted_submission"], 1)
		self.assertIsNone(row["open_submission"])

	def test_workspace_read_creates_nothing(self):
		counts = {
			d: frappe.db.count(d)
			for d in ("Departmental Plan", "Annual Plan", "Planning Command Journal")
		}
		self.load(fx.PLANNER)
		for doctype, count in counts.items():
			self.assertEqual(frappe.db.count(doctype), count, doctype)

	def test_departmental_rows_name_the_outcome_not_the_verb_open(self):
		"""Agreed 2026-09-11: "Open" read the same for creating a plan and for
		navigating to one. The create row names the gap and the button the act;
		the navigate rows read Continue / Correct."""
		before = self.load(fx.AUTHOR)
		self.assertEqual(before["actionable"][0]["headline"], "No departmental plan yet for FY 2101/02")
		self.assertEqual(before["actionable"][0]["supporting"], fx.OU_ALPHA_NAME)
		self.assertEqual(before["actionable"][0]["action"], "Start departmental plan")
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		after = self.load(fx.AUTHOR)
		self.assertEqual(after["actionable"][0]["headline"], "Continue departmental plan")
		self.assertEqual(after["actionable"][0]["supporting"], f"{fx.OU_ALPHA_NAME} · Submission 1 · 0 requirements · KES 0")
		self.assertEqual(after["actionable"][0]["action"], "Continue")
		self.assertNotIn("Open", [a["action"] for a in after["actionable"]])

	def test_closed_window_shows_not_included_and_critical_status(self):
		self._sources = patch.object(needs_intake, "current_accepted_sources", return_value=[fx.accepted_source()])
		self._sources.start()
		self.addCleanup(self._sources.stop)
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		fx.close_test_intake()
		self.addCleanup(fx.open_test_intake)
		result = self.load(fx.PLANNER)
		self.assertFalse(result["window_open"])
		self.assertIn("not included in any departmental plan", result["not_included"]["title"])
		self.assertIn("submission window closed before they were added", result["not_included"]["text"])
		self.assertIn(fx.OU_ALPHA_NAME, result["not_included"]["text"])
		row = result["departmental_plans"][0]
		self.assertEqual(row["status"], "Not submitted — window closed")
		self.assertEqual(row["status_kind"], "critical")

	def test_an_open_update_on_an_accepted_plan_is_not_a_missed_window(self):
		"""§4.3 — one accepted Version may coexist with one open successor, and
		§7.1 strands only departments with no submitted DPP. A department whose
		accepted plan has a Draft update open after window close used to read
		"Not submitted — window closed" and its accepted Needs were counted as
		not included in any plan (reported live 2026-09-11)."""
		from kentender_procurement.procurement_planning.services import dpp_validation

		submitted = self.submitted()
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": submitted["current_version"]}, "entry_id")
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			classifications={entry_id: "Consulting services"},
		)
		self._sources = patch.object(needs_intake, "current_accepted_sources", return_value=[fx.accepted_source()])
		self._sources.start()
		self.addCleanup(self._sources.stop)
		fx.close_test_intake()
		self.addCleanup(fx.open_test_intake)
		frappe.set_user(fx.HOD)
		dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=submitted["departmental_plan"],
			expected_record_version=frappe.db.get_value("Departmental Plan", submitted["departmental_plan"], "record_version"),
			idempotency_key=key(),
		)

		result = self.load(fx.PLANNER)
		self.assertFalse(result["window_open"])
		self.assertIsNone(result["not_included"])
		self.assertEqual(result["departmental_plans_shape"], "accepted")
		row = result["departmental_plans"][0]
		self.assertEqual(row["version"], 2)
		self.assertEqual(row["status"], "Accepted · update in progress")
		self.assertEqual(row["status_kind"], "attention")
		self.assertEqual(row["accepted_submission"], 1)
		self.assertEqual(row["open_submission"], 2)
		# the department is still offered its draft to continue
		author = self.load(fx.AUTHOR)
		self.assertEqual(author["actionable"][0]["headline"], "Continue departmental plan")

	def test_an_active_plan_with_unallocated_entries_offers_prepare_plan_update(self):
		"""§5 (Active; no successor → Begin plan update, Procurement Planner)
		and §12.1. The workspace used to demote a pending accepted entry on an
		Active plan to a waiting line and offer no route at all to the Annual
		Plan record, stranding the Planner (reported live 2026-09-11)."""
		from kentender_procurement.procurement_planning.services import dpp_validation

		submitted = self.submitted()
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": submitted["current_version"]}, "entry_id")
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			classifications={entry_id: "Consulting services"},
		)
		# the read model keys on version_status and active_version only; the
		# full activation path is proven in test_plan_publication
		frappe.db.set_value("Annual Plan Version", accepted["annual_plan_version"], "version_status", "Active")
		frappe.db.set_value("Annual Plan", accepted["annual_plan"], {"active_version": accepted["annual_plan_version"], "open_successor_version": ""})

		result = self.load(fx.PLANNER)
		self.assertEqual(result["annual_plan"]["plan_reference"], accepted["annual_plan"])
		self.assertEqual(result["annual_plan"]["summary"], "Annual Plan · Active Version 1")
		self.assertEqual(len(result["annual_plan"]["blocks"]), 1)
		block = result["annual_plan"]["blocks"][0]
		self.assertEqual(block["kind"], "active")
		self.assertEqual(block["version_status"], "Active")
		self.assertEqual(block["action"], "Prepare plan update")
		self.assertEqual(block["action_kind"], "primary")
		# a non-Planner reader gets the same facts but only a plain View link
		auditor_block = self.load(fx.AUDITOR)["annual_plan"]["blocks"][0]
		self.assertEqual(auditor_block["action"], "View Active Plan")
		self.assertEqual(auditor_block["action_kind"], "secondary")
		self.assertEqual(result["waiting"], [])
		row = result["actionable"][0]
		self.assertEqual(row["headline"], "1 accepted departmental entry not yet in the Active plan")
		self.assertEqual(row["supporting"], f"{fx.OU_ALPHA_NAME} · KES 1,000,000")
		self.assertEqual(row["action"], "Prepare plan update")
		self.assertEqual(row["route"], ["annual-procurement-plan", accepted["annual_plan"]])
		self.assertEqual(row["kind"], "attention")
		# an auditor reads the same summary but is offered nothing
		self.assertEqual(self.load(fx.AUDITOR)["actionable"], [])


class TestAnnualPlanCard(WorkspaceCase):
	"""PLN-CHG-001 v1.18 §9.6 (U01) — the Annual Plan card's own structured
	fact blocks and, at most, one Planner-discretionary command; every other
	reader gets the same facts with a plain View link, or no block at all."""

	def test_no_plan_yet_is_an_empty_block_list(self):
		result = self.load(fx.PLANNER)
		self.assertEqual(result["annual_plan"], {"plan_reference": "", "title": "", "summary": "", "blocks": []})

	def test_an_initial_draft_offers_continue_plan_to_the_planner_only(self):
		from kentender_procurement.procurement_planning.services import dpp_validation

		submitted = self.submitted()
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": submitted["current_version"]}, "entry_id")
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			classifications={entry_id: "Consulting services"},
		)
		result = self.load(fx.PLANNER)
		self.assertEqual(len(result["annual_plan"]["blocks"]), 1)
		block = result["annual_plan"]["blocks"][0]
		self.assertEqual(block["kind"], "current")
		self.assertEqual(block["version_status"], "Draft")
		self.assertEqual(block["version_number"], 1)
		self.assertEqual(block["funding_state"], "Not requested")
		self.assertEqual(block["action"], "Continue Plan")
		self.assertEqual(block["action_kind"], "primary")
		self.assertEqual(block["route"], ["annual-procurement-plan", frappe.db.get_value("Annual Plan", {"fiscal_year": fx.FY_OPEN}, "plan_reference")])
		# a non-Planner reader (e.g. the Auditor) sees the same facts but only a view link
		auditor_block = self.load(fx.AUDITOR)["annual_plan"]["blocks"][0]
		self.assertEqual(auditor_block["action"], "View")
		self.assertEqual(auditor_block["action_kind"], "secondary")

	def test_active_plus_a_draft_successor_is_two_blocks(self):
		"""U01-B — the Active block offers View (never a discretionary
		command over Active content) and the candidate block offers the
		Planner's own Continue update."""
		from kentender_procurement.procurement_planning.services import dpp_validation

		submitted = self.submitted()
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": submitted["current_version"]}, "entry_id")
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			classifications={entry_id: "Consulting services"},
		)
		frappe.db.set_value("Annual Plan Version", accepted["annual_plan_version"], "version_status", "Active")
		frappe.db.set_value("Annual Plan", accepted["annual_plan"], "active_version", accepted["annual_plan_version"])
		successor = frappe.copy_doc(frappe.get_doc("Annual Plan Version", accepted["annual_plan_version"]))
		successor.version_reference = f"{accepted['annual_plan']}-V2"
		successor.version_number = 2
		successor.version_status = "Draft"
		successor.based_on_version = accepted["annual_plan_version"]
		successor.insert(ignore_permissions=True)
		frappe.db.set_value("Annual Plan", accepted["annual_plan"], "open_successor_version", successor.name)

		result = self.load(fx.PLANNER)
		blocks = result["annual_plan"]["blocks"]
		self.assertEqual(len(blocks), 2)
		active_block, candidate_block = blocks
		self.assertEqual(active_block["kind"], "active")
		self.assertEqual(active_block["version_status"], "Active")
		self.assertEqual(active_block["action"], "View Active Plan")
		self.assertEqual(active_block["action_kind"], "secondary")
		self.assertEqual(candidate_block["kind"], "candidate")
		self.assertEqual(candidate_block["version_status"], "Draft")
		self.assertEqual(candidate_block["version_number"], 2)
		self.assertEqual(candidate_block["action"], "Continue update")
		self.assertEqual(candidate_block["action_kind"], "primary")

	def test_a_candidate_awaiting_a_decision_offers_no_card_button(self):
		"""U01-F — the decision lives on that actor's own governance task in
		Your actions, never a second button on the Annual Plan card."""
		from kentender_procurement.procurement_planning.services import dpp_validation

		submitted = self.submitted()
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": submitted["current_version"]}, "entry_id")
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			classifications={entry_id: "Consulting services"},
		)
		frappe.db.set_value("Annual Plan Version", accepted["annual_plan_version"], "version_status", "Awaiting Accounting Officer")
		result = self.load(fx.PLANNER)
		block = result["annual_plan"]["blocks"][0]
		self.assertEqual(block["version_status"], "Awaiting Accounting Officer")
		self.assertEqual(block["action"], "")
		self.assertEqual(block["action_kind"], "")
