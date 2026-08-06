# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-002 — Approved demand planning drawer API (UI spec §8 / PP2-SMOKE-UI-004)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import DEMAND_TITLE
from kentender_procurement.procurement_planning.api.approved_demands import (
	get_pp_approved_demand_planning_drawer,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	FISCAL_YEAR,
	PLAN_CODE,
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.approved_demand_drawer import (
	get_approved_demand_planning_drawer,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


def _ensure_works_demand_queue_ready() -> None:
	clear_master_planning_seed()
	for row in frappe.get_all(
		"Procurement Package Line",
		filters={"demand_item_code": DEMAND_ITEM_CODE, "is_active": 1},
		fields=["name"],
	):
		frappe.db.set_value(
			"Procurement Package Line",
			row.name,
			"is_active",
			0,
			update_modified=False,
		)
	demand_name = frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "name")
	if demand_name:
		for row in frappe.get_all(
			"Procurement Package Line",
			filters={"demand_id": demand_name, "is_active": 1},
			fields=["name"],
		):
			frappe.db.set_value(
				"Procurement Package Line",
				row.name,
				"is_active",
				0,
				update_modified=False,
			)
	frappe.db.commit()


def _bootstrap_upstream_only() -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
	from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
	from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey

	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")


def _restore_works_journey_handoffs() -> None:
	from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey

	assert upsert_works_master_journey().get("ok")


def _ensure_works_active_plan() -> None:
	entity = frappe.db.get_value("Procuring Entity", {"entity_code": _PE_CODE}, "name") or _PE_CODE
	if frappe.db.exists("Procurement Plan", PLAN_CODE):
		frappe.db.set_value(
			"Procurement Plan",
			PLAN_CODE,
			{"status": PLAN_ACTIVE, "is_active": 1, "procuring_entity": entity},
			update_modified=False,
		)
		frappe.db.commit()
		return
	plan = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"name": PLAN_CODE,
			"plan_code": PLAN_CODE,
			"plan_name": PLAN_NAME,
			"fiscal_year": FISCAL_YEAR,
			"procuring_entity": entity,
			"currency": "KES",
			"status": PLAN_ACTIVE,
			"is_active": 1,
		}
	)
	plan.flags.ignore_mandatory = True
	plan.insert(ignore_permissions=True)
	frappe.db.commit()


def _check_map(payload: dict) -> dict[str, dict]:
	eligibility = payload.get("eligibility") or {}
	return {c.get("id"): c for c in (eligibility.get("checks") or []) if c.get("id")}


class TestPP2ApprovedDemandDrawerP4002(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not _pp_ok() or not frappe.db.exists("DocType", "Demand"):
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream_only()

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		self._cleanup = []
		_ensure_works_demand_queue_ready()
		_ensure_works_active_plan()
		_restore_works_journey_handoffs()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		_ensure_works_demand_queue_ready()
		for doctype, name in reversed(getattr(self, "_cleanup", [])):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_001_works_drawer_shows_summary_and_eligibility(self):
		"""SEED-TEST-P4-002-001: WORKS drawer returns summary, budget/strategy, and passing checks."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_approved_demand_planning_drawer(
			DEMAND_CODE,
			plan_code=PLAN_CODE,
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"), out)

		demand = out.get("demand") or {}
		self.assertEqual(demand.get("code"), DEMAND_CODE)
		self.assertEqual(demand.get("name"), DEMAND_TITLE)
		self.assertEqual(demand.get("category"), "Works")
		self.assertEqual(flt(demand.get("estimated_value")), flt(ESTIMATED_VALUE))

		budget_context = out.get("budget_context") or {}
		self.assertEqual((budget_context.get("budget_line") or {}).get("code"), BUDGET_LINE_CODE)
		# XMOD-STR-004 — drawer surfaces Demand primary Performance Target (Name/code), not outcome.
		self.assertEqual(
			(budget_context.get("strategy_objective") or {}).get("code"),
			TARGET_CODE,
		)

		item_codes = {it.get("code") for it in (out.get("demand_items") or [])}
		self.assertIn(DEMITEM := DEMAND_ITEM_CODE, item_codes)
		item = next(it for it in out.get("demand_items") or [] if it.get("code") == DEMITEM)
		self.assertEqual(item.get("category"), "Works")
		self.assertEqual(item.get("uom"), "Lot")
		self.assertEqual(flt(item.get("quantity")), 1.0)

		checks = _check_map(out)
		for check_id, label in (
			("demand_approved", "Demand approved"),
			("budget_linked", "Budget line linked"),
			("not_already_packaged", "Demand item not already packaged"),
			("category_supported", "Category supported: Works"),
		):
			self.assertIn(check_id, checks, msg=f"missing {check_id}")
			self.assertTrue(checks[check_id].get("ok"), msg=checks.get(check_id))
			self.assertEqual(checks[check_id].get("label"), label)

		self.assertTrue((out.get("eligibility") or {}).get("allowed"))
		self.assertTrue((out.get("actions") or {}).get("include_in_plan"))

	def test_002_unknown_demand_returns_not_found(self):
		"""SEED-TEST-P4-002-002: Unknown demand code returns NOT_FOUND."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_approved_demand_planning_drawer(
			"DEM-DOES-NOT-EXIST-002",
			actor="Administrator",
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_003_packaged_demand_shows_packaging_blocker(self):
		"""SEED-TEST-P4-002-003: Packaged WORKS demand fails not_already_packaged check."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(seed.get("ok"), seed)

		out = get_approved_demand_planning_drawer(
			DEMAND_CODE,
			plan_code=PLAN_CODE,
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"), out)
		checks = _check_map(out)
		self.assertFalse(checks["not_already_packaged"].get("ok"))
		self.assertFalse((out.get("eligibility") or {}).get("allowed"))
		self.assertFalse((out.get("actions") or {}).get("include_in_plan"))

	def test_004_whitelisted_api_delegates_for_administrator(self):
		"""SEED-TEST-P4-002-004: Whitelisted drawer API returns ok for Administrator."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Administrator")
		out = get_pp_approved_demand_planning_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual((out.get("demand") or {}).get("code"), DEMAND_CODE)

	def test_005_guest_denied(self):
		"""SEED-TEST-P4-002-005: Guest receives PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		out = get_pp_approved_demand_planning_drawer(demand_code=DEMAND_CODE)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_006_approval_certificate_route_when_journey_seeded(self):
		"""SEED-TEST-P4-002-006: WORKS journey exposes approval certificate route in drawer."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_approved_demand_planning_drawer(
			DEMAND_CODE,
			plan_code=PLAN_CODE,
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"), out)
		actions = out.get("actions") or {}
		evidence = out.get("evidence") or {}
		if evidence.get("demand_approval_certificate"):
			self.assertTrue(actions.get("view_demand_approval_certificate"))
			self.assertTrue((actions.get("approval_certificate_route") or "").strip())
