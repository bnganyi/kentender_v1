# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-015 — Planning Audit Events strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	JOURNEY_CODE,
	MASTER_PLANNING_AUDIT_EVENT_CODES,
	PKGCONSUME_AUDIT_EVENT_REF,
	PKGCONSUME_CODE,
	master_planning_audit_event_specs,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.audit_events import (
	ensure_planning_audit_events,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.consumption import (
	ensure_release_consumed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.inclusion import (
	ensure_planning_inclusion,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.method_decision import (
	ensure_method_decision,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
	ensure_master_package,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	ensure_procurement_plan,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.readiness_review import (
	_ensure_schedule,
	_ensure_upstream_handoffs,
	ensure_review_readiness_and_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.release import (
	ensure_planning_release,
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


def _nullable_state(value) -> str:
	return str(value or "").strip()


def _assert_strict_audit_timeline(test_case, *, expected_count: int = 12) -> None:
	spec_rows = master_planning_audit_event_specs()[:expected_count]
	rows = frappe.get_all(
		"Planning Audit Event",
		filters={"journey_code": JOURNEY_CODE, "is_master_seed": 1},
		fields=[
			"name",
			"event_code",
			"event_type",
			"object_type",
			"object_code",
			"actor",
			"occurred_at",
			"from_state",
			"to_state",
			"evidence_ref",
			"journey_code",
			"is_master_seed",
		],
		order_by="occurred_at asc, event_code asc",
	)
	allowed_codes = {row["event_code"] for row in spec_rows}
	master_rows = [row for row in rows if (row.get("event_code") or "").strip() in allowed_codes]
	test_case.assertEqual(len(master_rows), expected_count)
	test_case.assertEqual(len(rows), expected_count)

	times = [str(row.get("occurred_at") or "").split(".")[0] for row in master_rows]
	test_case.assertEqual(times, sorted(times))

	for actual, expected in zip(master_rows, spec_rows, strict=True):
		test_case.assertEqual((actual.get("event_code") or "").strip(), expected["event_code"])
		test_case.assertEqual((actual.get("event_type") or "").strip(), expected["event_type"])
		test_case.assertEqual((actual.get("object_type") or "").strip(), expected["object_type"])
		test_case.assertEqual((actual.get("object_code") or "").strip(), expected["object_code"])
		test_case.assertEqual(_user_code(actual.get("actor")), expected["actor_user_code"])
		test_case.assertEqual(
			str(actual.get("occurred_at") or "").split(".")[0],
			expected["occurred_at"],
		)
		test_case.assertEqual(_nullable_state(actual.get("from_state")), _nullable_state(expected.get("from_state")))
		test_case.assertEqual(_nullable_state(actual.get("to_state")), _nullable_state(expected.get("to_state")))
		test_case.assertEqual((actual.get("evidence_ref") or "").strip(), expected["evidence_ref"])
		test_case.assertEqual((actual.get("journey_code") or "").strip(), JOURNEY_CODE)
		test_case.assertTrue(cint(actual.get("is_master_seed")))

	if expected_count == 12:
		test_case.assertTrue(frappe.db.exists("Planning Audit Event", PKGCONSUME_AUDIT_EVENT_REF))
		consumption_ref = frappe.db.get_value(
			"Planning Release Consumption Record",
			PKGCONSUME_CODE,
			"audit_event_ref",
		)
		test_case.assertEqual((consumption_ref or "").strip(), PKGCONSUME_AUDIT_EVENT_REF)


def _prepare_consumed_checkpoint() -> None:
	ensure_procurement_plan()
	ensure_planning_inclusion()
	ensure_master_package()
	ensure_method_decision()
	_ensure_upstream_handoffs()
	_ensure_schedule()
	ensure_review_readiness_and_ready()
	ensure_planning_release()
	ensure_release_consumed()
	frappe.db.commit()


class TestPP2PlanningWorksMasterSeedP3015(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Planning Audit Event"):
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

	def test_001_consumed_by_tender_checkpoint_sets_strict_audit_timeline(self):
		"""SEED-TEST-P3-015-001: CONSUMED_BY_TENDER seeds strict PPAUD-MOH-2026-* timeline."""
		if self._skip:
			self.skipTest("Planning Audit Event DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("records", {}).get("audit_events"), 12)
		_assert_strict_audit_timeline(self, expected_count=12)
		for code in MASTER_PLANNING_AUDIT_EVENT_CODES:
			self.assertTrue(frappe.db.exists("Planning Audit Event", code))

	def test_002_existing_audit_event_is_repaired_to_spec(self):
		"""SEED-TEST-P3-015-002: Drifted PPAUD row is repaired by ensure_planning_audit_events."""
		if self._skip:
			self.skipTest("Planning Audit Event DocType not installed")

		_prepare_consumed_checkpoint()

		if frappe.db.exists("Planning Audit Event", "PPAUD-MOH-2026-007"):
			doc = frappe.get_doc("Planning Audit Event", "PPAUD-MOH-2026-007")
			doc.flags.ignore_pp_aud_append_only_override = True
			doc.event_type = "Drifted Event"
			doc.object_code = "DRIFT"
			doc.is_master_seed = 0
			doc.save(ignore_permissions=True)
			frappe.db.commit()

		ensure_planning_audit_events(checkpoint="CONSUMED_BY_TENDER")
		_assert_strict_audit_timeline(self, expected_count=12)

	def test_003_validator_val_019_fails_on_audit_drift(self):
		"""SEED-TEST-P3-015-003: PP2-SEED-VAL-019 fails when audit fields drift from strict spec."""
		if self._skip:
			self.skipTest("Planning Audit Event DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)

		if frappe.db.exists("Planning Audit Event", "PPAUD-MOH-2026-010"):
			doc = frappe.get_doc("Planning Audit Event", "PPAUD-MOH-2026-010")
			doc.flags.ignore_pp_aud_append_only_override = True
			doc.event_type = "Drifted Release"
			doc.object_code = "DRIFT"
			doc.is_master_seed = 0
			doc.save(ignore_permissions=True)
			frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_019 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-019"), {})
		self.assertEqual(val_019.get("result"), "FAIL")

	def test_004_consumed_by_tender_validation_passes_val_014_and_val_019(self):
		"""SEED-TEST-P3-015-004: CONSUMED_BY_TENDER validation passes VAL-014 and VAL-019 after seed."""
		if self._skip:
			self.skipTest("Planning Audit Event DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_014 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-014"), {})
		val_019 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-019"), {})
		self.assertEqual(val_014.get("result"), "PASS")
		self.assertEqual(val_019.get("result"), "PASS")
