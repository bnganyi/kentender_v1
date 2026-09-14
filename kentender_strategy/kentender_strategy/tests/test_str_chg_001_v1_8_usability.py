# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.8 — the approved usability decisions, server side.

Covers the Phase 2 rows of `STR-CHG-001_IMPLEMENTATION_TRACKER.md`:
STR18-201 vocabulary, STR18-202 workspace compositions, STR18-203 review
overview, STR18-204 comparison, STR18-205 immediate-effect approval and
predecessor closure, STR18-206 idempotent replay, STR18-207 sibling
reorder, STR18-208 fixture profiles. Traceability: STR18-AC-001/002/
005/006/008/010/011/012/013/014/015/021/022.

    bench --site kentender.midas.com run-tests --app kentender_strategy \
        --module kentender_strategy.tests.test_str_chg_001_v1_8_usability
"""

from __future__ import annotations

from uuid import uuid4

import frappe

from kentender_strategy.api import strategy_consumer_api as api
from kentender_strategy.services import strategy_ui_contracts as ui
from kentender_strategy.services.strategy_transitions import transition_plan_version
from kentender_strategy.services.strategy_writes import (
	create_strategy_successor_version,
	save_strategy_structure_draft,
)
from kentender_strategy.tests.fixtures import pin_review_date
from kentender_strategy.tests.test_str_chg_001_phase7_ui_contracts import FY, Phase7TestBase


class UsabilityTestBase(Phase7TestBase):
	def _actors(self, tag: str) -> tuple[str, str]:
		author = self._user(f"author{tag}")
		approver = self._user(f"approver{tag}")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		self._assign(approver, "CAP-STRATEGY-APPROVAL-AUTHORITY")
		return author, approver

	def _activate(self, version_id: str, author: str, approver: str) -> None:
		frappe.set_user(author)
		transition_plan_version(version_id, "Submit for approval")
		frappe.set_user(approver)
		transition_plan_version(version_id, "Approve")
		frappe.set_user("Administrator")

	def _successor(self, plan_id: str, author: str) -> str:
		frappe.set_user(author)
		try:
			out = create_strategy_successor_version(plan_id)
		finally:
			frappe.set_user("Administrator")
		self._cleanup.append(("Strategic Plan Version", out["name"]))
		for dt, field in (("Strategy Node", "plan_version_id"), ("Performance Indicator", "plan_version_id")):
			for name in frappe.get_all(dt, filters={field: out["name"]}, pluck="name"):
				self._cleanup.append((dt, name))
		for ind in frappe.get_all("Performance Indicator", filters={"plan_version_id": out["name"]}, pluck="name"):
			for t in frappe.get_all("Performance Target", filters={"indicator_id": ind}, pluck="name"):
				self._cleanup.append(("Performance Target", t))
		return out["name"]

	def _target_of(self, version_id: str) -> str:
		ind = frappe.db.get_value("Performance Indicator", {"plan_version_id": version_id}, "name")
		return frappe.db.get_value("Performance Target", {"indicator_id": ind}, "name")


class TestVocabulary(UsabilityTestBase):
	"""STR18-201 / STR18-AC-001, 002 — labels are produced on the server from
	the stored enums and real evidence; enums themselves are untouched."""

	def test_plan_type_and_status_labels(self):
		self.assertEqual(ui.plan_type_label("Primary"), "Main strategic plan")
		self.assertEqual(ui.plan_type_label("Supporting Framework"), "Supporting framework")
		self.assertEqual(ui.version_status_label("Active"), "Current")
		self.assertEqual(ui.version_status_label("Superseded"), "Previous version")
		self.assertEqual(ui.version_status_label("Submitted for approval"), "Awaiting approval")
		self.assertEqual(ui.version_status_label("Draft", version_number=1), "Draft")
		self.assertEqual(ui.version_status_label("Draft", version_number=2), "Draft update")
		self.assertEqual(ui.version_status_label("Draft", version_number=2, return_reason="fix it please"), "Changes requested")
		self.assertEqual(ui.fiscal_year_label("2027-2028"), "FY 2027/28")
		self.assertEqual(ui.target_period_label(None, "2028-06-30"), "By 30 Jun 2028")

	def test_register_row_actions_follow_server_authority(self):
		plan_id, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		author, approver = self._actors("vocab")

		frappe.set_user(author)
		row = next(p for p in ui.get_strategy_portfolio()["plans"] if p["id"] == plan_id)
		self.assertEqual(row["plan_type_label"], "Main strategic plan")
		self.assertEqual(row["status_label"], "Draft")
		self.assertEqual(row["available_action"], "Continue draft")
		transition_plan_version(version_id, "Submit for approval")
		row = next(p for p in ui.get_strategy_portfolio()["plans"] if p["id"] == plan_id)
		self.assertEqual(row["status_label"], "Awaiting approval")
		self.assertEqual(row["available_action"], "View")  # the author decides nothing

		frappe.set_user(approver)
		portfolio = ui.get_strategy_portfolio()
		row = next(p for p in portfolio["plans"] if p["id"] == plan_id)
		self.assertEqual(row["available_action"], "Review")
		task = next(w for w in portfolio["my_work"] if w["version_id"] == version_id)
		self.assertEqual(task["review_type"], "New plan")
		self.assertEqual(task["status_label"], "Awaiting review")
		self.assertEqual(task["action_label"], "Review")
		self.assertTrue(task["submitted_by"])
		self.assertTrue(task["submitted_at_label"])
		transition_plan_version(version_id, "Return", reason="Please name the measure more precisely.")

		frappe.set_user(author)
		row = next(p for p in ui.get_strategy_portfolio()["plans"] if p["id"] == plan_id)
		self.assertEqual(row["status_label"], "Changes requested")
		self.assertEqual(row["available_action"], "Correct and resubmit")
		frappe.set_user("Administrator")

	def test_technical_reader_has_an_empty_actions_queue(self):
		"""KT-STD-001 v1.5 §3A.6 — a technical reader reads everything and
		decides nothing."""
		_, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		author, _approver = self._actors("tech")
		frappe.set_user(author)
		transition_plan_version(version_id, "Submit for approval")
		frappe.set_user("Administrator")
		portfolio = ui.get_strategy_portfolio()
		self.assertFalse(portfolio["forbidden"])
		self.assertEqual([w for w in portfolio["my_work"] if w["version_id"] == version_id], [])


class TestWorkspaceComposition(UsabilityTestBase):
	"""STR18-202 / STR18-AC-015, 016 — current facts first, pending update
	separately, exact historical version on request."""

	def test_overview_leads_with_objectives_and_targets(self):
		plan_id, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		ws = ui.get_plan_workspace(plan_id)
		self.assertEqual(len(ws["objectives"]), 1)
		objective = ws["objectives"][0]
		self.assertEqual(objective["title"], "Objective A")
		self.assertEqual(objective["path_label"], "Pillar A / Programme A")
		indicator = objective["indicators"][0]
		self.assertEqual(indicator["definition"], "Definition")
		self.assertEqual(indicator["unit"], "Percentage")
		self.assertEqual(indicator["targets"][0]["period_label"], "FY 2040/41")
		self.assertEqual(indicator["targets"][0]["result_label"], "At least 80%")
		self.assertEqual(ws["plan"]["plan_type_label"], "Main strategic plan")
		self.assertEqual(ws["current_version"]["status_label"], "Draft")
		self.assertEqual(ws["current_version"]["effective_from_label"], "1 Jul 2040")

	def test_current_version_leads_and_pending_update_is_separate(self):
		plan_id, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors("ws")
		self._activate(v1, author, approver)

		frappe.set_user(author)
		ws = ui.get_plan_workspace(plan_id)
		self.assertTrue(ws["capabilities"]["update_plan"])
		self.assertIsNone(ws["pending_update"])
		self.assertEqual(ws["approval_details"]["label"], "Approved and activated Version 1")
		frappe.set_user("Administrator")

		v2 = self._successor(plan_id, author)
		frappe.set_user(author)
		ws = ui.get_plan_workspace(plan_id)
		# The Current version still leads; the Draft update is a notice.
		self.assertEqual(ws["current_version"]["id"], v1)
		self.assertEqual(ws["current_version"]["status_label"], "Current")
		self.assertTrue(ws["selected_is_current"])
		self.assertFalse(ws["capabilities"]["update_plan"])
		self.assertEqual(ws["pending_update"]["kind"], "draft")
		self.assertEqual(ws["pending_update"]["action_label"], "Continue draft")
		self.assertEqual(ws["pending_update"]["structure_route"][-1], "structure")
		# The exact successor on request, labelled as an update.
		ws2 = ui.get_plan_workspace(plan_id, version_number=2)
		self.assertEqual(ws2["current_version"]["id"], v2)
		self.assertEqual(ws2["current_version"]["status_label"], "Draft update")
		self.assertTrue(ws2["capabilities"]["edit_version_dates"])
		self.assertFalse(ws2["capabilities"]["edit_identity"])
		self.assertEqual(ws2["routes"]["current"], ["strategy", "plan", ws2["plan"]["reference"]])
		frappe.set_user("Administrator")

		self.assertTrue(ui.get_plan_workspace(plan_id, version_number=9)["not_found"])

	def test_history_carries_readable_event_labels_and_verbatim_actions(self):
		plan_id, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors("hist")
		self._activate(v1, author, approver)
		v2 = self._successor(plan_id, author)
		rows = ui.get_version_history(v2)
		self.assertEqual(rows[-1]["event"], "Successor Version Created")
		self.assertEqual(rows[-1]["event_label"], "Draft update created from Version 1")
		v1_rows = ui.get_version_history(v1)
		labels = {r["event"]: r["event_label"] for r in v1_rows}
		self.assertEqual(labels["Submit for approval"], "Submitted for approval")
		self.assertEqual(labels["Approve"], "Approved and activated")


class TestReviewOverviewAndComparison(UsabilityTestBase):
	"""STR18-203 / STR18-204 / STR18-AC-011, 012, 013."""

	def _submitted_successor(self, tag: str):
		plan_id, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors(tag)
		self._activate(v1, author, approver)
		v2 = self._successor(plan_id, author)
		return plan_id, v1, v2, author, approver

	def test_first_version_review_shows_full_proposal_and_no_comparison(self):
		_, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors("first")
		frappe.set_user(author)
		transition_plan_version(v1, "Submit for approval")
		frappe.set_user(approver)
		out = ui.get_version_review_overview(v1)
		frappe.set_user("Administrator")
		self.assertEqual(out["review_type"], "New plan")
		self.assertEqual(out["title"], "Review strategic plan")
		self.assertIsNone(out["comparison"])
		self.assertEqual(out["decision"]["approve_label"], "Approve and use plan")
		self.assertTrue(out["decision"]["can_approve"])
		self.assertEqual(out["objectives"][0]["indicators"][0]["targets"][0]["result_label"], "At least 80%")
		self.assertEqual(out["version"]["status_label"], "Awaiting approval")
		self.assertEqual(out["readiness"]["failures"], [])

	def test_successor_review_leads_with_server_comparison(self):
		plan_id, v1, v2, author, approver = self._submitted_successor("cmp")
		frappe.db.set_value("Performance Target", self._target_of(v2), "target_value", 85)
		frappe.db.set_value("Strategic Plan Version", v2, "effective_from", "2041-07-01")
		frappe.set_user(author)
		transition_plan_version(v2, "Submit for approval")
		frappe.set_user(approver)
		out = ui.get_version_review_overview(v2)
		frappe.set_user("Administrator")
		self.assertEqual(out["review_type"], "Plan changes")
		self.assertEqual(out["title"], "Review plan changes")
		self.assertEqual(out["baseline_version_number"], 1)
		self.assertTrue(out["comparison"]["available"])
		rows = {c["item"]: c for c in out["comparison"]["changes"]}
		self.assertEqual(rows["Target for FY 2040/41"]["previous"], "At least 80%")
		self.assertEqual(rows["Target for FY 2040/41"]["proposed"], "At least 85%")
		self.assertEqual(rows["Version effective from"]["previous"], "1 Jul 2040")
		self.assertEqual(rows["Version effective from"]["proposed"], "1 Jul 2041")
		self.assertEqual(out["comparison"]["heading"], "Changes from Version 1")
		self.assertEqual(out["decision"]["approve_label"], "Approve changes and use plan")
		self.assertIn("Existing approved records keep their saved strategy details.", out["decision"]["consequence"])

	def test_comparison_reports_definitions_units_order_additions_and_removals(self):
		plan_id, v1, v2, author, approver = self._submitted_successor("diff")
		# Definition and unit change on the cloned indicator.
		ind = frappe.db.get_value("Performance Indicator", {"plan_version_id": v2}, "name")
		frappe.db.set_value("Performance Indicator", ind, {"definition": "Revised definition", "unit": "Count"})
		# Remove the cloned target, add a new one for a different period, and
		# reorder two objectives in one change set.
		programme = frappe.db.get_value("Strategy Node", {"plan_version_id": v2, "node_type": "Programme"}, "name")
		objective_a = frappe.db.get_value("Strategy Node", {"plan_version_id": v2, "node_type": "Strategic Objective"}, "name")
		frappe.set_user(author)
		result = save_strategy_structure_draft(
			v2,
			nodes=[
				{"client_id": "$b", "node_type": "Strategic Objective", "title": "Objective B", "display_order": 9, "parent_node_id": programme},
			],
			deletes=[{"doctype": "Performance Target", "name": self._target_of(v2)}],
		)
		self._cleanup.append(("Strategy Node", result["nodes"][0]))
		objective_b = result["nodes"][0]
		# Swap the two objectives' order in one validated change set (STR18-207).
		save_strategy_structure_draft(
			v2,
			nodes=[
				{"name": objective_a, "display_order": 9},
				{"name": objective_b, "display_order": 3},
			],
		)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Strategy Node", objective_a, "display_order"), 9)
		self.assertEqual(frappe.db.get_value("Strategy Node", objective_b, "display_order"), 3)

		diff = ui.diff_strategy_versions(v1, v2)
		kinds = {(c["kind"], c["item"]): c for c in diff["changes"]}
		self.assertEqual(kinds[("definition", "How Indicator A is measured")]["proposed"], "Revised definition")
		self.assertEqual(kinds[("unit", "Unit of Indicator A")]["proposed"], "Count")
		self.assertEqual(kinds[("node", "Strategic Objective: Objective B")]["proposed"], "Added")
		self.assertEqual(kinds[("node", "Strategic Objective: Objective B")]["path"], "Pillar A / Programme A")
		removed = kinds[("target", "Target for FY 2040/41")]
		self.assertEqual(removed["proposed"], "Removed")
		self.assertEqual(removed["previous"], "At least 80%")
		self.assertTrue(removed["previous_id"])

	def test_first_version_comparison_says_so(self):
		_, v1 = self._plan_and_version()
		out = ui.diff_strategy_versions(None, v1)
		self.assertTrue(out["first_version"])
		self.assertEqual(out["message"], "This is the first version of this plan.")

	def test_readiness_failures_name_the_missing_item(self):
		_, v1 = self._plan_and_version()
		readiness = ui.get_version_readiness(v1)
		rules = [f["rule"] for f in readiness["failures"]]
		self.assertEqual(rules, ["HIERARCHY_PILLAR"])
		self.assertEqual(readiness["failures"][0]["message"], "Add a pillar to start the plan structure.")
		author, _ = self._actors("ready")
		frappe.set_user(author)
		with self.assertRaises(frappe.ValidationError) as ctx:
			transition_plan_version(v1, "Submit for approval")
		frappe.set_user("Administrator")
		self.assertIn("Complete the highlighted items before submitting or approving.", str(ctx.exception))
		self.assertIn("Add a pillar", str(ctx.exception))

	def test_self_approval_is_named_not_hidden(self):
		_, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		dual = self._user("dualv18")
		self._assign(dual, "CAP-STRATEGY-AUTHOR")
		self._assign(dual, "CAP-STRATEGY-APPROVAL-AUTHORITY")
		frappe.set_user(dual)
		transition_plan_version(v1, "Submit for approval")
		out = ui.get_version_review_overview(v1)
		frappe.set_user("Administrator")
		self.assertFalse(out["forbidden"])
		self.assertTrue(out["self_approval_blocked"])
		self.assertFalse(out["decision"]["can_approve"])
		self.assertFalse(out["decision"]["can_return"])


class TestImmediateEffectApproval(UsabilityTestBase):
	"""STR18-205 / STR18-AC-021, 022 / STR18-XD-002 — the FUTURE profile is
	refused while Submitted; the IMMEDIATE profile activates and closes the
	predecessor's applicability to the day before it starts."""

	def _submitted_successor_with_start(self, tag: str, start: str):
		plan_id, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors(tag)
		self._activate(v1, author, approver)
		v2 = self._successor(plan_id, author)
		frappe.db.set_value("Performance Target", self._target_of(v2), "target_value", 85)
		frappe.db.set_value("Strategic Plan Version", v2, "effective_from", start)
		frappe.set_user(author)
		transition_plan_version(v2, "Submit for approval")
		frappe.set_user("Administrator")
		return plan_id, v1, v2, author, approver

	def test_future_effective_version_cannot_be_approved_and_stays_submitted(self):
		plan_id, v1, v2, author, approver = self._submitted_successor_with_start("future", "2041-07-01")
		pin_review_date(self, "2040-11-25")
		frappe.set_user(approver)
		out = ui.get_version_review_overview(v2)
		self.assertTrue(out["blockers"]["blocked"])
		self.assertEqual(out["blockers"]["future_effective"]["effective_from_label"], "1 Jul 2041")
		self.assertIn("It starts on 1 Jul 2041.", out["blockers"]["future_effective"]["headline"])
		self.assertFalse(out["decision"]["can_approve"])
		self.assertTrue(out["decision"]["can_return"])
		with self.assertRaises(frappe.ValidationError) as ctx:
			transition_plan_version(v2, "Approve")
		frappe.set_user("Administrator")
		self.assertIn("cannot be approved yet", str(ctx.exception))
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", v2, "status"), "Submitted for approval")
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", v1, "status"), "Active")

	def test_immediate_version_activates_and_closes_the_predecessor(self):
		plan_id, v1, v2, author, approver = self._submitted_successor_with_start("now", "2040-11-25")
		pin_review_date(self, "2040-11-25")
		frappe.set_user(approver)
		out = transition_plan_version(v2, "Approve")
		frappe.set_user("Administrator")
		self.assertEqual(out["status"], "Active")
		self.assertEqual(out["version_number"], 2)
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", v1, "status"), "Superseded")
		self.assertEqual(str(frappe.db.get_value("Strategic Plan Version", v1, "effective_to")), "2040-11-24")
		ws = ui.get_plan_workspace(plan_id, version_number=1)
		self.assertEqual(ws["current_version"]["status_label"], "Previous version")
		self.assertEqual(ws["current_version"]["effective_period_label"], "1 Jul 2040 – 24 Nov 2040")


class TestIdempotentReplay(UsabilityTestBase):
	"""STR18-206 / STR18-AC-004, 008, 014 — a retried attempt returns the
	original committed result and creates nothing twice."""

	def test_plan_creation_replays_from_the_journal(self):
		author, _ = self._actors("idem")
		key = f"attempt-{uuid4().hex}"
		payload = {
			"title": f"Idempotent plan {self.suffix}",
			"plan_role": "Primary",
			"period_start": "2050-07-01",
			"period_end": "2055-06-30",
			"effective_from": "2050-07-01",
			"effective_to": "2055-06-30",
		}
		frappe.set_user(author)
		first = api.save_strategy_plan_draft(payload=payload, idempotency_key=key)
		second = api.save_strategy_plan_draft(payload=payload, idempotency_key=key)
		frappe.set_user("Administrator")
		self._cleanup.append(("Strategic Plan Version", first["version"]["name"]))
		self._cleanup.append(("Strategic Plan", first["plan"]["plan_id"]))
		self._cleanup.append(("Strategy Command Journal", frappe.db.get_value("Strategy Command Journal", {"idempotency_key": key}, "name")))
		self.assertEqual(first["plan"]["plan_id"], second["plan"]["plan_id"])
		self.assertEqual(frappe.db.count("Strategic Plan", {"title": payload["title"]}), 1)

	def test_approval_replays_without_a_second_decision(self):
		_, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		author, approver = self._actors("idem2")
		frappe.set_user(author)
		transition_plan_version(v1, "Submit for approval")
		key = f"decide-{uuid4().hex}"
		frappe.set_user(approver)
		token = str(frappe.db.get_value("Strategic Plan Version", v1, "modified"))
		first = api.approve_strategy_version(v1, expected_version=token, idempotency_key=key)
		second = api.approve_strategy_version(v1, expected_version=token, idempotency_key=key)
		frappe.set_user("Administrator")
		self._cleanup.append(("Strategy Command Journal", frappe.db.get_value("Strategy Command Journal", {"idempotency_key": key}, "name")))
		self.assertEqual(first["status"], "Active")
		self.assertEqual(second, first)
		approvals = [e for e in ui.get_version_history(v1) if e["event"] == "Approve"]
		self.assertEqual(len(approvals), 1)


class TestFixtureProfiles(UsabilityTestBase):
	"""STR18-208 / STR18-AC-021, 022 — the §14.4 profiles on the canonical
	plan, isolated and torn down; the default Version 1 stays unchanged."""

	def setUp(self):
		super().setUp()
		from kentender_strategy.seeds.kentender_mvp_v1_strategy import PLAN_TITLE

		if not frappe.db.exists("Strategic Plan", {"title": PLAN_TITLE}) or not frappe.db.exists("Fiscal Year", "2027-2028"):
			self.skipTest("canonical §14.3 plan and FY 2027-2028 are not seeded on this site")

	def test_profiles_carry_the_section_14_4_clocks_and_isolate(self):
		from kentender_strategy.seeds import kentender_mvp_v1_strategy as seed

		v1 = frappe.db.get_value(
			"Strategic Plan Version",
			{"plan_id": frappe.db.get_value("Strategic Plan", {"title": seed.PLAN_TITLE}, "name"), "version_number": 1},
			"name",
		)
		v1_before = frappe.db.get_value("Strategic Plan Version", v1, ["status", "effective_to", "modified"], as_dict=True)
		if frappe.db.exists("Strategic Plan Version", {"plan_id": frappe.db.get_value("Strategic Plan Version", v1, "plan_id"), "version_number": [">", 1]}):
			self.skipTest("an open Version 2 already exists on the canonical plan")

		fixture = seed.seed_str_des_v2_fixture(profile=seed.PROFILE_FUTURE)
		v2 = fixture["plan_version"]
		try:
			self.assertEqual(str(frappe.db.get_value("Strategic Plan Version", v2, "effective_from")), "2027-07-01")
			self.assertEqual(frappe.db.get_value("Strategic Plan Version", v2, "status"), "Submitted for approval")
			history = ui.get_version_history(v2)
			by_event = {h["event"]: h for h in history}
			self.assertEqual(by_event["Successor Version Created"]["at"], "2026-11-24 13:10:00")
			self.assertEqual(by_event["Draft structure saved"]["at"], "2026-11-24 15:55:00")
			self.assertEqual(by_event["Submit for approval"]["at"], "2026-11-24 16:20:00")
			self.assertEqual(len(history), 3)
			self.assertEqual(frappe.db.get_value("Performance Target", fixture["target"], "target_value"), 85)
			# The comparison names both the target and the applicability start.
			diff = ui.diff_strategy_versions(None, v2)
			items = {c["item"] for c in diff["changes"]}
			self.assertIn("Target for FY 2027/28", items)
			self.assertIn("Version effective from", items)
		finally:
			seed.teardown_str_des_v2_fixture(v2)

		fixture = seed.seed_str_des_v2_returned_fixture()
		v2 = fixture["plan_version"]
		try:
			self.assertEqual(frappe.db.get_value("Strategic Plan Version", v2, "status"), "Draft")
			self.assertEqual(frappe.db.get_value("Strategic Plan Version", v2, "return_reason"), seed.RETURN_REASON)
			returned = next(h for h in ui.get_version_history(v2) if h["event"] == "Return")
			self.assertEqual(returned["at"], "2026-11-25 11:20:00")
		finally:
			seed.teardown_str_des_v2_fixture(v2)

		v1_after = frappe.db.get_value("Strategic Plan Version", v1, ["status", "effective_to", "modified"], as_dict=True)
		self.assertEqual(v1_after.status, "Active")
		self.assertEqual(v1_after.effective_to, v1_before.effective_to)
