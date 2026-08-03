# Copyright (c) 2026, KenTender and contributors
"""STR-UI-01 Portfolio service contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import (
	create_plan,
	get_strategy_portfolio,
	list_strategy_plans,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles


class TestStrategyPortfolioUi01(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()

	def test_portfolio_strip_counts_shape(self):
		pf = get_strategy_portfolio(procuring_entity=self.seed["procuring_entity"])
		counts = pf["counts"]
		for key in (
			"active",
			"submitted",
			"draft",
			"expiring",
			"measurements_due",
			"measurement_attention",
		):
			self.assertIn(key, counts)
			self.assertIsInstance(counts[key], int)
		self.assertGreaterEqual(counts["active"], 1)
		self.assertTrue(pf.get("capabilities", {}).get("create_plan"))

	def test_plans_include_attention_and_period(self):
		rows = list_strategy_plans(procuring_entity=self.seed["procuring_entity"])
		moh = next(r for r in rows if r["code"] == STRATEGY_PLAN_CODE)
		self.assertEqual(moh["status"], "Active")
		self.assertIn("attention", moh)
		self.assertIn("attention_kind", moh)
		self.assertTrue(moh.get("start_date"))
		self.assertTrue(moh.get("end_date"))
		self.assertIn("version_number", moh)

	def test_list_filters_search_and_status(self):
		rows = list_strategy_plans(
			procuring_entity=self.seed["procuring_entity"],
			search="MOH-SP-2026",
			status="Active",
		)
		self.assertTrue(rows)
		self.assertTrue(all(r["status"] == "Active" for r in rows))
		self.assertTrue(any(r["code"] == STRATEGY_PLAN_CODE for r in rows))
		empty = list_strategy_plans(
			procuring_entity=self.seed["procuring_entity"],
			search="NO-SUCH-PLAN-ZZZ",
		)
		self.assertEqual(empty, [])

	def test_my_work_includes_seeded_attention(self):
		pf = get_strategy_portfolio(procuring_entity=self.seed["procuring_entity"])
		self.assertIsInstance(pf["my_work"], list)
		# Seed has verified At risk Sep measurement + CA — expect measurement or CA work item
		kinds = {i.get("type") for i in pf["my_work"]}
		self.assertTrue(kinds.intersection({"plan_review", "submit_measurement", "resolve_target", "verify_measurement"}))

	def test_create_plan_returns_code_and_draft(self):
		pe = self.seed["procuring_entity"]
		code = f"UI01-CREATE-{frappe.generate_hash(length=6).upper()}"
		created = create_plan(
			{
				"plan_code": code,
				"title": "UI01 Create Fixture",
				"procuring_entity": pe,
				"plan_type": "Entity Strategic Plan",
				"start_date": "2026-07-01",
				"end_date": "2027-06-30",
			}
		)
		self.assertTrue(created.get("ok"))
		self.assertEqual(created["plan"]["code"], code)
		self.assertEqual(created["plan"]["status"], "Draft")
		self.addCleanup(
			lambda: frappe.delete_doc(
				"Strategic Plan", created["plan"]["id"], force=True, ignore_permissions=True
			)
		)
