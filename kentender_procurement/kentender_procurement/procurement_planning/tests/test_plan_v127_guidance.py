# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.27 — D2 readiness, guard reasons and the next-step
answer (§5.3.1, §5.6 item 4, §5.7, §14.12 PLN27-AC-001..010).

Run:
  bench --site kentender.midas.com run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_planning.tests.test_plan_v127_guidance
"""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import plan_finance, plan_read, plan_workbench, publication_pipeline, readiness
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_finance import PlanFinanceCase, key


def _report(plan_reference: str, stage: str = "pre_finance") -> dict:
	plan = frappe.get_doc("Annual Plan", {"plan_reference": plan_reference})
	version = frappe.get_doc("Annual Plan Version", plan.current_version) if plan.get("current_version") else None
	if version is None:
		name = frappe.db.get_value("Annual Plan Version", {"annual_plan": plan.name, "version_status": "Draft"}, "name")
		version = frappe.get_doc("Annual Plan Version", name)
	return plan_read.plan_readiness(version, plan, stage=stage)


def _codes(report: dict) -> list[tuple[str, str]]:
	return [(b["code"], b.get("field", "")) for b in report["blockers"]]


class TestD2PreFinanceReadiness(PlanFinanceCase):
	"""§5.6 item 4 (v1.27 D2): an over-budget line and a missing procurement
	method block Request plan funding confirmation; a selected method whose
	profile is missing or unverified blocks only Sign and submit."""

	def _without_method(self) -> tuple[dict, str]:
		accepted, item_id = self.accepted_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(procurement_method=""),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		return accepted, item_id

	def test_ac_002_a_missing_method_is_a_contents_gap_naming_the_purchase_not_a_missing_setting(self):
		accepted, item_id = self._without_method()
		report = _report(accepted["annual_plan"])
		self.assertIn(("PLN_PLAN_CONTENTS_INCOMPLETE", "procurement_method"), _codes(report))
		# The schedule cannot be calculated without a method, so it is not a
		# separate failure, and nothing blames a missing rule or setting.
		self.assertFalse([c for c in _codes(report) if c[0] in ("PLN_REFERENCE_UNAVAILABLE", "PLN_SCHEDULE_INVALID")])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.request(accepted["annual_plan"])
		self.assertEqual(caught.exception.code, "PLN_PLAN_CONTENTS_INCOMPLETE")
		self.assertIn(item_id, str(caught.exception))

	def test_ac_002_a_selected_method_with_a_missing_profile_blocks_only_signature(self):
		accepted, item_id = self.ready_item()
		missing = {"method": {"found": False}, "schedule": {"found": False}, "unresolved": ["method", "schedule"]}
		with patch.object(readiness, "method_profile_for", return_value=missing):
			pre = _report(accepted["annual_plan"])
			sub = _report(accepted["annual_plan"], stage="submission")
		self.assertEqual([c for c in _codes(pre) if c[0] in ("PLN_REFERENCE_UNAVAILABLE", "PLN_METHOD_NOT_ADMISSIBLE", "PLN_SCHEDULE_INVALID")], [])
		self.assertIn(("PLN_REFERENCE_UNAVAILABLE", "procurement_method"), _codes(sub))

	def test_ac_001_the_affordability_blocker_names_every_line_with_its_figures(self):
		accepted, item_id = self.ready_item(indicative_amount=150_000_000)
		report = _report(accepted["annual_plan"])
		over = next(b for b in report["blockers"] if b["code"] == "PLN_PLAN_NOT_AFFORDABLE")
		self.assertEqual(len(over["lines"]), 1)
		line = over["lines"][0]
		self.assertEqual(line["budget_line"], fx.BUDGET_LINE)
		self.assertTrue(line["title"])
		self.assertEqual(int(line["approved"]), 100_000_000)
		self.assertEqual(int(line["planned"]), 150_000_000)
		self.assertEqual(int(line["over"]), 50_000_000)
		# the plan-level blocker comes first, so the refusal names it (AC-001)
		self.assertEqual(report["blockers"][0]["code"], "PLN_PLAN_NOT_AFFORDABLE")

	def test_ac_001_over_budget_and_missing_method_are_reported_together(self):
		accepted, item_id = self.accepted_item(indicative_amount=150_000_000)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=fx.item_values(procurement_method=""),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		codes = [c[0] for c in _codes(_report(accepted["annual_plan"]))]
		self.assertIn("PLN_PLAN_NOT_AFFORDABLE", codes)
		self.assertIn("PLN_PLAN_CONTENTS_INCOMPLETE", codes)

	def test_a_budget_read_failure_is_an_explicit_blocker_never_silence(self):
		accepted, item_id = self.ready_item()
		with patch.object(plan_finance, "affordability_statement", side_effect=RuntimeError("budget down")):
			report = _report(accepted["annual_plan"])
		self.assertIn(("PLN_REFERENCE_UNAVAILABLE", "budget_basis"), _codes(report))


def _name(user: str) -> str:
	return frappe.db.get_value("User", user, "full_name") or user


def _nairobi_now_displays() -> set[str]:
	"""The wall-clock minute in Nairobi now, and the next one (a run may
	cross a minute boundary) — independent of the site's own timezone."""
	from datetime import datetime, timedelta, timezone
	from zoneinfo import ZoneInfo

	now = datetime.now(timezone.utc).astimezone(ZoneInfo("Africa/Nairobi"))
	return {f"{t.day} {t.strftime('%b %Y, %H:%M')} EAT" for t in (now, now + timedelta(minutes=1))}


class TestAnnualPlanNextStep(PlanFinanceCase):
	"""§5.7 first table / PLN27-AC-005, AC-009: the next-step answer and the
	journey for each viewer, from the same guards the commands use."""

	def read(self, plan_reference: str, user: str) -> dict:
		frappe.set_user(user)
		return plan_read.get_annual_plan(plan_reference=plan_reference)

	def stages(self, view: dict) -> dict[str, str]:
		return {s["code"]: s["marker"] for s in view["journey"]["stages"]}

	def test_a_ready_draft_is_the_planners_turn_and_everyone_else_waits_on_them(self):
		accepted, item_id = self.ready_item()
		view = self.read(accepted["annual_plan"], fx.PLANNER)
		self.assertEqual(view["next_step"]["kind"], "your_turn")
		self.assertEqual(view["next_step"]["headline"], "Send the plan to Finance for funding review")
		self.assertTrue(view["can_request_funding"])
		self.assertEqual(self.stages(view)["preparation"], "current")
		self.assertEqual(self.stages(view)["funding"], "not_started")
		self.assertEqual(len(view["journey"]["stages"]), 7)
		# the upstream link names the accepted requirements behind the plan
		self.assertEqual(view["journey"]["upstream"]["label"], "1 departmental requirement included")

		finance = self.read(accepted["annual_plan"], fx.FINANCE_OFFICER)
		self.assertEqual(finance["next_step"]["kind"], "waiting")
		self.assertIn(_name(fx.PLANNER), finance["next_step"]["holder"]["people"])
		self.assertEqual(finance["next_step"]["holder"]["role"], "Procurement Planner")

		auditor = self.read(accepted["annual_plan"], fx.AUDITOR)
		self.assertEqual(auditor["next_step"]["kind"], "not_involved")
		self.assertEqual(auditor["journey"]["current"], "preparation")

	def test_ac_009_a_technical_reader_never_gets_a_turn_or_a_fix(self):
		accepted, item_id = self.ready_item(indicative_amount=150_000_000)
		view = self.read(accepted["annual_plan"], "Administrator")
		self.assertNotIn(view["next_step"]["kind"], ("your_turn", "your_turn_blocked"))
		self.assertEqual(view["next_step"]["fixes"], [])
		self.assertEqual(view["next_step"]["primary_action"], "")

	def test_an_over_budget_draft_offers_the_budget_and_the_departmental_recovery_paths(self):
		# Owner decision 26 Sep 2026: a purchase's cost is copied from the
		# departments' accepted requirements and cannot be lowered in the plan,
		# so "Reduce a purchase" (found live: the editor locks the amount) is
		# not offered. The two recovery paths are a budget revision and an
		# update of the departmental plan behind the line.
		accepted, item_id = self.ready_item(indicative_amount=150_000_000)
		view = self.read(accepted["annual_plan"], fx.PLANNER)
		step = view["next_step"]
		self.assertEqual(step["kind"], "your_turn_blocked")
		self.assertTrue(step["headline"].startswith("Over budget by KES 50,000,000 on "))
		self.assertEqual(
			step["sentence"],
			"Purchase costs come from the departments' accepted requirements and cannot be lowered in the plan. "
			"You can request the funding check once the line's approved amount covers them.",
		)
		self.assertEqual([f["fix_id"] for f in step["fixes"]], ["request_budget_revision", "request_departmental_update"])
		self.assertEqual(step["fixes"][0]["responsibility"], "Budget Officer")
		self.assertTrue(step["fixes"][0]["primary"])
		department = step["fixes"][1]
		self.assertEqual(department["label"], f"Request departmental plan update from {fx.OU_ALPHA_NAME}")
		self.assertEqual(department["target"], {"budget_line": fx.BUDGET_LINE, "organisation_unit": fx.OU_ALPHA})
		self.assertFalse(department["primary"])
		facts = {f["label"]: f["value"] for f in step["blockers"][0]["facts"]}
		self.assertEqual(facts["Requirements on this line"], fx.OU_ALPHA_NAME)
		self.assertFalse(view["can_request_funding"])
		self.assertEqual(self.stages(view)["preparation"], "blocked")
		# budget fit: the live comparison, never "not yet checked"
		fit = view["budget_fit"]
		self.assertFalse(fit["all_within"])
		self.assertEqual(fit["result"], "Over by KES 50,000,000 on one budget line")
		self.assertEqual([r["difference_display"] for r in fit["lines"] if r["over"]], ["Over by KES 50,000,000"])
		self.assertEqual(view["finance_confirmation"]["state"], "Not requested")

	def test_a_missing_method_blocks_with_the_board_wording(self):
		accepted, item_id = self.accepted_item()
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(plan_item=item_id, values=fx.item_values(procurement_method=""), expected_record_version=item["record_version"], idempotency_key=key())
		step = self.read(accepted["annual_plan"], fx.PLANNER)["next_step"]
		self.assertEqual(step["headline"], "1 purchase needs a procurement method")
		self.assertEqual(step["sentence"], "You can request the funding check once a method is chosen.")
		self.assertEqual(step["fixes"][0]["target"], ["procurement-plan-item", item_id])

	def test_a_time_written_by_a_planning_command_reads_as_the_nairobi_clock(self):
		# FU-V127-01, owner decision 26 Sep 2026: every module stores times in
		# the site timezone (Frappe's own rule) and shows them as stored. The
		# funding request's Finance task is written by a command, now; the
		# Planner's "since" must be Nairobi's wall clock, not three hours on.
		accepted, item_id = self.ready_item()
		self.request(accepted["annual_plan"])
		step = self.read(accepted["annual_plan"], fx.PLANNER)["next_step"]
		self.assertEqual(step["kind"], "waiting")
		self.assertIn(step["since"]["display"], _nairobi_now_displays())

	def test_the_funding_request_moves_the_turn_to_finance_and_confirmation_to_the_signer(self):
		accepted, item_id = self.ready_item()
		self.request(accepted["annual_plan"])
		planner = self.read(accepted["annual_plan"], fx.PLANNER)
		self.assertEqual(planner["next_step"]["kind"], "waiting")
		self.assertIn("to confirm plan funding", planner["next_step"]["headline"])
		self.assertTrue(planner["next_step"]["since"]["display"].endswith("EAT"))
		self.assertEqual(planner["finance_confirmation"]["state"], "Awaiting confirmation")
		self.assertEqual(self.stages(planner)["funding"], "current")
		self.assertEqual(self.stages(planner)["preparation"], "done")
		finance = self.read(accepted["annual_plan"], fx.FINANCE_OFFICER)
		self.assertEqual(finance["next_step"]["kind"], "your_turn")
		self.assertEqual(finance["next_step"]["headline"], "Confirm plan funding or return the plan to the planner")

		task = frappe.get_doc("Plan Finance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"})
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		hopf = self.read(accepted["annual_plan"], fx.HOPF)
		self.assertEqual(hopf["finance_confirmation"]["state"], "Confirmed")
		self.assertTrue(hopf["finance_confirmation"]["checked_by"])
		self.assertEqual(self.stages(hopf)["signature"], hopf["next_step"]["kind"] == "your_turn" and "current" or "blocked")
		planner = self.read(accepted["annual_plan"], fx.PLANNER)
		self.assertEqual(planner["next_step"]["kind"], "waiting")
		self.assertEqual(planner["next_step"]["stage"], "signature")


class TestDepartmentalPlanNextStep(PlanFinanceCase):
	"""§5.7 second table, §10.1A.2, §10.5: the DPP journey from preparation to
	acceptance, as each actor reads it."""

	def test_the_dpp_journey_from_certification_to_acceptance(self):
		from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_read, dpp_validation

		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(), expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		reference = opened["dpp_reference"]

		# complete content: the Head of Department's to certify
		author = dpp_read.get_departmental_plan(dpp_reference=reference)
		self.assertEqual(author["next_step"]["kind"], "waiting")
		self.assertIn("to certify and submit the departmental plan", author["next_step"]["headline"])
		# the Head of Department by name, not only the role (found in the
		# named-user pass 26 Sep 2026: the holder lookup matched no one)
		self.assertIn(_name(fx.HOD), author["next_step"]["holder"]["people"])
		self.assertIn(_name(fx.HOD), author["journey"]["reduced_text"])
		self.assertTrue(author["journey"]["reduced"])
		self.assertEqual(author["journey"]["current"], "certification")
		frappe.set_user(fx.HOD)
		hod = dpp_read.get_departmental_plan(dpp_reference=reference)
		self.assertEqual(hod["next_step"]["headline"], "Certify and submit the departmental plan")
		self.assertFalse(hod["journey"]["reduced"])
		self.assertEqual([s["marker"] for s in hod["journey"]["stages"]], ["done", "current", "not_started", "not_started"])

		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=key(),
		)
		hod = dpp_read.get_departmental_plan(dpp_reference=reference)
		self.assertEqual(hod["next_step"]["kind"], "waiting")
		self.assertIn("to review the submission", hod["next_step"]["headline"])
		self.assertTrue(hod["next_step"]["since"])
		self.assertEqual(hod["journey"]["current"], "review")

		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		review = dpp_read.get_dpp_validation_task(task=task.name)
		self.assertEqual(review["next_step"]["headline"], "Classify every included requirement, then accept or return the submission")
		self.assertEqual(review["journey"]["current"], "review")
		dpp_validation.accept_departmental_plan(task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=key())

		decided = dpp_read.get_dpp_validation_task(task=task.name)
		self.assertEqual(decided["next_step"]["kind"], "done")
		self.assertTrue(decided["next_step"]["headline"].startswith(f"Accepted by {_name(fx.PLANNER)} on "))
		self.assertTrue(all(s["marker"] == "done" for s in decided["journey"]["stages"]))
		frappe.set_user(fx.HOD)
		accepted = dpp_read.get_departmental_plan(dpp_reference=reference)
		self.assertEqual(accepted["next_step"]["kind"], "done")

	def test_an_auditor_is_not_involved_and_a_technical_reader_gets_no_turn(self):
		from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_read

		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS)
		frappe.set_user(fx.AUDITOR)
		self.assertEqual(dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])["next_step"]["kind"], "not_involved")
		frappe.set_user("Administrator")
		technical = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])["next_step"]
		self.assertNotIn(technical["kind"], ("your_turn", "your_turn_blocked"))
		self.assertEqual(technical["fixes"], [])


class TestBudgetRevisionHandOff(PlanFinanceCase):
	"""PLN27-AC-006/008, §7.7 row RequestBudgetRevision, BUD-CHG-001 v1.11
	§8.5 — both sides of the hand-off in one transaction, and each outcome
	reported back idempotently and in order."""

	def over_budget(self) -> tuple[dict, dict]:
		accepted, item_id = self.ready_item(indicative_amount=150_000_000)
		frappe.set_user(fx.PLANNER)
		return accepted, plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])

	def ask(self, plan: dict, *, idem: str | None = None) -> dict:
		from kentender_procurement.procurement_planning.services import budget_revision

		frappe.set_user(fx.PLANNER)
		return budget_revision.request_budget_revision(
			plan_version=plan["version_reference"], budget_line=fx.BUDGET_LINE,
			expected_record_version=plan["record_version"], idempotency_key=idem or key(),
		)

	def test_ac_006_one_request_on_each_side_and_the_planner_now_waits(self):
		accepted, plan = self.over_budget()
		result = self.ask(plan)
		self.assertEqual(result["action"], "requested")
		mine = frappe.get_doc("Plan Budget Revision Request", result["request"])
		self.assertEqual(mine.status, "Open")
		self.assertEqual(int(mine.over_amount), 50_000_000)
		theirs = frappe.get_doc("Budget Revision Request", {"planning_request_id": mine.name})
		self.assertEqual(theirs.status, "Open")
		self.assertEqual(int(theirs.approved_amount_at_receipt), 100_000_000)
		self.assertEqual(theirs.budget_revision_request_id, mine.bud_request_reference)
		# no Budget amount, no Plan state change
		after = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(after["record_version"], plan["record_version"])
		self.assertEqual(after["next_step"]["kind"], "waiting")
		self.assertEqual(after["next_step"]["headline"], f"Waiting for {_name(fx.BUDGET_OFFICER)} (Budget Officer) to revise the budget line".replace(_name(fx.BUDGET_OFFICER), after["next_step"]["holder"]["display"].split(" (")[0]))
		self.assertIn(_name(fx.BUDGET_OFFICER), after["next_step"]["holder"]["people"])
		# §3 — "since" is the real Nairobi time of the request, stored as a
		# UTC instant (PLN §4 Dates/instants); found live 25 Sep 2026 three
		# hours ahead because the local clock was converted a second time.
		self.assertIn(after["next_step"]["since"]["display"], _nairobi_now_displays())
		self.assertEqual(after["journey"]["stages"][0]["marker"], "blocked")
		# Every other reader sees where it stands: with the Budget Officer, not
		# "waiting for the Planner to prepare" (found live 25 Sep 2026).
		technical = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"], user="Administrator")["next_step"]
		self.assertEqual(technical["kind"], "waiting")
		self.assertTrue(technical["headline"].endswith("(Budget Officer) to revise the budget line"))

	def test_the_budget_officer_reading_the_plan_is_sent_to_budget_not_told_to_wait_for_themselves(self):
		# Found live 25 Sep 2026: Josphat Mwangi (Finance Confirmation Officer
		# and Budget Officer) opened the waiting update and read "Waiting for
		# Josphat Mwangi (Budget Officer) to revise the budget line", beside a
		# tracker naming Mercy as the holder of the blocked stage.
		accepted, plan = self.over_budget()
		self.ask(plan)
		officer = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"], user=fx.FINANCE_BUDGET)
		step = officer["next_step"]
		self.assertEqual(step["kind"], "your_turn")
		self.assertTrue(step["headline"].startswith("Revise ") and step["headline"].endswith(" for the plan update"), step["headline"])
		route = [f for f in step["fixes"] if f["kind"] == "route"]
		self.assertEqual(len(route), 1)
		self.assertEqual(route[0]["target"], ["budget-funding", {"fiscal_year": officer["fiscal_year"]}])
		self.assertEqual(officer["journey"]["current"], step["stage"])
		# The tracker names who holds the blocked stage now — the Budget
		# Officers the line waits on — for every reader, not the Planner.
		for user in (fx.PLANNER, fx.FINANCE_BUDGET):
			holder = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"], user=user)["journey"]["stages"][0]["holder"]
			self.assertIn(_name(fx.BUDGET_OFFICER), holder)
			self.assertNotIn(_name(fx.PLANNER), holder)

	def test_ac_006_a_second_request_is_refused_and_a_replay_returns_the_first(self):
		accepted, plan = self.over_budget()
		idem = key()
		first = self.ask(plan, idem=idem)
		self.assertEqual(self.ask(plan, idem=idem)["request"], first["request"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.ask(plan)
		self.assertEqual(caught.exception.code, "PLN_BUDGET_REVISION_ALREADY_REQUESTED")
		self.assertEqual(frappe.db.count("Budget Revision Request", {"planning_request_id": first["request"]}), 1)

	def test_ac_006_a_line_within_its_approved_amount_needs_no_revision(self):
		accepted, item_id = self.ready_item()
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.ask(plan)
		self.assertEqual(caught.exception.code, "PLN_BUDGET_REVISION_NOT_REQUIRED")

	def test_ac_008_a_decline_reaches_planning_and_the_request_fix_returns(self):
		from kentender_budget.services import budget_revision_request_contracts as bud

		accepted, plan = self.over_budget()
		result = self.ask(plan)
		frappe.set_user(fx.BUDGET_OFFICER)
		theirs = frappe.db.get_value("Budget Revision Request", {"planning_request_id": result["request"]}, "name")
		short = bud.decline_budget_revision_request({"budget_revision_request": theirs, "reason": "short"})
		self.assertFalse(short["ok"])
		declined = bud.decline_budget_revision_request({"budget_revision_request": theirs, "reason": "No further allocation is available this year."})
		self.assertTrue(declined["ok"])
		event = frappe.get_doc("Budget Revision Request Event", {"budget_revision_request": theirs})
		self.assertEqual(event.status, "Delivered")
		# BUD v1.11 §6 — an instant crossing the contract is ISO-8601 UTC.
		decided_at = frappe.parse_json(event.payload)["decided_at"]
		self.assertRegex(decided_at, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
		mine = frappe.get_doc("Plan Budget Revision Request", result["request"])
		self.assertEqual(mine.status, "Declined")
		# stored in site time (owner decision 26 Sep 2026), the same instant
		from kentender_core.utils.instants import to_utc_iso

		self.assertEqual(to_utc_iso(mine.outcome_at), decided_at)
		self.assertEqual(mine.outcome_reason, "No further allocation is available this year.")
		frappe.set_user(fx.PLANNER)
		step = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["next_step"]
		self.assertEqual(step["kind"], "your_turn_blocked")
		self.assertEqual([f["fix_id"] for f in step["fixes"]], ["request_departmental_update"])
		# a closed request cannot be declined again
		frappe.set_user(fx.BUDGET_OFFICER)
		self.assertEqual(bud.decline_budget_revision_request({"budget_revision_request": theirs, "reason": "Second decline attempt."})["code"], "BUDGET_REVISION_REQUEST_CLOSED")

	def test_after_a_decline_the_planner_is_told_who_declined_it_when_and_why(self):
		# Found live 25 Sep 2026: once Josphat Mwangi declined, Mercy's plan
		# read exactly as before she asked — the decline and its reason were
		# nowhere on the plan or the workspace.
		from kentender_budget.services import budget_revision_request_contracts as bud
		from kentender_procurement.procurement_planning.services import my_work_provider, workspace
		from kentender_procurement.procurement_planning.services import next_step as plan_next_step

		accepted, plan = self.over_budget()
		result = self.ask(plan)
		frappe.set_user(fx.BUDGET_OFFICER)
		theirs = frappe.db.get_value("Budget Revision Request", {"planning_request_id": result["request"]}, "name")
		bud.decline_budget_revision_request({"budget_revision_request": theirs, "reason": "No further allocation is available this year."})
		when = plan_next_step._since(frappe.db.get_value("Plan Budget Revision Request", result["request"], "outcome_at"))["display"]

		frappe.set_user(fx.PLANNER)
		step = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["next_step"]
		self.assertEqual(step["kind"], "your_turn_blocked")
		over = next(b for b in step["blockers"] if b["reason_code"] == "PLN_PLAN_NOT_AFFORDABLE")
		facts = {f["label"]: f["value"] for f in over["facts"]}
		self.assertEqual(facts["Budget revision"], f"Declined by {_name(fx.BUDGET_OFFICER)} on {when}")
		self.assertEqual(facts["Reason"], "No further allocation is available this year.")
		# Owner decision 26 Sep 2026: after a decline the departmental path
		# leads, and a budget request on the same amounts is neither offered
		# nor accepted — no endless "ask again".
		self.assertEqual([f["fix_id"] for f in over["fixes"]], ["request_departmental_update"])
		self.assertTrue(over["fixes"][0]["primary"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.ask(plan_read.get_annual_plan(plan_reference=accepted["annual_plan"]))
		self.assertEqual(caught.exception.code, "PLN_BUDGET_REVISION_ALREADY_DECLINED")
		# The workspace row and the My Work item say it too, at the decline's time.
		self.assertEqual(workspace._narrative(step)["detail"], f"Budget revision declined by {_name(fx.BUDGET_OFFICER)}: No further allocation is available this year.")
		item = [r for r in my_work_provider.my_work_rows(user=fx.PLANNER)["assigned"] if r["task_type"] == "planning.budget_outcome" and r["reference"].startswith(accepted["annual_plan"])]
		self.assertEqual(len(item), 1)
		self.assertIn("No further allocation is available this year.", item[0]["stage"])
		self.assertEqual(item[0]["received_at"], when)
		# A new basis (here the planned amount changes; fixture-only override)
		# makes a fresh request possible again, and asking replaces the
		# explanation with the wait.
		for name in frappe.get_all("Plan Source Allocation", filters={"plan_version": accepted["annual_plan_version"]}, pluck="name"):
			frappe.db.set_value("Plan Source Allocation", name, "indicative_amount", 140_000_000, update_modified=False)
		renewed = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		fixes = {f["fix_id"]: f for f in renewed["next_step"]["fixes"]}
		self.assertTrue(fixes["request_budget_revision"]["label"].startswith("Request budget revision again from "), fixes["request_budget_revision"]["label"])
		self.assertTrue(fixes["request_departmental_update"]["primary"])
		self.ask(renewed)
		again = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["next_step"]
		self.assertEqual(again["kind"], "waiting")

	def test_ac_008_outcomes_apply_once_and_in_order(self):
		from kentender_procurement.procurement_planning.services import budget_revision

		accepted, plan = self.over_budget()
		result = self.ask(plan)
		budget_revision.receive_budget_revision_outcome({"planning_request_id": result["request"], "outcome": "Revised", "sequence": 2, "decided_by": "x"})
		budget_revision.receive_budget_revision_outcome({"planning_request_id": result["request"], "outcome": "Declined", "sequence": 1, "decided_by": "x"})
		budget_revision.receive_budget_revision_outcome({"planning_request_id": result["request"], "outcome": "Revised", "sequence": 2, "decided_by": "x"})
		mine = frappe.get_doc("Plan Budget Revision Request", result["request"])
		self.assertEqual(mine.status, "Revised")
		self.assertEqual(mine.outcome_sequence, 2)

	def test_bud_br_029_activating_a_changed_line_marks_the_request_revised(self):
		from kentender_budget.services import budget_revision_request_contracts as bud

		accepted, plan = self.over_budget()
		result = self.ask(plan)
		theirs = frappe.get_doc("Budget Revision Request", {"planning_request_id": result["request"]})
		line_version = theirs.budget_line_version_at_receipt
		version = frappe.db.get_value("Procurement Budget Line Version", line_version, "budget_version")
		before = frappe.db.get_value("Procurement Budget Line Version", line_version, "approved_amount")
		frappe.db.set_value("Procurement Budget Line Version", line_version, "approved_amount", 160_000_000, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Procurement Budget Line Version", line_version, "approved_amount", before, update_modified=False)
		frappe.set_user("Administrator")
		revised = bud.revise_on_activation(frappe.get_doc("Procurement Budget Version", version))
		self.assertEqual(revised, [theirs.budget_revision_request_id])
		self.assertEqual(frappe.db.get_value("Plan Budget Revision Request", result["request"], "status"), "Revised")

	def test_only_the_planning_principal_may_send_a_request(self):
		from kentender_budget.api import budget_api

		frappe.set_user("Administrator")
		with self.assertRaises(frappe.PermissionError):
			budget_api.receive_budget_revision_request({"planning_request_id": "X", "budget_line": fx.BUDGET_LINE})

	def test_sending_a_now_fitting_plan_to_finance_withdraws_the_moot_request(self):
		accepted, plan = self.over_budget()
		result = self.ask(plan)
		theirs = frappe.get_doc("Budget Revision Request", {"planning_request_id": result["request"]})
		line_version = theirs.budget_line_version_at_receipt
		before = frappe.db.get_value("Procurement Budget Line Version", line_version, "approved_amount")
		frappe.db.set_value("Procurement Budget Line Version", line_version, "approved_amount", 160_000_000, update_modified=False)
		self.addCleanup(frappe.db.set_value, "Procurement Budget Line Version", line_version, "approved_amount", before, update_modified=False)
		self.request(accepted["annual_plan"])
		self.assertEqual(frappe.db.get_value("Budget Revision Request", theirs.name, "status"), "Withdrawn")
		self.assertEqual(frappe.db.get_value("Plan Budget Revision Request", result["request"], "status"), "Withdrawn")


class TestDepartmentalUpdateRoute(PlanFinanceCase):
	"""Owner decision 26 Sep 2026 — the departmental correction route for an
	over-budget line: the Planner asks the department, the department decides
	in an update of its accepted plan (here it corrects the estimate), and
	the Planner rebuilds the purchase from the new accepted source."""

	def over_budget(self) -> tuple[dict, dict]:
		accepted, item_id = self.ready_item(indicative_amount=150_000_000)
		frappe.set_user(fx.PLANNER)
		return accepted, plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])

	def ask_department(self, plan: dict) -> dict:
		from kentender_procurement.procurement_planning.services import departmental_update

		frappe.set_user(fx.PLANNER)
		return departmental_update.request_departmental_plan_update(
			plan_version=plan["version_reference"], budget_line=fx.BUDGET_LINE, organisation_unit=fx.OU_ALPHA,
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)

	def test_the_department_updates_its_plan_and_the_planner_rebuilds_the_purchase(self):
		from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_read, dpp_validation, my_work_provider

		accepted, plan = self.over_budget()
		result = self.ask_department(plan)
		self.assertEqual(result["action"], "requested")
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.ask_department(plan_read.get_annual_plan(plan_reference=accepted["annual_plan"]))
		self.assertEqual(caught.exception.code, "PLN_DEPARTMENTAL_UPDATE_ALREADY_REQUESTED")

		# The Planner waits on the named department, and so does the tracker.
		mine = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(mine["next_step"]["kind"], "waiting")
		self.assertEqual(mine["next_step"]["headline"], f"Waiting for {fx.OU_ALPHA_NAME} to update its departmental plan")
		self.assertTrue(mine["next_step"]["since"])
		self.assertEqual(mine["journey"]["stages"][0]["holder"], fx.OU_ALPHA_NAME)
		waits = [r for r in my_work_provider.my_work_rows(user=fx.PLANNER)["waiting"] if r["reference"].startswith(accepted["annual_plan"])]
		self.assertEqual([r["title"] for r in waits], ["Waiting for the departmental plan update"])

		# The department is told what was asked, in My Work and on its plan.
		for user in (fx.AUTHOR, fx.HOD):
			rows = [r for r in my_work_provider.my_work_rows(user=user)["assigned"] if r["task_id"] == result["request"]]
			self.assertEqual(len(rows), 1, user)
			self.assertIn("over budget by KES 50,000,000", rows[0]["stage"])
		frappe.set_user(fx.AUTHOR)
		dpp = dpp_read.get_departmental_plan(dpp_reference=accepted["dpp_reference"])
		self.assertEqual((dpp["next_step"]["kind"], dpp["next_step"]["headline"]), ("your_turn", "Update this plan as Procurement asked"))
		self.assertIn("is over by KES 50,000,000", dpp["update_request_notice"]["text"])
		self.assertTrue(dpp["update_request_notice"]["asked"].startswith(f"Asked by {_name(fx.PLANNER)} on "))
		self.assertTrue(dpp["can_create_update"])

		# The department corrects the estimate in an update; Procurement accepts it.
		entry_id = frappe.db.get_value("Departmental Plan Entry", frappe.get_all("Plan Source Allocation", filters={"plan_version": accepted["annual_plan_version"]}, pluck="dpp_entry")[0], "entry_id")
		root = frappe.db.get_value("Departmental Plan", {"dpp_reference": accepted["dpp_reference"]})
		frappe.set_user(fx.HOD)
		update = dpp_lifecycle.create_departmental_plan_update(
			departmental_plan=root, expected_record_version=frappe.db.get_value("Departmental Plan", root, "record_version"), idempotency_key=key(),
		)
		changed = dpp_lifecycle.save_direct_requirement(
			dpp_version=update["current_version"], entry_id=entry_id, values=fx.direct_values(indicative_amount=90_000_000),
			expected_record_version=update["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.AUTHOR)
		self.assertIsNotNone(dpp_read.get_departmental_plan(dpp_reference=accepted["dpp_reference"])["update_request_notice"])
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=update["current_version"], certification_confirmed=True,
			expected_record_version=changed["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(task=task.name, classifications={entry_id: "Goods"}, task_token=task.task_token, idempotency_key=key())

		self.assertEqual(frappe.db.get_value("Departmental Plan Update Request", result["request"], "status"), "Answered")
		for user in (fx.AUTHOR, fx.HOD):
			self.assertEqual([r for r in my_work_provider.my_work_rows(user=user)["assigned"] if r["task_id"] == result["request"]], [], user)

		# The Planner rebuilds the purchase from the new accepted source.
		frappe.set_user(fx.PLANNER)
		stale = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(stale["next_step"]["kind"], "your_turn_blocked")
		blockers = {b["reason_code"]: b for b in stale["next_step"]["blockers"]}
		# The purchase is named with why it needs rebuilding (found in the
		# named-user pass 26 Sep 2026: "…after a source correction for 1 purchase").
		rebuild = blockers["PLN_SOURCE_CORRECTION_REQUIRED"]
		title = stale["plan_items"][0]["title"]
		self.assertEqual(rebuild["headline"], f"Rebuild {title} from the department's updated plan")
		self.assertEqual([f["fix_id"] for f in rebuild["fixes"]], ["edit_purchase"])
		self.assertTrue(rebuild["fixes"][0]["primary"])
		# Until then the line's total is stale: no request is offered on it
		# (the department just answered), only the order of work.
		over = blockers["PLN_PLAN_NOT_AFFORDABLE"]
		self.assertEqual([f["kind"] for f in over["fixes"]], ["text"])
		self.assertEqual(over["fixes"][0]["label"], "Rebuild the purchase first: the department's update changes this line's total")
		item_id = stale["plan_items"][0]["plan_item_id"]
		plan_workbench.dissolve_plan_item(plan_item=item_id, expected_record_version=stale["record_version"], idempotency_key=key())
		refreshed = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[refreshed["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=refreshed["record_version"], idempotency_key=key(),
		)
		item = plan_read.get_plan_item(plan_item_id=formed["created_items"][0])
		plan_workbench.save_plan_item(plan_item=formed["created_items"][0], values=fx.item_values(), expected_record_version=item["record_version"], idempotency_key=key())
		ready = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(ready["next_step"]["kind"], "your_turn", ready["next_step"])
		self.assertTrue(ready["budget_fit"]["all_within"])

	def test_sending_the_plan_to_finance_withdraws_an_open_departmental_request(self):
		accepted, plan = self.over_budget()
		result = self.ask_department(plan)
		for name in frappe.get_all("Plan Source Allocation", filters={"plan_version": accepted["annual_plan_version"]}, pluck="name"):
			frappe.db.set_value("Plan Source Allocation", name, "indicative_amount", 1_000_000, update_modified=False)
		self.request(accepted["annual_plan"])
		self.assertEqual(frappe.db.get_value("Departmental Plan Update Request", result["request"], "status"), "Withdrawn")


class TestHandOffRegister(PlanFinanceCase):
	"""PLN27-AC-007 — every §7.7 row puts the next holder's item and the
	sender's waiting-on item in My Work with the event, and clears each only
	on its stated state change."""

	def rows(self, user: str, bucket: str, kind: str | None = None) -> list[dict]:
		"""This test's own rows only: the fixture roles are site-wide, so the
		live dev site's plans (e.g. a real update waiting on the Budget
		Officer) reach the same My Work and are not this test's to count."""
		from kentender_procurement.procurement_planning.services import my_work_provider

		out = my_work_provider.my_work_rows(user=user)[bucket]
		tokens = self.scope_tokens()
		mine = [r for r in out if any(t in frappe.as_json(r) for t in tokens)]
		return [r for r in mine if kind is None or r["task_type"] == kind or r["title"] == kind]

	def scope_tokens(self) -> list[str]:
		"""The plan's reference, plus its task records (a Finance or
		signature item names only its task)."""
		if not self.scope:
			return []
		versions = frappe.get_all("Annual Plan Version", filters={"annual_plan": self.scope}, pluck="name")
		tasks = []
		for doctype in ("Plan Finance Task", "Plan Governance Task"):
			for task in frappe.get_all(doctype, filters={"plan_version": ["in", versions or [""]]}, fields=["name", "task_reference"]):
				tasks += [task.name, task.task_reference]
		return [self.scope, *[t for t in tasks if t]]

	scope = ""

	def ready_item(self, *args, **kwargs):
		accepted, item_id = super().ready_item(*args, **kwargs)
		self.scope = accepted["annual_plan"]
		return accepted, item_id

	def test_funding_request_confirmation_and_signature_hand_offs(self):
		accepted, item_id = self.ready_item()
		self.assertEqual(self.rows(fx.PLANNER, "waiting"), [])
		self.request(accepted["annual_plan"])
		waiting = self.rows(fx.PLANNER, "waiting", "Waiting for Finance")
		self.assertEqual(len(waiting), 1)
		self.assertIn(_name(fx.FINANCE_OFFICER), waiting[0]["holder"]["people"])
		self.assertTrue(waiting[0]["since"])
		self.assertEqual(len(self.rows(fx.FINANCE_OFFICER, "assigned", "planning.finance")), 1)
		# Every row's Received reads as a time, never a raw timestamp (found in
		# the named-user pass 26 Sep 2026: "2026-09-26 01:19:03.296127").
		for row in self.rows(fx.FINANCE_OFFICER, "assigned") + self.rows(fx.PLANNER, "waiting"):
			self.assertRegex(row["received_at"], r"^\d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2} EAT$", row)

		task = frappe.get_doc("Plan Finance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"})
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		# Finance's item cleared on the decision; the signer now holds the plan
		self.assertEqual(self.rows(fx.FINANCE_OFFICER, "assigned", "planning.finance"), [])
		self.assertEqual(self.rows(fx.PLANNER, "waiting", "Waiting for Finance"), [])
		signer = self.rows(fx.HOPF, "assigned", "planning.sign")
		planner_waits = self.rows(fx.PLANNER, "waiting", "Waiting for signature")
		frappe.set_user(fx.HOPF)
		hopf_step = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])["next_step"]
		if hopf_step["kind"] == "your_turn":
			# every submission gate passes: the signer's item and the Planner's wait
			self.assertEqual([r["title"] for r in signer], ["Sign and submit the annual plan"])
			self.assertEqual(len(planner_waits), 1)
		else:
			# a submission gate fails in this world: no signing item is offered,
			# and the answer names what blocks it (never a silent dead end)
			self.assertEqual(signer, [])
			self.assertEqual(hopf_step["stage"], "signature")
			self.assertTrue(hopf_step["headline"])

	def test_finance_return_is_the_planners_item_with_the_reason(self):
		accepted, item_id = self.ready_item()
		self.request(accepted["annual_plan"])
		task = frappe.get_doc("Plan Finance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"})
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.return_from_finance(task=task.name, task_token=task.task_token, reason="Split the laptops across two lines before resubmitting.", idempotency_key=key())
		row = self.rows(fx.PLANNER, "assigned", "planning.finance_return")
		self.assertEqual(len(row), 1)
		self.assertEqual(row[0]["title"], "Correct the plan returned by Finance")
		self.assertIn("Split the laptops", row[0]["stage"])
		self.request(accepted["annual_plan"])
		self.assertEqual(self.rows(fx.PLANNER, "assigned", "planning.finance_return"), [])

	def test_budget_revision_request_and_its_outcome(self):
		from kentender_budget.services import budget_my_work_provider
		from kentender_budget.services import budget_revision_request_contracts as bud
		from kentender_procurement.procurement_planning.services import budget_revision

		accepted, item_id = self.ready_item(indicative_amount=150_000_000)
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		result = budget_revision.request_budget_revision(plan_version=plan["version_reference"], budget_line=fx.BUDGET_LINE, expected_record_version=plan["record_version"], idempotency_key=key())
		waits = self.rows(fx.PLANNER, "waiting", "Waiting for the budget revision")
		self.assertEqual(len(waits), 1)
		# The My Work page's own columns (found in the browser 25 Sep 2026):
		# the year shows, the stage names the stage (the holder line already
		# says who and since when), and "received" is when it started waiting.
		self.assertEqual(waits[0]["financial_year"], waits[0]["fiscal_year"])
		self.assertTrue(waits[0]["financial_year"])
		self.assertEqual(waits[0]["stage"], "Preparation")
		self.assertEqual(waits[0]["received_at"], waits[0]["since"]["display"])
		officer = [
			r for r in budget_my_work_provider.my_work_rows(user=fx.BUDGET_OFFICER)["assigned"]
			if r["task_type"] == "budget.revision_request"
			and r["reference"] == frappe.db.get_value("Plan Budget Revision Request", result["request"], "bud_request_reference")
		]
		self.assertEqual(len(officer), 1)
		self.assertTrue(officer[0]["title"].startswith("Revise "))
		self.assertIn("50,000,000", officer[0]["stage"])

		theirs = frappe.db.get_value("Budget Revision Request", {"planning_request_id": result["request"]}, "name")
		frappe.set_user(fx.BUDGET_OFFICER)
		bud.decline_budget_revision_request({"budget_revision_request": theirs, "reason": "No further allocation is available this year."})
		# both sides clear on the outcome; the Planner's item names it
		self.assertEqual([r for r in budget_my_work_provider.my_work_rows(user=fx.BUDGET_OFFICER)["assigned"] if r["reference"] == officer[0]["reference"]], [])
		self.assertEqual(self.rows(fx.PLANNER, "waiting", "Waiting for the budget revision"), [])
		cont = self.rows(fx.PLANNER, "assigned", "planning.budget_outcome")
		self.assertEqual(len(cont), 1)
		self.assertEqual(cont[0]["title"], "Continue plan update")

		self.assertIn("declined", cont[0]["stage"])

	def test_dpp_hand_offs_to_procurement_review_and_back(self):
		from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation

		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS)
		self.scope = opened["dpp_reference"]
		added = dpp_lifecycle.save_direct_requirement(dpp_version=opened["current_version"], values=fx.direct_values(), expected_record_version=opened["record_version"], idempotency_key=key())
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=key())
		self.assertEqual(len(self.rows(fx.HOD, "waiting", "Waiting for Procurement review")), 1)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		dpp_validation.return_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=key(),
			issues=[{"dpp_entry_id": None, "correction_required": "Add the delivery location to every requirement."}],
		)
		self.assertEqual(self.rows(fx.HOD, "waiting", "Waiting for Procurement review"), [])
		for user in (fx.HOD, fx.AUTHOR):
			row = self.rows(user, "assigned", "planning.dpp_return")
			self.assertEqual(len(row), 1, user)
			self.assertIn("Add the delivery location", row[0]["stage"])


class TestFinanceTaskNextStep(PlanFinanceCase):
	"""PLN v1.27 §10.9 — U10's next step is about this task, not only the
	plan: return when over the approved amount, and a decided task read as
	history involves no one."""

	def open_task(self, accepted: dict):
		return frappe.get_doc("Plan Finance Task", {"plan_version": accepted["annual_plan_version"], "status": "Open"})

	def test_u10_an_open_review_is_the_officers_turn_at_funding_confirmation(self):
		accepted, _ = self.ready_item()
		self.request(accepted["annual_plan"])
		read = plan_read.get_finance_task(task=self.open_task(accepted).name, user=fx.FINANCE_OFFICER)
		self.assertEqual((read["next_step"]["kind"], read["next_step"]["headline"]), ("your_turn", "Confirm plan funding or return the plan to the planner"))
		self.assertEqual(read["journey"]["current"], "funding")
		self.assertNotIn("badge", read["header"])

	def test_u10_over_the_approved_amount_the_only_turn_is_to_return_it(self):
		accepted, _ = self.ready_item()
		self.request(accepted["annual_plan"])
		# the plan's amount rose past the line after the request (fixture-only
		# override, as the Playwright U10-OVER-APPROVED profile does)
		for allocation in frappe.get_all("Plan Source Allocation", filters={"plan_version": accepted["annual_plan_version"]}, pluck="name"):
			frappe.db.set_value("Plan Source Allocation", allocation, "indicative_amount", 150_000_000, update_modified=False)
		read = plan_read.get_finance_task(task=self.open_task(accepted).name, user=fx.FINANCE_OFFICER)
		self.assertFalse(read["can_confirm"])
		self.assertEqual((read["next_step"]["kind"], read["next_step"]["headline"]), ("your_turn", "Return the plan to the planner"))

	def test_u10_a_decided_review_read_as_history_involves_no_one(self):
		accepted, _ = self.ready_item()
		self.request(accepted["annual_plan"])
		task = self.open_task(accepted)
		frappe.set_user(fx.FINANCE_OFFICER)
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
		read = plan_read.get_finance_task(task=task.name, user=fx.FINANCE_OFFICER)
		self.assertEqual(read["next_step"]["kind"], "not_involved")
		self.assertTrue(read["journey"])


from kentender_procurement.procurement_planning.tests.test_plan_requisition import RequisitionCase  # noqa: E402


class TestFinanceHistoryAfterActivation(RequisitionCase):
	"""U10-HISTORY — the confirmation that preceded activation stays that
	confirmation once the plan is in force; only a check requested after
	activation is a reassessment (found live 25 Sep 2026: the plan's own
	original review was retitled "Check funding again for the current plan")."""

	def test_the_original_review_is_not_a_reassessment_once_the_plan_is_in_force(self):
		accepted, item_id = self.active_item()
		task = frappe.get_all("Plan Finance Task", filters={"plan_version": accepted["annual_plan_version"]}, pluck="name")[0]
		read = plan_read.get_finance_task(task=task, user=fx.FINANCE_OFFICER)
		self.assertFalse(read["is_reassessment"])
		self.assertEqual(read["next_step"]["kind"], "not_involved")
		self.assertTrue(read["journey"])


class TestGovernanceReviewNextStep(RequisitionCase):
	"""PLN v1.27 §10.10 — U11 as each reader sees the plan at AO adoption."""

	def test_u11_ao_turn_planner_waits_on_the_named_officer_auditor_not_involved(self):
		from kentender_procurement.procurement_planning.services import plan_governance

		accepted, item_id = self.confirmed_item()
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		frappe.set_user(fx.HOPF)
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		task = submitted["task"]
		ao = plan_read.get_plan_governance_task(task=task, user=fx.ACCOUNTING_OFFICER)
		self.assertEqual((ao["next_step"]["kind"], ao["next_step"]["headline"]), ("your_turn", "Adopt and submit the plan, or return it for correction"))
		self.assertEqual(ao["journey"]["current"], "ao")
		planner = plan_read.get_plan_governance_task(task=task, user=fx.PLANNER)
		self.assertEqual(planner["next_step"]["kind"], "waiting")
		officer = _name(fx.ACCOUNTING_OFFICER)
		self.assertIn(officer, planner["next_step"]["holder"]["people"])
		self.assertTrue(planner["next_step"]["headline"].endswith("(Accounting Officer) to adopt or return the plan"))
		self.assertTrue(planner["next_step"]["since"]["display"].endswith("EAT"))
		# §10.16 C01-ROUTE-MISSING — with no statutory approver set up, the AO
		# cannot adopt: the missing setting is the blocker in the AO's next
		# step (Setting / Affected action / Responsible role + the D3 fix).
		from unittest.mock import patch as _patch
		from kentender_procurement.procurement_planning.services import plan_governance as _pg

		with _patch.object(_pg, "statutory_route_configured", return_value=False):
			blocked = plan_read.get_plan_governance_task(task=task, user=fx.ACCOUNTING_OFFICER)["next_step"]
		self.assertEqual(blocked["kind"], "your_turn_blocked")
		facts = {f["label"]: f["value"] for f in blocked["blockers"][0]["facts"]}
		self.assertEqual(facts, {"Setting": "Annual Plan approval authority", "Affected action": "Adopt and submit", "Responsible role": "Administrator or System Manager"})
		self.assertEqual([f["label"] for f in blocked["blockers"][0]["fixes"]], ["Ask your KenTender administrator to complete this setting."])
		auditor = plan_read.get_plan_governance_task(task=task, user=fx.AUDITOR)
		self.assertEqual(auditor["next_step"]["kind"], "not_involved")
		self.assertTrue(auditor["journey"])

	def test_a_returned_plan_carrying_its_funding_check_still_says_since_when_it_waits_for_signature(self):
		"""Found in the browser 25 Sep 2026: after the Accounting Officer
		returned the plan, the corrected Version reused Finance's check (no new
		decision on it), so the wait for the signer lost its "since"."""
		from kentender_procurement.procurement_planning.services import plan_governance

		accepted, item_id = self.confirmed_item()
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		frappe.set_user(fx.HOPF)
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		plan_governance.return_plan_version(task=ao_task.name, reason="Confirm the contract-signing date against delivery.", task_token=ao_task.task_token, idempotency_key=key())
		step = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"], user=fx.PLANNER)["next_step"]
		if step["kind"] == "waiting" and step["stage"] == "signature":
			self.assertTrue(step["since"], "a wait for the signer names since when")
			self.assertTrue(step["since"]["display"].endswith("EAT"))


from kentender_procurement.procurement_planning.tests.test_plan_publication import PublicationCase  # noqa: E402


class TestPublicationNextStep(PublicationCase):
	"""PLN v1.27 §10.12 U13 — reduced tracker, per-actor answers, and O4: the
	one named exception to KT-STD §3B.6 — the authorised technical operator
	gets Your turn on a failed or unknown publication, and nothing in My Work."""

	def publication(self) -> tuple[dict, str, str]:
		accepted, item_id = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		version = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
		return accepted, approved["publication"], version

	def test_u13_treasury_is_the_aos_turn_the_planner_waits_on_them_reduced_tracker(self):
		accepted, publication, version = self.publication()
		ao = plan_read.get_publication_task(publication=publication, user=fx.ACCOUNTING_OFFICER)
		self.assertEqual((ao["next_step"]["kind"], ao["next_step"]["headline"]), ("your_turn", "Record the Treasury submission"))
		self.assertTrue(ao["journey"]["reduced"])
		self.assertEqual(ao["journey"]["reduced_parts"]["prefix"], "Stage 6 of 7: ")
		planner = plan_read.get_publication_task(publication=publication, user=fx.PLANNER)
		self.assertEqual(planner["next_step"]["kind"], "waiting")
		self.assertIn("(Accounting Officer) to record the Treasury submission", planner["next_step"]["headline"])

	def test_o4_a_failed_publication_is_the_technical_operators_turn_and_no_one_elses(self):
		from kentender_procurement.procurement_planning.services import my_work_provider

		accepted, publication, version = self.publication()
		self.record_treasury(version)
		frappe.db.set_value("Annual Plan Publication Destination", frappe.get_doc("Plan Publication", publication).destination, "sandbox_outcome", "Fail")
		frappe.set_user("Administrator")
		self.assertEqual(publication_pipeline.publish_annual_plan(plan_version=version, idempotency_key=key())["result"], "Failed")
		technical = plan_read.get_publication_task(publication=publication, user="Administrator")
		self.assertEqual((technical["next_step"]["kind"], technical["next_step"]["headline"]), ("your_turn", "Retry publication"))
		ao = plan_read.get_publication_task(publication=publication, user=fx.ACCOUNTING_OFFICER)
		self.assertEqual(ao["next_step"]["kind"], "waiting")
		self.assertEqual(ao["next_step"]["headline"], "Waiting for an authorised technical operator to retry publication")
		self.assertTrue(ao["next_step"]["since"])
		# O4: no My Work item for the technical operator
		work = my_work_provider.my_work_rows(user="Administrator")
		self.assertEqual([r for r in work["assigned"] if publication in frappe.as_json(r)], [])
