# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning Hub ledger demo seed contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.planning_hub import (
	get_pp_planning_hub_plans_page,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PLAN_CANCELLED,
	PLAN_CLOSED,
	PLAN_DRAFT,
	PLAN_SUPERSEDED,
)
from kentender_procurement.procurement_planning.seeds.seed_planning_hub_ledger_demo import (
	_DEMO_PLANS,
	_KEEP_PLAN_CODES,
	seed_planning_hub_ledger_demo,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PLAN_CODE as MASTER_PLAN_CODE,
)


class TestSeedPlanningHubLedgerDemo(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", MASTER_PLAN_CODE):
			self.skipTest(f"{MASTER_PLAN_CODE} not seeded")

	def test_seed_removes_non_canonical_plans_and_upserts_status_mix(self) -> None:
		junk_code = f"PP-CMP-{frappe.generate_hash()[:6]}"
		frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_code": junk_code,
				"plan_name": "Gov completeness",
				"fiscal_year": 2029,
				"procuring_entity": frappe.db.get_value(
					"Procurement Plan", MASTER_PLAN_CODE, "procuring_entity"
				),
				"currency": "KES",
				"status": PLAN_DRAFT,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()

		out = seed_planning_hub_ledger_demo()
		self.assertTrue(out.get("ok"))
		self.assertIn(junk_code, out.get("removed_plan_codes") or [])
		self.assertFalse(frappe.db.exists("Procurement Plan", junk_code))

		for code in _KEEP_PLAN_CODES:
			self.assertTrue(
				frappe.db.exists("Procurement Plan", code),
				msg=f"missing canonical/demo plan {code}",
			)

		statuses = {
			(row.get("plan_code") or row.get("name") or "").strip(): (row.get("status") or "").strip()
			for row in frappe.get_all(
				"Procurement Plan",
				filters={"plan_code": ["in", list(_KEEP_PLAN_CODES)]},
				fields=["name", "plan_code", "status"],
			)
		}
		self.assertEqual(statuses[MASTER_PLAN_CODE], "Active")
		for spec in _DEMO_PLANS:
			self.assertEqual(statuses[spec["plan_code"]], spec["status"])

	def test_hub_ledger_lists_demo_status_labels(self) -> None:
		seed_planning_hub_ledger_demo()
		frappe.set_user("Administrator")
		page = get_pp_planning_hub_plans_page(limit=50)
		self.assertTrue(page.get("ok"))
		self.assertEqual(page.get("total"), len(_KEEP_PLAN_CODES))
		labels = {row.get("code"): row.get("status_label") for row in page.get("rows") or []}
		self.assertEqual(labels.get(MASTER_PLAN_CODE), "Active")
		self.assertEqual(labels.get("PLAN-MOH-2027"), PLAN_DRAFT)
		self.assertEqual(labels.get("PLAN-MOH-2025"), PLAN_CLOSED)
		self.assertEqual(labels.get("PLAN-MOH-2024"), PLAN_SUPERSEDED)
		self.assertEqual(labels.get("PLAN-MOH-2023-CXL"), PLAN_CANCELLED)
