# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 7 — UI read contracts backing STR-UI-01..04.

Covers the rebuilt get_strategy_portfolio / get_plan_workspace /
get_strategy_tree / get_plan_history / get_version_review_overview /
diff_strategy_versions in kentender_strategy.services.strategy_ui_contracts,
which replace the still-broken pre-Phase-1 functions of the same intent in
strategy_contracts.py for the 4 new Vue screens.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from kentender_strategy.services import strategy_ui_contracts as ui
from kentender_strategy.services.strategy_authorization import ensure_strategy_governance_roles
from kentender_strategy.services.strategy_transitions import transition_plan_version

PE = "PE-MOH"
FY = "FY-2027-2028"


class Phase7TestBase(FrappeTestCase):
	def setUp(self):
		ensure_strategy_governance_roles()
		self.suffix = uuid4().hex[:8]
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def _track(self, doc):
		self._cleanup.append((doc.doctype, doc.name))
		return doc

	def _user(self, label: str) -> str:
		email = f"str.p7.{label}.{self.suffix}@test.local"
		self._track(
			frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		)
		return email

	def _assign(self, user: str, profile_id: str, pe: str = PE) -> None:
		self._track(
			frappe.get_doc(
				{
					"doctype": "Operational Scope Assignment",
					"assignment_id": f"OSA-P7-{uuid4().hex[:10]}-{self.suffix}",
					"user_id": user,
					"capability_profile_id": profile_id,
					"procuring_entity_id": pe,
					"effective_from": add_days(now_datetime(), -1),
					"status": "Active",
					"assigned_by": "Administrator",
					"assigned_at": now_datetime(),
					"concurrency_token": uuid4().hex,
				}
			).insert(ignore_permissions=True)
		)

	def _plan_and_version(self, pe: str = PE, **version_kwargs) -> tuple[str, str]:
		plan = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan",
					"title": f"Phase 7 Test Plan {self.suffix}",
					"procuring_entity_id": pe,
					"plan_role": "Primary",
					"period_start": "2040-07-01",
					"period_end": "2045-06-30",
				}
			).insert(ignore_permissions=True)
		)
		data = {
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": "2040-07-01",
			"effective_to": "2045-06-30",
		}
		data.update(version_kwargs)
		version = self._track(frappe.get_doc(data).insert(ignore_permissions=True))
		return plan.name, version.name

	def _fill_hierarchy(self, plan_version: str, target_value: float = 80) -> dict:
		pillar = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Pillar",
					"title": "Pillar A",
					"display_order": 1,
				}
			).insert(ignore_permissions=True)
		)
		programme = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Programme",
					"title": "Programme A",
					"display_order": 2,
					"parent_node_id": pillar.name,
				}
			).insert(ignore_permissions=True)
		)
		objective = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Strategic Objective",
					"title": "Objective A",
					"display_order": 3,
					"parent_node_id": programme.name,
				}
			).insert(ignore_permissions=True)
		)
		indicator = self._track(
			frappe.get_doc(
				{
					"doctype": "Performance Indicator",
					"plan_version_id": plan_version,
					"measures_node_id": objective.name,
					"indicator_name": "Indicator A",
					"definition": "Definition",
					"unit": "Percentage",
				}
			).insert(ignore_permissions=True)
		)
		target = self._track(
			frappe.get_doc(
				{
					"doctype": "Performance Target",
					"indicator_id": indicator.name,
					"financial_year_id": FY,
					"comparison": "At least",
					"target_value": target_value,
				}
			).insert(ignore_permissions=True)
		)
		return {
			"pillar": pillar.name,
			"programme": programme.name,
			"objective": objective.name,
			"indicator": indicator.name,
			"target": target.name,
		}


class TestPortfolio(Phase7TestBase):
	def test_forbidden_when_no_role_or_capability(self):
		user = self._user("norole")
		frappe.set_user(user)
		result = ui.get_strategy_portfolio()
		frappe.set_user("Administrator")
		self.assertTrue(result["forbidden"])

	def test_lists_scoped_plan_for_author(self):
		plan_id, version_id = self._plan_and_version()
		user = self._user("author")
		self._assign(user, "CAP-STRATEGY-AUTHOR")
		frappe.set_user(user)
		result = ui.get_strategy_portfolio()
		frappe.set_user("Administrator")
		self.assertFalse(result["forbidden"])
		ids = [p["id"] for p in result["plans"]]
		self.assertIn(plan_id, ids)
		row = next(p for p in result["plans"] if p["id"] == plan_id)
		self.assertEqual(row["current_version"]["status"], "Draft")

	def test_other_pe_plan_not_visible_to_scoped_author(self):
		self._plan_and_version(pe="PE-CGKIS")
		user = self._user("authormoh")
		self._assign(user, "CAP-STRATEGY-AUTHOR", pe=PE)
		frappe.set_user(user)
		result = ui.get_strategy_portfolio()
		frappe.set_user("Administrator")
		self.assertFalse(result["forbidden"])
		for row in result["plans"]:
			self.assertEqual(row["procuring_entity"]["id"], PE)


class TestPlanWorkspaceAndTree(Phase7TestBase):
	def test_strategy_tree_shape_and_counts(self):
		_, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		tree = ui.get_strategy_tree(version_id)
		self.assertEqual(tree["counts"]["pillars"], 1)
		self.assertEqual(tree["counts"]["programmes"], 1)
		self.assertEqual(tree["counts"]["strategic_objectives"], 1)
		self.assertEqual(tree["counts"]["performance_indicators"], 1)
		self.assertEqual(tree["counts"]["performance_targets"], 1)
		root = tree["tree"][0]
		self.assertEqual(root["node_type"], "Pillar")
		programme = root["children"][0]
		objective = programme["children"][0]
		indicator = objective["children"][0]
		self.assertEqual(indicator["node_type"], "Performance Indicator")
		target = indicator["children"][0]
		self.assertEqual(target["node_type"], "Performance Target")
		self.assertEqual(target["comparison"], "At least")

	def test_workspace_active_plan_shows_current_authority(self):
		plan_id, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		author = self._user("author2")
		reviewer = self._user("reviewer2")
		approver = self._user("approver2")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		self._assign(reviewer, "CAP-STRATEGY-REVIEWER")
		self._assign(approver, "CAP-STRATEGY-APPROVAL-AUTHORITY")

		frappe.set_user(author)
		transition_plan_version(version_id, "Submit for review")
		frappe.set_user(reviewer)
		transition_plan_version(version_id, "Recommend for approval")
		frappe.set_user(approver)
		transition_plan_version(version_id, "Approve")
		transition_plan_version(version_id, "Activate")
		frappe.set_user("Administrator")

		result = ui.get_plan_workspace(plan_id)
		self.assertFalse(result["forbidden"])
		self.assertIsNotNone(result["active_version"])
		self.assertIsNone(result["pending_version"])
		self.assertIsNotNone(result["current_authority"])
		self.assertIsNotNone(result["current_authority"]["approved_by"])
		self.assertIsNotNone(result["current_authority"]["activated"])
		self.assertEqual(result["structure_summary"]["performance_targets"], 1)

	def test_workspace_forbidden_for_unrelated_user(self):
		plan_id, version_id = self._plan_and_version()
		user = self._user("outsider")
		frappe.set_user(user)
		result = ui.get_plan_workspace(plan_id)
		frappe.set_user("Administrator")
		self.assertTrue(result["forbidden"])

	def test_plan_history_lists_events_newest_first(self):
		plan_id, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		author = self._user("author3")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		frappe.set_user(author)
		transition_plan_version(version_id, "Submit for review")
		frappe.set_user("Administrator")

		history = ui.get_plan_history(plan_id)
		self.assertGreaterEqual(len(history), 1)
		events = [h["event"] for h in history]
		self.assertIn("Submit for review", events)
		timestamps = [h["at"] for h in history]
		self.assertEqual(timestamps, sorted(timestamps, reverse=True))


class TestVersionReviewOverview(Phase7TestBase):
	def _submit(self, version_id: str, author: str) -> None:
		frappe.set_user(author)
		transition_plan_version(version_id, "Submit for review")
		frappe.set_user("Administrator")

	def test_reviewer_role_and_readiness(self):
		_, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		author = self._user("author4")
		reviewer = self._user("reviewer4")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		self._assign(reviewer, "CAP-STRATEGY-REVIEWER")
		self._submit(version_id, author)

		frappe.set_user(reviewer)
		result = ui.get_version_review_overview(version_id)
		frappe.set_user("Administrator")

		self.assertEqual(result["role"], "reviewer")
		self.assertIn("Return", result["allowed_actions"])
		self.assertIn("Recommend for approval", result["allowed_actions"])
		self.assertTrue(result["readiness"]["ready"])
		self.assertIsNotNone(result["submission_authority"]["submitted_by"])

	def test_approver_role_after_recommend(self):
		_, version_id = self._plan_and_version()
		self._fill_hierarchy(version_id)
		author = self._user("author5")
		reviewer = self._user("reviewer5")
		approver = self._user("approver5")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		self._assign(reviewer, "CAP-STRATEGY-REVIEWER")
		self._assign(approver, "CAP-STRATEGY-APPROVAL-AUTHORITY")
		self._submit(version_id, author)
		frappe.set_user(reviewer)
		transition_plan_version(version_id, "Recommend for approval")
		frappe.set_user("Administrator")

		frappe.set_user(approver)
		result = ui.get_version_review_overview(version_id)
		frappe.set_user("Administrator")

		self.assertEqual(result["role"], "approver")
		self.assertIn("Approve", result["allowed_actions"])
		self.assertIsNotNone(result["submission_authority"]["reviewed_by"])


class TestDiffStrategyVersions(Phase7TestBase):
	def test_detects_target_value_change_and_node_addition(self):
		plan_id, base_version = self._plan_and_version()
		self._fill_hierarchy(base_version, target_value=80)
		author = self._user("author6")
		reviewer = self._user("reviewer6")
		approver = self._user("approver6")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		self._assign(reviewer, "CAP-STRATEGY-REVIEWER")
		self._assign(approver, "CAP-STRATEGY-APPROVAL-AUTHORITY")

		frappe.set_user(author)
		transition_plan_version(base_version, "Submit for review")
		frappe.set_user(reviewer)
		transition_plan_version(base_version, "Recommend for approval")
		frappe.set_user(approver)
		transition_plan_version(base_version, "Approve")
		transition_plan_version(base_version, "Activate")
		frappe.set_user("Administrator")

		from kentender_strategy.services.strategy_writes import create_strategy_successor_version

		frappe.set_user(author)
		successor = create_strategy_successor_version(plan_id)
		frappe.set_user("Administrator")
		successor_id = successor["name"]

		# Bump the cloned target's value 80 -> 85 (the concrete example in the
		# design spec) and add a brand-new Pillar to exercise the addition path.
		target_name = frappe.db.get_value(
			"Performance Target",
			{"indicator_id": ["in", frappe.get_all(
				"Performance Indicator", filters={"plan_version_id": successor_id}, pluck="name"
			)]},
			"name",
		)
		frappe.db.set_value("Performance Target", target_name, "target_value", 85)
		self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": successor_id,
					"node_type": "Pillar",
					"title": "New Pillar",
					"display_order": 99,
				}
			).insert(ignore_permissions=True)
		)

		result = ui.diff_strategy_versions(base_version, successor_id)
		items = {c["item"]: c for c in result["changes"]}
		self.assertIn("Target: Indicator A", items)
		self.assertEqual(items["Target: Indicator A"]["active"], "At least 80.0")
		self.assertEqual(items["Target: Indicator A"]["submitted"], "At least 85.0")
		self.assertIn("Pillar: New Pillar", items)
		self.assertEqual(items["Pillar: New Pillar"]["submitted"], "Added")
		self.assertTrue(result["limitation"])
