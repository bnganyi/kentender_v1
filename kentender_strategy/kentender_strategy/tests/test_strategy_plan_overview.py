# Copyright (c) 2026, KenTender and contributors
"""STR-UI-02 Plan Overview — get_plan_overview + create_successor_version."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import get_plan_overview, get_strategy_tree
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_writes import create_successor_version


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_strategy_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


def _delete_plan_version(plan_id: str | None):
	if not plan_id or not frappe.db.exists("Strategic Plan", plan_id):
		return
	# Child records first
	for dt, filt in (
		("Strategy Value Commitment", {"plan_version": plan_id}),
		("Performance Target", {"plan_version": plan_id}),
		("Performance Indicator", {"plan_version": plan_id}),
		("Strategic Outcome", {"plan_version": plan_id}),
		("Strategy Sub Programme", {"plan_version": plan_id}),
		("Strategy Programme", {"plan_version": plan_id}),
		("Strategy Audit Event", {"plan_version": plan_id}),
	):
		for name in frappe.get_all(dt, filters=filt, pluck="name"):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
	frappe.delete_doc("Strategic Plan", plan_id, force=True, ignore_permissions=True)


def _purge_open_successors(plan_code: str):
	for row in frappe.get_all(
		"Strategic Plan",
		filters={
			"plan_code": plan_code,
			"status": ["in", ["Draft", "Returned", "Submitted"]],
			"version_number": [">", 1],
		},
		pluck="name",
	):
		_delete_plan_version(row)


class TestStrategyPlanOverview(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan_id = cls.seed["plan"]
		# Ensure Active for overview/successor semantics
		if cls.plan_id:
			status = frappe.db.get_value("Strategic Plan", cls.plan_id, "status")
			if status != "Active":
				frappe.db.set_value("Strategic Plan", cls.plan_id, "status", "Active")
		_purge_open_successors(STRATEGY_PLAN_CODE)

	def tearDown(self):
		frappe.set_user("Administrator")
		_purge_open_successors(STRATEGY_PLAN_CODE)
		super().tearDown()

	def test_get_plan_overview_moh_seed_fields_counts_and_attention(self):
		_ensure_user("str.officer.ov@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.ov@example.com")
		dto = get_plan_overview(plan_code=STRATEGY_PLAN_CODE)
		plan = dto["plan"]
		self.assertEqual(plan["code"], STRATEGY_PLAN_CODE)
		self.assertEqual(plan["status"], "Active")
		self.assertTrue(plan.get("name"))
		self.assertTrue(plan.get("version_number"))
		self.assertIsInstance(plan.get("procuring_entity"), dict)
		self.assertEqual(plan["procuring_entity"]["id"], self.pe)
		self.assertTrue(plan["procuring_entity"].get("name"))
		counts = dto["counts"]
		self.assertGreaterEqual(counts["programmes"], 1)
		self.assertGreaterEqual(counts["outcomes"], 1)
		self.assertGreaterEqual(counts["indicators"], 1)
		self.assertGreaterEqual(counts["targets"], 1)
		self.assertIn("sub_programmes", counts)
		cs = dto["commitments_summary"]
		self.assertGreaterEqual(cs["total"], 1)
		self.assertGreaterEqual(cs["required"], 0)
		self.assertGreaterEqual(cs["recommended"], 0)
		self.assertGreaterEqual(len(dto["attention_rows"]), 1)
		row = dto["attention_rows"][0]
		self.assertTrue(row["target"]["code"])
		self.assertTrue(row["target"]["name"])
		self.assertNotEqual(row["target"]["code"], row["target"]["id"])
		self.assertIn(row["action"], ("view-measurement", "submit-measurement", "review-measurement"))
		self.assertTrue(dto["capabilities"]["create_successor"])
		self.assertTrue(dto["lock"]["show"])

	def test_resolve_plan_by_docname_or_code(self):
		dto_by_code = get_plan_overview(plan_code=STRATEGY_PLAN_CODE)
		dto_by_id = get_plan_overview(plan_version=self.plan_id)
		# Ambiguous route token: docname passed as plan_code
		dto_token = get_plan_overview(plan_code=self.plan_id)
		self.assertEqual(dto_by_code["plan"]["id"], self.plan_id)
		self.assertEqual(dto_by_id["plan"]["id"], self.plan_id)
		self.assertEqual(dto_token["plan"]["id"], self.plan_id)

	def test_viewer_cannot_create_successor(self):
		_ensure_user("str.viewer.ov@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.ov@example.com")
		dto = get_plan_overview(plan_code=STRATEGY_PLAN_CODE)
		self.assertFalse(dto["capabilities"]["create_successor"])
		with self.assertRaises(frappe.PermissionError):
			create_successor_version(self.plan_id)

	def test_entity_scope_blocks_overview_and_successor(self):
		if not frappe.db.exists("Procuring Entity", {"entity_code": "OTHER-OV"}):
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": "OTHER-OV",
					"entity_name": "Other PE Overview",
				}
			).insert(ignore_permissions=True)
		other_pe = frappe.db.get_value("Procuring Entity", {"entity_code": "OTHER-OV"}, "name")
		_ensure_user("str.officer.ov.other@example.com", ["Strategy Officer"], other_pe)
		frappe.set_user("str.officer.ov.other@example.com")
		with self.assertRaises(frappe.PermissionError):
			get_plan_overview(plan_code=STRATEGY_PLAN_CODE)
		with self.assertRaises(frappe.PermissionError):
			create_successor_version(self.plan_id)

	def test_create_successor_clones_hierarchy_and_blocks_second(self):
		_ensure_user("str.officer.succ@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.succ@example.com")
		src_tree = get_strategy_tree(plan_version=self.plan_id)
		src_counts = src_tree["counts"]
		src_commitments = frappe.db.count("Strategy Value Commitment", {"plan_version": self.plan_id})

		result = create_successor_version(self.plan_id)
		self.assertTrue(result.get("ok"))
		new_plan = result["plan"]
		self.addCleanup(lambda: _delete_plan_version(new_plan["id"]))
		self.assertEqual(new_plan["code"], STRATEGY_PLAN_CODE)
		self.assertEqual(new_plan["status"], "Draft")
		self.assertEqual(int(new_plan["version_number"]), int(src_tree["plan"]["version_number"]) + 1)
		self.assertEqual(new_plan["supersedes_plan_version"], self.plan_id)

		# Active source unchanged
		self.assertEqual(frappe.db.get_value("Strategic Plan", self.plan_id, "status"), "Active")

		new_tree = get_strategy_tree(plan_version=new_plan["id"])
		self.assertEqual(new_tree["counts"]["programmes"], src_counts["programmes"])
		self.assertEqual(new_tree["counts"]["targets"], src_counts["targets"])
		self.assertEqual(new_tree["counts"]["outcomes"], src_counts["outcomes"])
		self.assertEqual(
			frappe.db.count("Strategy Value Commitment", {"plan_version": new_plan["id"]}),
			src_commitments,
		)
		# Measurements stay on the Active version only
		self.assertEqual(
			frappe.db.count("Performance Measurement", {"plan_version": new_plan["id"]}),
			0,
		)

		audit = frappe.get_all(
			"Strategy Audit Event",
			filters={"plan_version": new_plan["id"], "event_type": "SuccessorCreated"},
			fields=["name", "actor"],
		)
		self.assertEqual(len(audit), 1)
		self.assertEqual(audit[0].actor, "str.officer.succ@example.com")

		# Second open successor rejected
		with self.assertRaises(frappe.ValidationError):
			create_successor_version(self.plan_id)

		ov = get_plan_overview(plan_version=self.plan_id)
		self.assertFalse(ov["capabilities"]["create_successor"])
