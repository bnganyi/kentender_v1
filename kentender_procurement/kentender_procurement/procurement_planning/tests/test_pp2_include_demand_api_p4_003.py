# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-003 — Include in Plan whitelisted API (PP2-SMOKE-BE-003)."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	FISCAL_YEAR,
	INCLUSION_CODE,
	PLAN_CODE,
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import DemandInclusion
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_REVIEWER_USER = "planning.reviewer@moh.test"


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


def _ensure_works_active_plan(*, status: str = PLAN_ACTIVE) -> None:
	entity = frappe.db.get_value("Procuring Entity", {"entity_code": _PE_CODE}, "name") or _PE_CODE
	if frappe.db.exists("Procurement Plan", PLAN_CODE):
		frappe.db.set_value(
			"Procurement Plan",
			PLAN_CODE,
			{"status": status, "is_active": 1, "procuring_entity": entity},
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
			"status": status,
			"is_active": 1,
		}
	)
	plan.flags.ignore_mandatory = True
	plan.insert(ignore_permissions=True)
	frappe.db.commit()


def _include_via_api(
	*,
	demand_code: str = DEMAND_CODE,
	procurement_plan_code: str = PLAN_CODE,
	demand_item_codes: list[str] | None = None,
) -> dict:
	item_codes = demand_item_codes if demand_item_codes is not None else [DEMAND_ITEM_CODE]
	return include_pp_demand_in_procurement_plan(
		demand_code=demand_code,
		procurement_plan_code=procurement_plan_code,
		demand_item_codes=json.dumps(item_codes),
	)


class TestPP2IncludeDemandApiP4003(IntegrationTestCase):
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
		self._cleanup: list[tuple[str, str]] = []
		_ensure_works_demand_queue_ready()
		_ensure_works_active_plan()
		_restore_works_journey_handoffs()
		if frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE):
			frappe.delete_doc(
				"Procurement Handoff Card",
				INCLUSION_CODE,
				force=True,
				ignore_permissions=True,
			)
			frappe.db.commit()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		_ensure_works_demand_queue_ready()
		for doctype, name in reversed(getattr(self, "_cleanup", [])):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _track_inclusion(self, inclusion_code: str | None) -> None:
		if inclusion_code and frappe.db.exists("Procurement Handoff Card", inclusion_code):
			self._cleanup.append(("Procurement Handoff Card", inclusion_code))

	def test_001_works_include_creates_planning_inclusion(self):
		"""SEED-TEST-P4-003-001: API include creates PLANINCL-MOH-2026-001 (PP2-SMOKE-BE-003)."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = _include_via_api()
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("inclusion_code"), INCLUSION_CODE)
		self.assertEqual(out.get("demand_code"), DEMAND_CODE)
		self.assertEqual(out.get("procurement_plan_code"), PLAN_CODE)
		self.assertEqual(out.get("budget_line_code"), BUDGET_LINE_CODE)
		self.assertEqual(out.get("demand_item_codes"), [DEMAND_ITEM_CODE])
		self.assertEqual(out.get("status"), "Included")
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE))
		self._track_inclusion(INCLUSION_CODE)

	def test_002_second_call_is_idempotent(self):
		"""SEED-TEST-P4-003-002: Second identical API call returns existing inclusion."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		first = _include_via_api()
		self.assertTrue(first.get("ok"), first)
		inclusion_code = first.get("inclusion_code")
		self.assertTrue(inclusion_code)
		self._track_inclusion(inclusion_code)

		count_after_first = frappe.db.count(
			"Procurement Handoff Card",
			{
				"handoff_title": "Planning Inclusion Record",
				"source_object_code": DEMAND_CODE,
				"target_object_code": PLAN_CODE,
			},
		)

		second = _include_via_api()
		self.assertTrue(second.get("ok"), second)
		self.assertEqual(second.get("action"), "existing")
		self.assertEqual(second.get("inclusion_code"), inclusion_code)

		count_after_second = frappe.db.count(
			"Procurement Handoff Card",
			{
				"handoff_title": "Planning Inclusion Record",
				"source_object_code": DEMAND_CODE,
				"target_object_code": PLAN_CODE,
			},
		)
		self.assertEqual(count_after_first, count_after_second)

	def test_003_inactive_plan_returns_guard_error(self):
		"""SEED-TEST-P4-003-003: Inactive plan returns structured guard error."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		_ensure_works_active_plan(status=PLAN_DRAFT)
		out = _include_via_api()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), DemandInclusion.PLAN_INACTIVE)
		self.assertTrue((out.get("message") or "").strip())

	def test_004_whitelisted_api_delegates_for_administrator(self):
		"""SEED-TEST-P4-003-004: Administrator succeeds via whitelisted API."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Administrator")
		out = _include_via_api()
		self.assertTrue(out.get("ok"), out)
		self.assertIn(out.get("action"), ("created", "existing"))
		self.assertEqual(out.get("inclusion_code"), INCLUSION_CODE)
		self._track_inclusion(out.get("inclusion_code"))

	def test_005_guest_denied(self):
		"""SEED-TEST-P4-003-005: Guest receives PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		out = _include_via_api()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_006_planning_reviewer_denied(self):
		"""SEED-TEST-P4-003-006: Planning Reviewer cannot include demand in plan."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		if not frappe.db.exists("User", _REVIEWER_USER):
			self.skipTest(f"User {_REVIEWER_USER} not present on site")

		frappe.set_user(_REVIEWER_USER)
		out = _include_via_api()
		self.assertFalse(out.get("ok"))
		self.assertIn(out.get("error_code"), ("PP_ACCESS_DENIED", "PP2-BLOCK-NOT-PERMITTED"))
