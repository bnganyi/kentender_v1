# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-018 — PP2 WORKS master planning seed idempotency tests (spec §20)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	INCLUSION_CODE,
	MASTER_PLANNING_AUDIT_EVENT_CODES,
	METHDEC_CODE,
	PKGCONSUME_CODE,
	PKGREL_CODE,
	PKGREV_CODE,
	PKGRDY_CODE,
	PKG_CODE,
	PKG_LINE_CODE,
	PLAN_CODE,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
	run_load,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
	_ensure_procurement_package,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"

_SUMMARY_RECORD_KEYS = (
	"package_lines",
	"method_decisions",
	"readiness_results",
	"review_decisions",
	"consumption_records",
	"audit_events",
)


def _bootstrap_upstream(*, with_tender: bool = True) -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")
	from kentender_procurement.tender_management.seeds.works_master_std_seed import (
		upsert_works_master_std,
	)

	assert upsert_works_master_std().get("ok")
	if with_tender:
		from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
			upsert_works_master_tender,
		)

		if not frappe.db.exists("TM2 Tender", TENDER_CODE):
			if not frappe.db.exists("Procurement Package", PKG_CODE):
				run_load(checkpoint="RELEASED_TO_TENDER", force_reset=False)
			upsert_works_master_tender()


def _sql_count(table: str, *, where: str, params: tuple) -> int:
	return int(frappe.db.sql(f"SELECT COUNT(*) FROM `{table}` WHERE {where}", params)[0][0])


def _handoff_count(handoff_code: str) -> int:
	return _sql_count(
		"tabProcurement Handoff Card",
		where="handoff_code = %s",
		params=(handoff_code,),
	)


def _tender_snapshot() -> dict[str, object]:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return {"available": False}
	count = _sql_count(
		"tabTM2 Tender",
		where="tender_code = %s",
		params=(TENDER_CODE,),
	)
	name = frappe.db.get_value("TM2 Tender", {"tender_code": TENDER_CODE}, "name")
	return {"available": True, "count": count, "name": name}


def _master_entity_counts() -> dict[str, int]:
	counts = {
		"procurement_plan": _sql_count(
			"tabProcurement Plan",
			where="name = %s",
			params=(PLAN_CODE,),
		),
		"planning_inclusion": _handoff_count(INCLUSION_CODE),
		"procurement_package": _sql_count(
			"tabProcurement Package",
			where="name = %s",
			params=(PKG_CODE,),
		),
		"active_package_lines": frappe.db.count(
			"Procurement Package Line",
			{"package_id": PKG_CODE, "is_active": 1},
		),
		"package_line_by_code": _sql_count(
			"tabProcurement Package Line",
			where="package_line_code = %s",
			params=(PKG_LINE_CODE,),
		),
		"method_decision": _sql_count(
			"tabPackage Method Decision",
			where="method_decision_code = %s",
			params=(METHDEC_CODE,),
		),
		"readiness_result": _sql_count(
			"tabPackage Readiness Result",
			where="readiness_code = %s",
			params=(PKGRDY_CODE,),
		),
		"review_decision": _sql_count(
			"tabPackage Review Decision",
			where="review_decision_code = %s",
			params=(PKGREV_CODE,),
		),
		"planning_release": _handoff_count(PKGREL_CODE),
		"consumption_record": _sql_count(
			"tabPlanning Release Consumption Record",
			where="consumption_code = %s",
			params=(PKGCONSUME_CODE,),
		),
	}
	for event_code in MASTER_PLANNING_AUDIT_EVENT_CODES:
		counts[f"audit_event:{event_code}"] = _sql_count(
			"tabPlanning Audit Event",
			where="name = %s",
			params=(event_code,),
		)
	tender = _tender_snapshot()
	if tender.get("available"):
		counts["tm2_tender"] = int(tender["count"])
	return counts


def _assert_exactly_one_master_entities(test_case: IntegrationTestCase, counts: dict[str, int]) -> None:
	single_value_keys = (
		"procurement_plan",
		"planning_inclusion",
		"procurement_package",
		"package_line_by_code",
		"method_decision",
		"readiness_result",
		"review_decision",
		"planning_release",
		"consumption_record",
	)
	for key in single_value_keys:
		test_case.assertEqual(counts.get(key), 1, msg=f"expected exactly one {key}, got {counts.get(key)}")
	test_case.assertGreaterEqual(counts.get("active_package_lines", 0), 1)
	for event_code in MASTER_PLANNING_AUDIT_EVENT_CODES:
		key = f"audit_event:{event_code}"
		test_case.assertEqual(
			counts.get(key),
			1,
			msg=f"expected exactly one audit event {event_code}, got {counts.get(key)}",
		)
	if "tm2_tender" in counts:
		test_case.assertEqual(counts["tm2_tender"], 1)


def _release_consumption_audit_counts() -> dict[str, int]:
	return {
		"planning_releases": _handoff_count(PKGREL_CODE),
		"consumption_records": _sql_count(
			"tabPlanning Release Consumption Record",
			where="release_code = %s",
			params=(PKGREL_CODE,),
		),
		"audit_events": frappe.db.count(
			"Planning Audit Event",
			{"journey_code": "JRN-MOH-2026-001", "is_master_seed": 1},
		),
	}


class TestPP2PlanningWorksMasterSeedP3018(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False
		cls._tm2_available = frappe.db.exists("DocType", "TM2 Tender")
		_bootstrap_upstream(with_tender=True)

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

	def test_001_consumed_double_run_no_duplicate_master_entities(self):
		"""SEED-TEST-P3-018-001: CONSUMED_BY_TENDER twice leaves stable master entity counts."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		first = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(first.get("ok"), first)
		counts_first = _master_entity_counts()

		second = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(second.get("ok"), second)
		counts_second = _master_entity_counts()

		self.assertEqual(counts_first, counts_second)
		_assert_exactly_one_master_entities(self, counts_second)

	def test_002_second_run_summary_records_stable(self):
		"""SEED-TEST-P3-018-002: Second run summary records block matches first run."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		first = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(first.get("ok"), first)
		second = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(second.get("ok"), second)

		first_records = first.get("records") or {}
		second_records = second.get("records") or {}
		for key in _SUMMARY_RECORD_KEYS:
			self.assertEqual(
				second_records.get(key),
				first_records.get(key),
				msg=f"records.{key} drifted on second seed run",
			)

	def test_003_validate_passes_after_second_seed_run(self):
		"""SEED-TEST-P3-018-003: Validator passes after idempotent second CONSUMED run."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self.assertTrue(
			seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER").get("ok")
		)
		self.assertTrue(
			seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER").get("ok")
		)

		out = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)
		self.assertGreater(out.get("passed", 0), 0)
		self.assertEqual(out.get("failed"), 0)

	def test_004_incremental_checkpoint_reentry_no_duplicate_growth(self):
		"""SEED-TEST-P3-018-004: READY_FOR_RELEASE x2 then CONSUMED x2 does not grow release/consumption/audit rows."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		ready_first = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(ready_first.get("ok"), ready_first)
		ready_counts_first = _release_consumption_audit_counts()

		ready_second = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(ready_second.get("ok"), ready_second)
		ready_counts_second = _release_consumption_audit_counts()
		self.assertEqual(ready_counts_first, ready_counts_second)

		consumed_first = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(consumed_first.get("ok"), consumed_first)
		consumed_counts_first = _release_consumption_audit_counts()

		consumed_second = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(consumed_second.get("ok"), consumed_second)
		consumed_counts_second = _release_consumption_audit_counts()
		self.assertEqual(consumed_counts_first, consumed_counts_second)

	def test_005_inconsistent_inclusion_link_fails_without_force_reset(self):
		"""SEED-TEST-P3-018-005: Material inclusion/package drift fails unless force_reset=True."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self.assertTrue(
			seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER").get("ok")
		)

		stray_code = "PKG-STRAY-IDEMP-018"
		if not frappe.db.exists("Procurement Package", stray_code):
			frappe.db.sql(
				"""
				INSERT INTO `tabProcurement Package`
				(name, package_code, package_name, plan_id, status, is_master_seed,
				 procurement_method, procurement_category, currency, owner, docstatus)
				VALUES (%s, %s, %s, %s, 'Draft', 0, 'Open Tender', 'Works', 'KES', 'Administrator', 0)
				""",
				(stray_code, stray_code, "Stray idempotency probe package", PLAN_CODE),
			)

		inclusion = frappe.get_doc("Procurement Handoff Card", INCLUSION_CODE)
		locked = frappe.parse_json(inclusion.locked_summary or "{}")
		if not isinstance(locked, dict):
			locked = {}
		locked["created_package_code"] = stray_code
		frappe.db.set_value(
			"Procurement Handoff Card",
			INCLUSION_CODE,
			"locked_summary",
			frappe.as_json(locked),
			update_modified=False,
		)
		frappe.db.commit()

		with self.assertRaises(frappe.ValidationError) as ctx:
			_ensure_procurement_package()
		exc_text = str(ctx.exception)
		self.assertIn("Inconsistent master seed", exc_text)
		self.assertIn("force_reset", exc_text.lower())

		with self.assertRaises(frappe.ValidationError) as ctx:
			seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		exc_text = str(ctx.exception)
		self.assertIn("Inconsistent master seed", exc_text)
		self.assertIn("force_reset", exc_text.lower())

		out = seed_procurement_planning_works_master(
			checkpoint="CONSUMED_BY_TENDER",
			force_reset=True,
		)
		self.assertTrue(out.get("ok"), out)
		inclusion_after = frappe.get_doc("Procurement Handoff Card", INCLUSION_CODE)
		locked_after = frappe.parse_json(inclusion_after.locked_summary or "{}")
		self.assertEqual((locked_after or {}).get("created_package_code"), PKG_CODE)

	def test_006_tender_link_not_recreated_on_second_run(self):
		"""SEED-TEST-P3-018-006: Second CONSUMED run does not recreate TND-MOH-2026-001."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		if not self._tm2_available:
			self.skipTest("TM2 Tender DocType not installed")

		self.assertTrue(
			seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER").get("ok")
		)
		before = _tender_snapshot()

		self.assertTrue(
			seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER").get("ok")
		)
		after = _tender_snapshot()

		self.assertEqual(after.get("count"), before.get("count"))
		self.assertEqual(after.get("name"), before.get("name"))
		self.assertEqual(after.get("count"), 1)
