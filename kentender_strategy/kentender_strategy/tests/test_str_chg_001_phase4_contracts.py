# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 4 — service contracts (§10, §10.1).

Covers STR-AC-009, 016-020. Uses the real, Phase 3-seeded
CAP-STRATEGY-AUTHOR/-APPROVAL-AUTHORITY profiles rather than throwaway
ones, now that they exist.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from kentender_strategy.api import strategy_consumer_api as api
from kentender_strategy.services import strategy_consumer as consumer
from kentender_strategy.services import strategy_contracts as contracts
from kentender_strategy.services.strategy_authorization import ensure_strategy_governance_roles
from kentender_strategy.services.strategy_writes import (
	create_strategy_successor_version,
	save_strategy_plan_draft,
	save_strategy_structure_draft,
)

PE = "PE-MOH"
FY = "FY-2027-2028"


class Phase4TestBase(FrappeTestCase):
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
		email = f"str.p4.{label}.{self.suffix}@test.local"
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
					"assignment_id": f"OSA-P4-{uuid4().hex[:10]}-{self.suffix}",
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
					"title": f"Contracts Test Plan {self.suffix}",
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

	def _fill_hierarchy(self, plan_version: str) -> dict:
		pillar = self._track(
			frappe.get_doc(
				{"doctype": "Strategy Node", "plan_version_id": plan_version, "node_type": "Pillar", "title": "Pillar", "display_order": 1}
			).insert(ignore_permissions=True)
		)
		programme = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Programme",
					"title": "Programme",
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
					"title": "Objective",
					"display_order": 3,
					"parent_node_id": programme.name,
				}
			).insert(ignore_permissions=True)
		)
		outcome = self._track(
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": plan_version,
					"node_type": "Strategic Outcome",
					"title": "Outcome",
					"display_order": 4,
					"parent_node_id": objective.name,
				}
			).insert(ignore_permissions=True)
		)
		indicator = self._track(
			frappe.get_doc(
				{
					"doctype": "Performance Indicator",
					"plan_version_id": plan_version,
					"measures_node_id": outcome.name,
					"indicator_name": "Indicator",
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
					"target_value": 80,
				}
			).insert(ignore_permissions=True)
		)
		return {
			"pillar": pillar.name,
			"programme": programme.name,
			"objective": objective.name,
			"outcome": outcome.name,
			"indicator": indicator.name,
			"target": target.name,
		}


class TestReadContracts(Phase4TestBase):
	def test_list_strategy_objectives_only_from_active_version_with_path(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		# Draft version: no objectives returned yet.
		self.assertEqual(consumer.list_strategy_objectives(version)["rows"], [])

		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")
		out = consumer.list_strategy_objectives(version)
		self.assertEqual(out["count"], 1)
		self.assertEqual(out["rows"][0]["id"], nodes["objective"])
		path_types = [p["type"] for p in out["rows"][0]["path"]]
		self.assertEqual(path_types, ["Pillar", "Programme", "Strategic Objective"])

	def test_get_strategy_lineage_for_node_indicator_and_target(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)

		obj_lineage = api.get_strategy_lineage(nodes["objective"])
		self.assertEqual([p["type"] for p in obj_lineage["path"]], ["Pillar", "Programme", "Strategic Objective"])

		ind_lineage = api.get_strategy_lineage(nodes["indicator"])
		self.assertEqual(ind_lineage["path"][-1]["type"], "Performance Indicator")

		tgt_lineage = api.get_strategy_lineage(nodes["target"])
		self.assertEqual(tgt_lineage["path"][-1]["type"], "Performance Target")

	def test_get_strategy_lineage_unknown_id_rejected(self):
		with self.assertRaises(frappe.DoesNotExistError):
			api.get_strategy_lineage("does-not-exist")


class TestCreateStrategySnapshot(Phase4TestBase):
	def test_snapshot_rejects_non_active_version(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		with self.assertRaises(frappe.ValidationError):
			consumer.create_strategy_snapshot(
				plan_version_id=version, objective_id=nodes["objective"], correlation_key=f"corr-{self.suffix}"
			)

	def test_snapshot_happy_path_and_idempotent_replay(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")
		key = f"corr-{self.suffix}"

		first = api.create_strategy_snapshot(version, nodes["objective"], key)
		self.assertEqual(first["objective_id"], nodes["objective"])
		self.assertEqual(first["correlation_key"], key)
		self.assertEqual([p["type"] for p in first["path"]], ["Pillar", "Programme", "Strategic Objective"])

		second = api.create_strategy_snapshot(version, nodes["objective"], key)
		self.assertEqual(first, second)
		self.assertEqual(
			frappe.db.count("Strategy Command Journal", {"idempotency_key": key}), 1
		)
		self.assertEqual(
			frappe.db.count(
				"Audit Event", {"document_type": "Strategy Node", "document_name": nodes["objective"]}
			),
			1,
		)

	def test_snapshot_rejects_wrong_node_type(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")
		with self.assertRaises(frappe.ValidationError):
			api.create_strategy_snapshot(version, nodes["outcome"], f"corr-outcome-{self.suffix}")


class TestBudgetTargetReferenceRebuilt(Phase4TestBase):
	"""XMOD-STR-001 — the Phase 1-flagged regression: Budget Line's
	strategy-linking depends on validate_strategy_reference/
	build_strategy_reference, which targeted the pre-rebuild schema."""

	def test_validate_and_build_strategy_reference_against_active_version(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")

		result = contracts.validate_strategy_reference(
			{"plan_version_id": version, "node_id": nodes["target"], "node_type": "PerformanceTarget"}
		)
		self.assertTrue(result["valid"])
		self.assertTrue(result["selectable_for_new"])
		self.assertEqual(result["reference"]["node_id"], nodes["target"])
		self.assertEqual(
			[p["type"] for p in result["reference"]["path"]],
			["Pillar", "Programme", "StrategicObjective", "StrategicOutcome", "PerformanceIndicator", "PerformanceTarget"],
		)

	def test_apply_budget_primary_strategy_reference_sets_fields(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")

		class _FakeBudgetLine:
			primary_target_id = None
			primary_target_code = None
			primary_target_name = None
			primary_plan_version_id = None
			primary_snapshot_label = None
			primary_strategy_linked = 0

		doc = _FakeBudgetLine()
		ref = consumer.apply_budget_primary_strategy_reference(doc, nodes["target"])
		self.assertEqual(doc.primary_target_id, nodes["target"])
		self.assertEqual(doc.primary_plan_version_id, version)
		self.assertEqual(doc.primary_strategy_linked, 1)
		self.assertIsNotNone(ref)


class TestPlanDraftAndSuccessorCommands(Phase4TestBase):
	def test_save_strategy_plan_draft_create_then_update(self):
		author = self._user("author")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		frappe.set_user(author)

		created = save_strategy_plan_draft(
			{
				"procuring_entity_id": PE,
				"title": f"New Draft Plan {self.suffix}",
				"plan_role": "Primary",
				"period_start": "2028-07-01",
				"period_end": "2033-06-30",
				"effective_from": "2028-07-01",
				"effective_to": "2033-06-30",
			}
		)
		self._track(frappe.get_doc("Strategic Plan Version", created["version"]["name"]))
		self._track(frappe.get_doc("Strategic Plan", created["plan"]["plan_id"]))
		self.assertEqual(created["version"]["status"], "Draft")

		updated = save_strategy_plan_draft(
			{"plan_id": created["plan"]["plan_id"], "title": "Renamed Draft Plan"}
		)
		self.assertEqual(updated["plan"]["title"], "Renamed Draft Plan")

	def test_save_strategy_plan_draft_stale_write_rejected(self):
		author = self._user("author2")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		plan, version = self._plan_and_version()
		stale = str(frappe.db.get_value("Strategic Plan Version", version, "modified"))
		frappe.db.set_value("Strategic Plan Version", version, "return_reason", "touch")
		frappe.set_user(author)
		with self.assertRaises(frappe.ValidationError):
			save_strategy_plan_draft(
				{"plan_id": plan, "plan_version_id": version, "title": "x"}, expected_version=stale
			)

	def test_create_successor_version_clones_hierarchy_with_remapped_ids(self):
		approver_author = self._user("succ_author")
		self._assign(approver_author, "CAP-STRATEGY-AUTHOR")
		plan, v1 = self._plan_and_version()
		nodes = self._fill_hierarchy(v1)
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")

		frappe.set_user(approver_author)
		out = create_strategy_successor_version(plan)
		self._track(frappe.get_doc("Strategic Plan Version", out["name"]))
		self.assertEqual(out["status"], "Draft")

		cloned_nodes = frappe.get_all(
			"Strategy Node", filters={"plan_version_id": out["name"]}, fields=["name", "node_type", "parent_node_id"]
		)
		self._cleanup.extend(("Strategy Node", n.name) for n in cloned_nodes)
		self.assertEqual(len(cloned_nodes), 4)
		objective_clone = next(n for n in cloned_nodes if n.node_type == "Strategic Objective")
		self.assertNotEqual(objective_clone.name, nodes["objective"])

		cloned_indicators = frappe.get_all(
			"Performance Indicator", filters={"plan_version_id": out["name"]}, fields=["name", "measures_node_id"]
		)
		self._cleanup.extend(("Performance Indicator", i.name) for i in cloned_indicators)
		self.assertEqual(len(cloned_indicators), 1)
		outcome_clone = next(n for n in cloned_nodes if n.node_type == "Strategic Outcome")
		self.assertEqual(cloned_indicators[0].measures_node_id, outcome_clone.name)

		cloned_targets = frappe.get_all(
			"Performance Target", filters={"indicator_id": cloned_indicators[0].name}, fields=["name"]
		)
		self._cleanup.extend(("Performance Target", t.name) for t in cloned_targets)
		self.assertEqual(len(cloned_targets), 1)

	def test_create_successor_version_blocked_while_open_successor_exists(self):
		author = self._user("succ_author2")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		plan, v1 = self._plan_and_version()
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")
		frappe.set_user(author)
		out = create_strategy_successor_version(plan)
		self._track(frappe.get_doc("Strategic Plan Version", out["name"]))
		with self.assertRaises(frappe.ValidationError):
			create_strategy_successor_version(plan)


class TestSaveStructureDraft(Phase4TestBase):
	def test_batch_create_with_client_id_references_then_delete_guard(self):
		author = self._user("structure_author")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		_, version = self._plan_and_version()
		frappe.set_user(author)

		out = save_strategy_structure_draft(
			version,
			nodes=[
				{"client_id": "$pillar", "node_type": "Pillar", "title": "P", "display_order": 1},
				{
					"client_id": "$prog",
					"node_type": "Programme",
					"title": "Prog",
					"display_order": 2,
					"parent_node_id": "$pillar",
				},
			],
		)
		self._cleanup.extend(("Strategy Node", n) for n in out["nodes"])
		self.assertEqual(len(out["nodes"]), 2)
		pillar_id, prog_id = out["nodes"]
		self.assertEqual(frappe.db.get_value("Strategy Node", prog_id, "parent_node_id"), pillar_id)

		# Cannot delete the pillar while it still has the programme as a child.
		with self.assertRaises(frappe.ValidationError):
			save_strategy_structure_draft(version, deletes=[{"doctype": "Strategy Node", "name": pillar_id}])

		out2 = save_strategy_structure_draft(
			version, deletes=[{"doctype": "Strategy Node", "name": prog_id}]
		)
		self.assertIn(prog_id, out2["deleted"])
		out3 = save_strategy_structure_draft(
			version, deletes=[{"doctype": "Strategy Node", "name": pillar_id}]
		)
		self.assertIn(pillar_id, out3["deleted"])


class TestLifecycleCommandDispatch(Phase4TestBase):
	"""Confirms the §10.1 API dispatchers wire correctly to the Phase 2
	engine — lifecycle rules themselves are exhaustively covered there."""

	def test_submit_and_activate_via_api_dispatchers(self):
		author = self._user("dispatch_author")
		approver = self._user("dispatch_approver")
		self._assign(author, "CAP-STRATEGY-AUTHOR")
		self._assign(approver, "CAP-STRATEGY-APPROVAL-AUTHORITY")
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)

		frappe.set_user(author)
		out = api.submit_strategy_version(version)
		self.assertEqual(out["status"], "In Review")

		frappe.db.set_value("Strategic Plan Version", version, "status", "Approved")
		frappe.set_user(approver)
		out = api.activate_strategy_version(version)
		self.assertEqual(out["status"], "Active")
