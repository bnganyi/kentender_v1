# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-007 — Planning Inclusion strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	CURRENCY,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	INCLUSION_CODE,
	INCLUSION_FISCAL_YEAR,
	INCLUSION_INCLUDED_AT,
	INCLUSION_NOTE,
	INCLUSION_PROCUREMENT_CATEGORY,
	INCLUSION_STATUS_INCLUDED,
	INCLUSION_STATUS_PACKAGED,
	JOURNEY_CODE,
	PKG_CODE,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_CREATOR_USER_CODE,
	PE_CODE,
	SOURCE_BUDGET_STATUS_AT_INCLUSION,
	SOURCE_DEMAND_STATUS_AT_INCLUSION,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.inclusion import (
	ensure_planning_inclusion,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	ensure_procurement_plan,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"


def _bootstrap_upstream() -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")


def _user_code(user_name: str | None) -> str:
	if not user_name or not frappe.db.exists("User", user_name):
		return ""
	return str(frappe.db.get_value("User", user_name, "username") or "").strip()


def _assert_strict_inclusion_included_state(self) -> None:
	handoff = frappe.get_doc("Procurement Handoff Card", INCLUSION_CODE)
	self.assertTrue(handoff.is_master_seed)
	self.assertEqual(handoff.journey_code, JOURNEY_CODE)
	self.assertEqual(handoff.source_object_code, DEMAND_CODE)
	self.assertEqual(handoff.target_object_code, PLAN_CODE)
	self.assertEqual(_user_code(handoff.generated_by), PLAN_CREATOR_USER_CODE)
	self.assertEqual(str(handoff.generated_at).split(".")[0], INCLUSION_INCLUDED_AT)

	locked = frappe.parse_json(handoff.locked_summary or "{}")
	self.assertEqual(locked.get("procurement_plan"), PLAN_CODE)
	self.assertEqual(locked.get("included_demand"), DEMAND_CODE)
	self.assertEqual(locked.get("budget_line"), BUDGET_LINE_CODE)
	self.assertEqual(sorted(locked.get("demand_item_codes") or []), [DEMAND_ITEM_CODE])
	self.assertEqual(locked.get("inclusion_note"), INCLUSION_NOTE)
	self.assertEqual(locked.get("inclusion_status"), INCLUSION_STATUS_INCLUDED)
	self.assertEqual(locked.get("procuring_entity_code"), PE_CODE)
	self.assertEqual(locked.get("fiscal_year"), INCLUSION_FISCAL_YEAR)
	self.assertEqual(locked.get("procurement_category"), INCLUSION_PROCUREMENT_CATEGORY)
	self.assertEqual(locked.get("source_demand_status_at_inclusion"), SOURCE_DEMAND_STATUS_AT_INCLUSION)
	self.assertEqual(locked.get("source_budget_status_at_inclusion"), SOURCE_BUDGET_STATUS_AT_INCLUSION)
	self.assertFalse((locked.get("created_package_code") or "").strip())

	passed = frappe.parse_json(handoff.passed_forward_summary or "{}")
	self.assertEqual(passed.get("package_candidate"), PKG_TITLE)
	self.assertEqual(passed.get("category"), INCLUSION_PROCUREMENT_CATEGORY)
	self.assertEqual(flt(passed.get("estimated_value")), ESTIMATED_VALUE)
	self.assertEqual(passed.get("currency"), CURRENCY)

	technical = frappe.parse_json(handoff.technical_refs_json or "{}")
	self.assertEqual(technical.get("inclusion_code"), INCLUSION_CODE)
	self.assertEqual(sorted(technical.get("demand_item_codes") or []), [DEMAND_ITEM_CODE])
	self.assertEqual(technical.get("budget_line_code"), BUDGET_LINE_CODE)

	inclusion = get_planning_inclusion(INCLUSION_CODE) or {}
	self.assertEqual(inclusion.get("status"), INCLUSION_STATUS_INCLUDED)
	self.assertFalse((inclusion.get("created_package_code") or "").strip())


class TestPP2PlanningWorksMasterSeedP3007(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream()

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()

	def test_001_included_checkpoint_sets_strict_inclusion_fields(self):
		"""SEED-TEST-P3-007-001: INCLUDED_IN_PLAN seeds strict PLANINCL-MOH-2026-001 values."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE))
		_assert_strict_inclusion_included_state(self)

	def test_002_existing_inclusion_is_repaired_to_spec(self):
		"""SEED-TEST-P3-007-002: Existing drifted inclusion is repaired by ensure_planning_inclusion."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		ensure_procurement_plan()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": INCLUSION_CODE,
				"handoff_title": "Drifted Inclusion",
				"journey_code": JOURNEY_CODE,
				"source_module": "Procurement Planning",
				"target_module": "Procurement Planning",
				"source_object_type": "Demand",
				"source_object_code": "DEM-DRIFT",
				"target_object_type": "Procurement Plan",
				"target_object_code": PLAN_CODE,
				"status": "Handed Off",
				"generated_by": "Administrator",
				"next_action": "Drifted next action",
				"locked_summary": {"included_demand": "DEM-DRIFT"},
				"passed_forward_summary": {},
				"is_master_seed": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_planning_inclusion()
		_assert_strict_inclusion_included_state(self)

	def test_003_validator_val_002_fails_on_inclusion_drift(self):
		"""SEED-TEST-P3-007-003: VAL-002 fails when inclusion fields drift from strict spec."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
		self.assertTrue(out.get("ok"), out)

		handoff = frappe.get_doc("Procurement Handoff Card", INCLUSION_CODE)
		locked = frappe.parse_json(handoff.locked_summary or "{}")
		locked["included_demand"] = "DEM-DRIFT"
		handoff.locked_summary = locked
		handoff.is_master_seed = 0
		handoff.save(ignore_permissions=True)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="INCLUDED_IN_PLAN")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_002 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-002"), {})
		self.assertEqual(val_002.get("result"), "FAIL")

	def test_004_package_draft_checkpoint_marks_inclusion_packaged(self):
		"""SEED-TEST-P3-007-004: PACKAGE_DRAFT marks inclusion Packaged with PKG-MOH-2026-001."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)

		inclusion = get_planning_inclusion(INCLUSION_CODE) or {}
		self.assertEqual(inclusion.get("status"), INCLUSION_STATUS_PACKAGED)
		self.assertEqual(inclusion.get("created_package_code"), PKG_CODE)

		locked = inclusion.get("locked_summary") or {}
		self.assertEqual(locked.get("inclusion_status"), INCLUSION_STATUS_PACKAGED)
		self.assertEqual(locked.get("created_package_code"), PKG_CODE)

		validation = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(validation.get("ok"), validation)
