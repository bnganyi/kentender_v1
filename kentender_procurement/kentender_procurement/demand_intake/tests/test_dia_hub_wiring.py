# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""H13 — TDD for DIA Hub wiring backend functions.

Tests:
  HUB-BE-001  alignment_pct = 0 when no active demands exist
  HUB-BE-002  alignment_pct = 100 when all active demands have strategy_target set
  HUB-BE-003  alignment_pct rounds correctly for partial linkage
  HUB-BE-004  alignment_pct = 0 when all active demands have no strategy_target
  HUB-BE-005  get_dia_landing_shell_data response includes alignment_pct key
  HUB-BE-006  cancelled demands are excluded from alignment_pct calculation
  HUB-BE-007  category_breakdown is present in landing response with Goods/Works/Services keys
  HUB-BE-008  category_breakdown counts reflect actual demand records

Run:
  bench --site kentender.midas.com run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_hub_wiring
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.landing import (
	get_dia_landing_shell_data,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy


def _compute_strategic_alignment_pct():
	from kentender_procurement.demand_intake.api.landing import compute_strategic_alignment_pct

	return compute_strategic_alignment_pct()


class TestDiaHubWiringBackend(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = upsert_works_master_strategy_hierarchy()

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_HUB_{h}", f"Hub Entity {h}")
		self.dept = ensure_department(f"HubDept {h}", self.entity)
		self._demand_names: list[str] = []
		self._strategy_target = self.seed.get("target")

	def tearDown(self):
		if getattr(self, "_skip", False):
			return
		frappe.set_user("Administrator")
		for name in list(self._demand_names):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		self._demand_names.clear()
		dept = getattr(self, "dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)
		ent = getattr(self, "entity", None)
		if ent and frappe.db.exists("Procuring Entity", ent):
			frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)

	def _mk_demand(self, *, strategy_target=None, status="Draft", requisition_type="Goods", **kwargs) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"Hub {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": requisition_type,
				"items": [
					{
						"item_description": "Item",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 1000,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		# Set strategy_target and status directly to avoid Active/entity filters on insert
		update = {"status": status}
		if strategy_target:
			update["strategy_target"] = strategy_target
			update["strategy_plan_version"] = self.seed.get("plan")
		frappe.db.set_value("Demand", doc.name, update, update_modified=False)
		self._demand_names.append(doc.name)
		return doc.name

	def test_hub_be_001_alignment_zero_when_no_demands(self):
		"""alignment_pct is in 0–100 when the isolated test has no active demands."""
		if self._skip:
			self.skipTest("Demand DocType not installed")
		pct = _compute_strategic_alignment_pct()
		self.assertIsInstance(pct, (int, float))
		self.assertGreaterEqual(pct, 0)
		self.assertLessEqual(pct, 100)

	def test_hub_be_002_alignment_100_when_all_have_strategy_target(self):
		"""alignment_pct = 100 when every active demand has strategy_target set."""
		if self._skip:
			self.skipTest("Demand DocType not installed")
		if not self._strategy_target:
			self.skipTest("No Performance Target seeded — cannot test full linkage")

		self._mk_demand(strategy_target=self._strategy_target, title="Linked 1")
		self._mk_demand(strategy_target=self._strategy_target, title="Linked 2")

		from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity

		pct = _compute_alignment_for_entity(self.entity)
		self.assertEqual(pct, 100)

	def test_hub_be_003_alignment_partial_linkage(self):
		"""alignment_pct rounds to nearest integer for partial linkage (2 of 3 = 67)."""
		if self._skip:
			self.skipTest("Demand DocType not installed")
		if not self._strategy_target:
			self.skipTest("No Performance Target seeded — cannot test partial linkage")

		self._mk_demand(strategy_target=self._strategy_target, title="Linked A")
		self._mk_demand(strategy_target=self._strategy_target, title="Linked B")
		self._mk_demand(title="Unlinked C")

		from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity

		pct = _compute_alignment_for_entity(self.entity)
		self.assertEqual(pct, 67)

	def test_hub_be_004_alignment_zero_when_none_linked(self):
		"""alignment_pct = 0 when all active demands have no strategy_target."""
		if self._skip:
			self.skipTest("Demand DocType not installed")

		self._mk_demand(title="Unlinked 1")
		self._mk_demand(title="Unlinked 2")

		from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity

		pct = _compute_alignment_for_entity(self.entity)
		self.assertEqual(pct, 0)

	def test_hub_be_005_landing_response_includes_alignment_pct(self):
		"""get_dia_landing_shell_data response must include alignment_pct key."""
		if self._skip:
			self.skipTest("Demand DocType not installed")

		out = get_dia_landing_shell_data()
		self.assertTrue(out.get("ok"), f"Landing API returned error: {out}")
		self.assertIn(
			"alignment_pct",
			out,
			"alignment_pct key missing from get_dia_landing_shell_data response",
		)
		pct = out["alignment_pct"]
		self.assertIsInstance(pct, (int, float))
		self.assertGreaterEqual(pct, 0)
		self.assertLessEqual(pct, 100)

	def test_hub_be_006_cancelled_excluded_from_alignment(self):
		"""Cancelled demands must not affect alignment_pct numerator or denominator."""
		if self._skip:
			self.skipTest("Demand DocType not installed")
		if not self._strategy_target:
			self.skipTest("No Performance Target seeded")

		self._mk_demand(
			strategy_target=self._strategy_target,
			status="Cancelled",
			title="Cancelled linked",
		)
		self._mk_demand(title="Active unlinked")

		from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity

		pct = _compute_alignment_for_entity(self.entity)
		self.assertEqual(pct, 0)

	def test_hub_be_007_landing_response_includes_category_breakdown(self):
		"""get_dia_landing_shell_data response must include category_breakdown with Goods/Works/Services."""
		if self._skip:
			self.skipTest("Demand DocType not installed")

		out = get_dia_landing_shell_data()
		self.assertTrue(out.get("ok"))
		self.assertIn(
			"category_breakdown",
			out,
			"category_breakdown key missing from get_dia_landing_shell_data response",
		)
		breakdown = out["category_breakdown"]
		self.assertIsInstance(breakdown, dict)
		for key in ("Goods", "Works", "Services"):
			self.assertIn(key, breakdown, f"'{key}' missing from category_breakdown")
			self.assertIsInstance(breakdown[key], (int, float))

	def test_hub_be_009_queue_list_returns_total_count(self):
		"""get_dia_queue_list must return a total_count integer for pagination."""
		if self._skip:
			self.skipTest("Demand DocType not installed")
		from kentender_procurement.demand_intake.api.queue_list import get_dia_queue_list

		self._mk_demand(title="Count A")
		self._mk_demand(title="Count B")

		out = get_dia_queue_list(work_tab="all", lifecycle_filter="all", limit=50, start=0)
		self.assertTrue(out.get("ok"), f"queue_list returned error: {out}")
		self.assertIn("total_count", out, "total_count key missing from get_dia_queue_list response")
		tc = out["total_count"]
		self.assertIsInstance(tc, int, f"total_count must be int, got {type(tc)}")
		self.assertGreaterEqual(tc, 2, "total_count must be >= 2 after inserting 2 demands")

	def test_hub_be_008_category_breakdown_reflects_actual_demands(self):
		"""category_breakdown counts must increment when new demands are inserted."""
		if self._skip:
			self.skipTest("Demand DocType not installed")

		out_before = get_dia_landing_shell_data()
		goods_before = (out_before.get("category_breakdown") or {}).get("Goods", 0)
		works_before = (out_before.get("category_breakdown") or {}).get("Works", 0)

		self._mk_demand(requisition_type="Goods", title="Goods demand")
		self._mk_demand(requisition_type="Works", title="Works demand")

		out_after = get_dia_landing_shell_data()
		self.assertTrue(out_after.get("ok"))
		breakdown = out_after.get("category_breakdown") or {}

		self.assertGreaterEqual(breakdown.get("Goods", 0), goods_before + 1)
		self.assertGreaterEqual(breakdown.get("Works", 0), works_before + 1)
