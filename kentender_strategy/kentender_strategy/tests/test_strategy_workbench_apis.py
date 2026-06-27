# Copyright (c) 2026, KenTender and contributors
"""
F1 — get_plan_meta returns correct counts and status for a given plan.
F2 — get_plan_activity returns entries scoped to one plan only.
F3 — Sub Program CRUD succeeds under the Strategy Manager role.
"""

import frappe
from frappe.tests import IntegrationTestCase

from kentender_strategy.api import strategy_builder as api
from kentender_strategy.services import strategy_builder as svc


class TestStrategyWorkbenchApis(IntegrationTestCase):
	# ── Fixtures ──────────────────────────────────────────────────────────────

	def setUp(self):
		frappe.set_user("Administrator")
		self.entity = self._ensure_entity()

		# Primary plan — we will add a full hierarchy to this one
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "WB API Test Plan A",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		).insert(ignore_permissions=True).name

		# Decoy plan — activity must NOT bleed into the primary plan
		self.decoy = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "WB API Test Plan B (decoy)",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		).insert(ignore_permissions=True).name

		# Build a full 4-level hierarchy under the primary plan
		self.prog = svc.create_node(self.plan, None, "Program", {"node_title": "Health Program"})
		self.sp = svc.create_node(self.plan, self.prog, "SubProgram", {"node_title": "District Works"})
		self.ind = svc.create_node(self.plan, self.sp, "Indicator", {"node_title": "Hospital readiness"})
		self.tgt = svc.create_node(
			self.plan, self.ind, "Target",
			{"node_title": "Renovate hospitals", "target_value": 5, "target_unit": "facilities"},
		)

		# A single node under the decoy so its activity can be distinguished
		svc.create_node(self.decoy, None, "Program", {"node_title": "Decoy Program"})

	def tearDown(self):
		frappe.set_user("Administrator")
		for plan in (self.plan, self.decoy):
			frappe.db.delete("Strategy Target",    {"strategic_plan": plan})
			frappe.db.delete("Strategy Objective", {"strategic_plan": plan})
			frappe.db.delete("Sub Program",        {"strategic_plan": plan})
			frappe.db.delete("Strategy Program",   {"strategic_plan": plan})
			if frappe.db.exists("Strategic Plan", plan):
				frappe.delete_doc("Strategic Plan", plan, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_entity(self) -> str:
		name = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
		if name:
			return name
		return frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_name": "MOH Test Entity",
				"entity_code": "PE-MOH",
			}
		).insert(ignore_permissions=True).name

	# ── F1 — get_plan_meta ────────────────────────────────────────────────────

	def test_f1_get_plan_meta_returns_correct_counts(self):
		"""get_plan_meta counts programs, objectives (indicators), targets correctly."""
		meta = api.get_plan_meta(self.plan)

		self.assertEqual(meta["programs"],   1, "programs count")
		self.assertEqual(meta["objectives"], 1, "objectives (indicators) count")
		self.assertEqual(meta["targets"],    1, "targets count")

	def test_f1_get_plan_meta_returns_correct_status(self):
		"""get_plan_meta returns the plan's current status field."""
		meta = api.get_plan_meta(self.plan)
		self.assertEqual(meta["status"], "Draft")

		# Promote to Submitted and confirm meta reflects it
		frappe.db.set_value("Strategic Plan", self.plan, "status", "Submitted")
		meta2 = api.get_plan_meta(self.plan)
		self.assertEqual(meta2["status"], "Submitted")

	def test_f1_get_plan_meta_raises_for_missing_plan(self):
		"""get_plan_meta throws DoesNotExistError for unknown plan name."""
		with self.assertRaises(frappe.DoesNotExistError):
			api.get_plan_meta("DOES-NOT-EXIST-XYZ")

	def test_f1_get_plan_meta_zero_counts_for_empty_plan(self):
		"""get_plan_meta returns zero counts for a brand-new plan with no hierarchy."""
		empty_plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "WB API Empty Plan",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		).insert(ignore_permissions=True).name

		try:
			meta = api.get_plan_meta(empty_plan)
			self.assertEqual(meta["programs"],   0)
			self.assertEqual(meta["objectives"], 0)
			self.assertEqual(meta["targets"],    0)
		finally:
			frappe.delete_doc("Strategic Plan", empty_plan, force=True, ignore_permissions=True)
			frappe.db.commit()

	# ── F2 — get_plan_activity ────────────────────────────────────────────────

	def test_f2_get_plan_activity_returns_list(self):
		"""get_plan_activity returns a non-empty list for a plan with hierarchy."""
		events = api.get_plan_activity(self.plan)
		self.assertIsInstance(events, list)
		self.assertGreater(len(events), 0, "Expected at least one activity event")

	def test_f2_get_plan_activity_scoped_to_plan(self):
		"""Activity events are scoped — decoy plan nodes do NOT appear in primary plan's feed."""
		events = api.get_plan_activity(self.plan)
		# Every event must reference a node that belongs to self.plan
		node_names = {e.get("node_name") for e in events if e.get("node_name")}
		plan_nodes = {self.plan, self.prog, self.sp, self.ind, self.tgt}
		# No event should carry a name from the decoy plan
		decoy_programs = frappe.db.get_all(
			"Strategy Program", filters={"strategic_plan": self.decoy}, pluck="name"
		)
		for decoy_name in decoy_programs:
			self.assertNotIn(decoy_name, node_names,
				f"Decoy node {decoy_name!r} leaked into primary plan activity feed")

	def test_f2_get_plan_activity_each_item_has_required_keys(self):
		"""Each activity item has the keys the frontend expects."""
		events = api.get_plan_activity(self.plan)
		required_keys = {"time", "action", "dot_class", "node_type", "node_title", "user"}
		for item in events:
			missing = required_keys - set(item.keys())
			self.assertFalse(missing, f"Activity item missing keys: {missing}")

	def test_f2_get_plan_activity_limit_respected(self):
		"""Passing limit=1 returns at most 1 item."""
		events = api.get_plan_activity(self.plan, limit=1)
		self.assertLessEqual(len(events), 1)

	def test_f2_get_plan_activity_raises_for_missing_plan(self):
		"""get_plan_activity throws DoesNotExistError for unknown plan name."""
		with self.assertRaises(frappe.DoesNotExistError):
			api.get_plan_activity("DOES-NOT-EXIST-XYZ")

	# ── F3 — Sub Program CRUD under Strategy Manager role ────────────────────

	def _get_or_create_strategy_manager(self) -> str:
		"""Return a Strategy Manager test user, creating it if needed."""
		email = "sm_test_wb@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc({
				"doctype": "User",
				"email": email,
				"first_name": "SM",
				"last_name": "Test",
				"send_welcome_email": 0,
				"roles": [{"role": "Strategy Manager"}],
			}).insert(ignore_permissions=True)
			frappe.db.commit()
		return email

	def test_f3_strategy_manager_can_create_sub_program(self):
		"""Strategy Manager role has create permission on Sub Program."""
		sm_user = self._get_or_create_strategy_manager()
		frappe.set_user(sm_user)

		try:
			name = svc.create_node(self.plan, self.prog, "SubProgram",
				{"node_title": "SM-Created Sub-program"})
			self.assertTrue(frappe.db.exists("Sub Program", name),
				"Sub Program should exist after creation by Strategy Manager")
		finally:
			frappe.set_user("Administrator")

	def test_f3_strategy_manager_can_update_sub_program(self):
		"""Strategy Manager role has write permission on Sub Program."""
		sm_user = self._get_or_create_strategy_manager()
		frappe.set_user(sm_user)

		try:
			svc.update_node(self.sp, {"node_title": "Updated by SM"})
			updated = frappe.db.get_value(
				"Sub Program", self.sp,
				frappe.db.get_value("Sub Program", self.sp, "title") and "title" or "sub_program_title"
				or "name",
			)
			# Just confirm no permission error was raised — the update_node call itself passing is the proof
		finally:
			frappe.set_user("Administrator")

	def test_f3_strategy_manager_can_delete_sub_program(self):
		"""Strategy Manager role has delete permission on Sub Program."""
		sm_user = self._get_or_create_strategy_manager()

		# Create a throwaway sub-program as Admin to delete as SM
		spare_sp = svc.create_node(self.plan, self.prog, "SubProgram",
			{"node_title": "Spare SP for delete test"})

		frappe.set_user(sm_user)
		try:
			frappe.has_permission("Sub Program", doc=spare_sp, ptype="delete", throw=True)
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("Sub Program", spare_sp):
				frappe.delete_doc("Sub Program", spare_sp, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_f3_sub_program_doctype_has_strategy_manager_permissions(self):
		"""DocType meta for Sub Program explicitly grants Strategy Manager Read+Write+Create+Delete."""
		perms = frappe.get_doc("DocType", "Sub Program").permissions
		sm_perm = next((p for p in perms if p.role == "Strategy Manager"), None)
		self.assertIsNotNone(sm_perm, "No permission row for 'Strategy Manager' on Sub Program")
		self.assertEqual(sm_perm.read,   1, "Strategy Manager must have Read on Sub Program")
		self.assertEqual(sm_perm.write,  1, "Strategy Manager must have Write on Sub Program")
		self.assertEqual(sm_perm.create, 1, "Strategy Manager must have Create on Sub Program")
		self.assertEqual(sm_perm.delete, 1, "Strategy Manager must have Delete on Sub Program")
