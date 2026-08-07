# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-016 — Negative fixture loader tests (spec §22)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.negative_fixtures.constants import (
	ALL_NEGATIVE_FIXTURE_CODES,
	FIXTURE_METADATA,
	NEG_ENTITY_CODES,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	clear_procurement_planning_negative_fixture,
	load_procurement_planning_negative_fixture,
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	INCLUSION_CODE,
	PKGREL_CODE,
	PKG_CODE,
	PKG_LINE_CODE,
	PLAN_CODE,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"

_MASTER_CODES: tuple[tuple[str, str], ...] = (
	("Procurement Plan", PLAN_CODE),
	("Procurement Handoff Card", INCLUSION_CODE),
	("Procurement Handoff Card", PKGREL_CODE),
	("Procurement Package", PKG_CODE),
	("Procurement Package Line", PKG_LINE_CODE),
)


def _bootstrap_upstream() -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")


def _snapshot_master_rows() -> dict[tuple[str, str], dict | None]:
	out: dict[tuple[str, str], dict | None] = {}
	for doctype, name in _MASTER_CODES:
		if not frappe.db.exists(doctype, name):
			out[(doctype, name)] = None
			continue
		out[(doctype, name)] = frappe.db.get_value(doctype, name, "*", as_dict=True)
	return out


def _assert_master_rows_unchanged(
	test_case: IntegrationTestCase,
	before: dict[tuple[str, str], dict | None],
) -> None:
	for key, row_before in before.items():
		doctype, name = key
		if row_before is None:
			test_case.assertFalse(frappe.db.exists(doctype, name), msg=f"master row created: {doctype}/{name}")
			continue
		test_case.assertTrue(frappe.db.exists(doctype, name), msg=f"master row missing: {doctype}/{name}")
		row_after = frappe.db.get_value(doctype, name, "*", as_dict=True)
		for field in ("status", "estimated_value", "is_master_seed", "plan_id", "package_id"):
			if field in row_before:
				test_case.assertEqual(
					row_after.get(field),
					row_before.get(field),
					msg=f"{doctype}/{name}.{field} changed",
				)


class TestPP2PlanningWorksMasterSeedP3016(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream()
		seed_procurement_planning_works_master(checkpoint="RELEASED_TO_TENDER")
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		for fixture_code in ALL_NEGATIVE_FIXTURE_CODES:
			clear_procurement_planning_negative_fixture(fixture_code)

	def test_001_unknown_fixture_returns_unknown_fixture(self):
		"""SEED-TEST-P3-016-001: Unknown fixture code returns ok=False + UNKNOWN_FIXTURE."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")

		out = load_procurement_planning_negative_fixture("NEG-PP2-DOES-NOT-EXIST")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "UNKNOWN_FIXTURE")
		self.assertEqual(out.get("fixture_code"), "NEG-PP2-DOES-NOT-EXIST")

	def test_002_each_fixture_loads_with_contract_metadata(self):
		"""SEED-TEST-P3-016-002: Each of 12 fixtures loads with metadata + context."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")
		if not frappe.db.exists("DocType", "TM2 Tender"):
			self.skipTest("TM2 Tender DocType not installed")

		for fixture_code in ALL_NEGATIVE_FIXTURE_CODES:
			with self.subTest(fixture_code=fixture_code):
				clear_procurement_planning_negative_fixture(fixture_code)
				out = load_procurement_planning_negative_fixture(fixture_code)
				self.assertTrue(out.get("ok"), out)
				meta = FIXTURE_METADATA[fixture_code]
				self.assertEqual(out.get("fixture_code"), fixture_code)
				self.assertEqual(out.get("setup"), meta["setup"])
				self.assertEqual(out.get("attempted_action"), meta["attempted_action"])
				self.assertEqual(out.get("expected_result"), meta["expected_result"])
				self.assertEqual(out.get("blocker_code"), meta["blocker_code"])
				self.assertEqual(out.get("message"), meta["message"])
				self.assertIsInstance(out.get("records"), dict)
				self.assertTrue(out.get("records"))
				self.assertIsInstance(out.get("context"), dict)
				self.assertTrue(out.get("context"))
				for key, value in NEG_ENTITY_CODES[fixture_code].items():
					if key in out["records"]:
						self.assertEqual(out["records"][key], value)

	def test_003_fixture_load_does_not_mutate_master_codes(self):
		"""SEED-TEST-P3-016-003: Loading fixtures does not create/modify WORKS master codes."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")
		if not frappe.db.exists("DocType", "TM2 Tender"):
			self.skipTest("TM2 Tender DocType not installed")

		before = _snapshot_master_rows()
		for fixture_code in ALL_NEGATIVE_FIXTURE_CODES:
			with self.subTest(fixture_code=fixture_code):
				clear_procurement_planning_negative_fixture(fixture_code)
				out = load_procurement_planning_negative_fixture(fixture_code)
				self.assertTrue(out.get("ok"), out)
				_assert_master_rows_unchanged(self, before)

	def test_004_reload_is_idempotent(self):
		"""SEED-TEST-P3-016-004: Reload same fixture does not duplicate active packages/lines."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")

		fixture_code = "NEG-PP2-PKG-NO-LINE-001"
		clear_procurement_planning_negative_fixture(fixture_code)
		first = load_procurement_planning_negative_fixture(fixture_code)
		self.assertTrue(first.get("ok"), first)
		package_code = first["records"]["package_code"]
		line_count_first = frappe.db.count(
			"Procurement Package Line",
			{"package_id": package_code, "is_active": 1},
		)
		package_count_first = frappe.db.count(
			"Procurement Package",
			{"name": package_code, "is_active": 1},
		)

		second = load_procurement_planning_negative_fixture(fixture_code)
		self.assertTrue(second.get("ok"), second)
		line_count_second = frappe.db.count(
			"Procurement Package Line",
			{"package_id": package_code, "is_active": 1},
		)
		package_count_second = frappe.db.count(
			"Procurement Package",
			{"name": package_code, "is_active": 1},
		)
		self.assertEqual(line_count_first, line_count_second)
		self.assertEqual(package_count_first, package_count_second)
