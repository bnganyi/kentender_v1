# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-004 — PP2 WORKS master planning seed checkpoint matrix tests."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CHECKPOINT_ORDER,
	INCLUSION_CODE,
	PKGREL_CODE,
	PKG_CODE,
	PLAN_CODE,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
	run_load,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"

_ALL_VAL_IDS = tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(1, 20))

_VALIDATE_GATING: dict[str, dict[str, tuple[str, ...]]] = {
	"APPROVED_DEMAND_READY": {
		"included": ("PP2-SEED-VAL-015",),
		"excluded": tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(1, 15))
		+ tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(16, 20)),
	},
	"INCLUDED_IN_PLAN": {
		"included": (
			"PP2-SEED-VAL-001",
			"PP2-SEED-VAL-002",
			"PP2-SEED-VAL-003",
			"PP2-SEED-VAL-015",
		),
		"excluded": tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(4, 15))
		+ tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(16, 20)),
	},
	"PACKAGE_DRAFT": {
		"included": tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(1, 9)) + ("PP2-SEED-VAL-015",),
		"excluded": tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(9, 15))
		+ tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(16, 20)),
	},
	"READY_FOR_RELEASE": {
		"included": tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(1, 10))
		+ ("PP2-SEED-VAL-014", "PP2-SEED-VAL-016", "PP2-SEED-VAL-015"),
		"excluded": (
			"PP2-SEED-VAL-010",
			"PP2-SEED-VAL-011",
			"PP2-SEED-VAL-012",
			"PP2-SEED-VAL-013",
			"PP2-SEED-VAL-017",
			"PP2-SEED-VAL-018",
			"PP2-SEED-VAL-019",
		),
	},
	"RELEASED_TO_TENDER": {
		"included": tuple(f"PP2-SEED-VAL-{i:03d}" for i in range(1, 12))
		+ ("PP2-SEED-VAL-013", "PP2-SEED-VAL-014", "PP2-SEED-VAL-016", "PP2-SEED-VAL-017", "PP2-SEED-VAL-015"),
		"excluded": ("PP2-SEED-VAL-012", "PP2-SEED-VAL-018", "PP2-SEED-VAL-019"),
	},
	"CONSUMED_BY_TENDER": {
		"included": _ALL_VAL_IDS,
		"excluded": (),
	},
}

CHECKPOINT_EXPECTATIONS: dict[str, dict[str, Any]] = {
	"APPROVED_DEMAND_READY": {
		"steps_run": [],
		"records": {
			"procurement_plans": 0,
			"planning_inclusions": 0,
			"procurement_packages": 0,
			"planning_releases": 0,
			"consumption_records": 0,
		},
		"links": {"package": "", "release": "", "tender": ""},
		"package_status": None,
		"locked_after_release": None,
	},
	"INCLUDED_IN_PLAN": {
		"steps_run": ["plan", "inclusion", "audit_events"],
		"records": {
			"procurement_plans": 1,
			"planning_inclusions": 1,
			"procurement_packages": 0,
			"planning_releases": 0,
			"consumption_records": 0,
		},
		"links": {"package": "", "release": "", "tender": ""},
		"package_status": None,
		"locked_after_release": None,
	},
	"PACKAGE_DRAFT": {
		"steps_run": ["plan", "inclusion", "package", "method_decision", "audit_events"],
		"records": {
			"procurement_plans": 1,
			"planning_inclusions": 1,
			"procurement_packages": 1,
			"package_lines": 1,
			"method_decisions": 1,
			"readiness_results": 0,
			"review_decisions": 0,
			"planning_releases": 0,
			"consumption_records": 0,
		},
		"links": {"package": PKG_CODE, "release": "", "tender": ""},
		"package_status": PKG_DRAFT,
		"locked_after_release": 0,
	},
	"READY_FOR_RELEASE": {
		"steps_run": ["plan", "inclusion", "package", "method_decision", "readiness_review", "audit_events"],
		"records": {
			"procurement_plans": 1,
			"planning_inclusions": 1,
			"procurement_packages": 1,
			"package_lines": 1,
			"method_decisions": 1,
			"readiness_results": 1,
			"review_decisions": 1,
			"planning_releases": 0,
			"consumption_records": 0,
		},
		"links": {"package": PKG_CODE, "release": "", "tender": ""},
		"package_status": PKG_READY_FOR_RELEASE,
		"locked_after_release": 0,
	},
	"RELEASED_TO_TENDER": {
		"steps_run": [
			"plan",
			"inclusion",
			"package",
			"method_decision",
			"readiness_review",
			"release",
			"audit_events",
		],
		"records": {
			"procurement_plans": 1,
			"planning_inclusions": 1,
			"procurement_packages": 1,
			"package_lines": 1,
			"method_decisions": 1,
			"readiness_results": 1,
			"review_decisions": 1,
			"planning_releases": 1,
			"consumption_records": 0,
		},
		"links": {"package": PKG_CODE, "release": PKGREL_CODE, "tender": ""},
		"package_status": PKG_RELEASED,
		"locked_after_release": 1,
	},
	"CONSUMED_BY_TENDER": {
		"steps_run": [
			"plan",
			"inclusion",
			"package",
			"method_decision",
			"readiness_review",
			"release",
			"consumption",
			"audit_events",
		],
		"records": {
			"procurement_plans": 1,
			"planning_inclusions": 1,
			"procurement_packages": 1,
			"package_lines": 1,
			"method_decisions": 1,
			"readiness_results": 1,
			"review_decisions": 1,
			"planning_releases": 1,
			"consumption_records": 1,
		},
		"links": {"package": PKG_CODE, "release": PKGREL_CODE, "tender": TENDER_CODE},
		"package_status": PKG_CONSUMED,
		"locked_after_release": 1,
	},
}


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


def _assert_checkpoint_load(test_case, out: dict[str, Any], checkpoint: str) -> None:
	expect = CHECKPOINT_EXPECTATIONS[checkpoint]
	self_msg = f"checkpoint={checkpoint}"
	test_case.assertTrue(out.get("ok"), f"{self_msg}: {out}")
	test_case.assertEqual(out.get("checkpoint"), checkpoint, self_msg)
	test_case.assertEqual(out.get("steps_run"), expect["steps_run"], self_msg)

	for key, value in expect["records"].items():
		actual = out.get("records", {}).get(key)
		if isinstance(value, int) and value >= 1:
			test_case.assertGreaterEqual(actual, value, f"{self_msg} records.{key}")
		else:
			test_case.assertEqual(actual, value, f"{self_msg} records.{key}")

	for link_key, link_value in expect["links"].items():
		if link_key == "tender" and checkpoint != "CONSUMED_BY_TENDER":
			continue
		test_case.assertEqual(
			out.get("links", {}).get(link_key), link_value, f"{self_msg} links.{link_key}"
		)

	if expect["package_status"] is not None:
		test_case.assertTrue(frappe.db.exists("Procurement Package", PKG_CODE), self_msg)
		status = frappe.db.get_value("Procurement Package", PKG_CODE, "status")
		test_case.assertEqual(status, expect["package_status"], self_msg)
		locked = cint(frappe.db.get_value("Procurement Package", PKG_CODE, "locked_after_release"))
		test_case.assertEqual(locked, expect["locked_after_release"], self_msg)
	else:
		test_case.assertFalse(frappe.db.exists("Procurement Package", PKG_CODE), self_msg)


class TestPP2PlanningWorksMasterSeedP3004(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False
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

	def test_001_all_checkpoints_load_expected_state(self):
		"""SEED-TEST-P3-004-001: Each checkpoint loads correct steps_run, records, links, status."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		for checkpoint in CHECKPOINT_ORDER:
			with self.subTest(checkpoint=checkpoint):
				clear_master_planning_seed()
				out = seed_procurement_planning_works_master(
					checkpoint=checkpoint, force_reset=True
				)
				_assert_checkpoint_load(self, out, checkpoint)

	def test_002_validate_passes_at_each_checkpoint(self):
		"""SEED-TEST-P3-004-002: Validator returns ok=true with zero failures at each checkpoint."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		for checkpoint in CHECKPOINT_ORDER:
			with self.subTest(checkpoint=checkpoint):
				clear_master_planning_seed()
				seed = seed_procurement_planning_works_master(
					checkpoint=checkpoint, force_reset=True
				)
				self.assertTrue(seed.get("ok"), seed)

				out = validate_procurement_planning_works_master_seed(checkpoint=checkpoint)
				self.assertTrue(out.get("ok"), out)
				self.assertEqual(out.get("failed"), 0, out)
				for check in out.get("checks") or []:
					self.assertEqual(
						check.get("result"),
						"PASS",
						msg=f"{checkpoint} {check.get('check_id')}: {check}",
					)

	def test_003_validate_check_id_gating_per_checkpoint(self):
		"""SEED-TEST-P3-004-003: PP2-SEED-VAL checks included/excluded per checkpoint."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		for checkpoint, gating in _VALIDATE_GATING.items():
			with self.subTest(checkpoint=checkpoint):
				clear_master_planning_seed()
				seed = seed_procurement_planning_works_master(
					checkpoint=checkpoint, force_reset=True
				)
				self.assertTrue(seed.get("ok"), seed)

				out = validate_procurement_planning_works_master_seed(checkpoint=checkpoint)
				ids = {c["check_id"] for c in out.get("checks") or []}
				for required in gating["included"]:
					self.assertIn(required, ids, checkpoint)
				for excluded in gating["excluded"]:
					self.assertNotIn(excluded, ids, checkpoint)

	def test_004_loader_rejects_unknown_checkpoint(self):
		"""SEED-TEST-P3-004-004: Unsupported checkpoint raises INVALID_CHECKPOINT on load."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		with self.assertRaises(frappe.ValidationError) as ctx:
			run_load(checkpoint="PHANTOM_CHECKPOINT", force_reset=False)
		self.assertIn("Unsupported checkpoint", str(ctx.exception))

	def test_005_package_draft_no_release_overshoot(self):
		"""SEED-TEST-P3-004-005: PACKAGE_DRAFT must not create release, consumption, or tender link."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		self.assertTrue(out.get("ok"), out)
		self.assertFalse(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))
		self.assertEqual(
			frappe.db.count("Planning Release Consumption Record", {"release_code": PKGREL_CODE}),
			0,
		)
		self.assertEqual(out["links"].get("release"), "")
		self.assertFalse(
			frappe.db.exists(
				"Planning Release Consumption Record",
				{"release_code": PKGREL_CODE, "target_object_code": TENDER_CODE},
			)
		)
		self.assertEqual(frappe.db.get_value("Procurement Package", PKG_CODE, "status"), PKG_DRAFT)

	def test_006_incremental_ascending_checkpoint_progression(self):
		"""SEED-TEST-P3-004-006: Ascending loads without force_reset reach CONSUMED_BY_TENDER."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		clear_master_planning_seed()
		for checkpoint in CHECKPOINT_ORDER:
			with self.subTest(checkpoint=checkpoint):
				out = seed_procurement_planning_works_master(
					checkpoint=checkpoint, force_reset=False
				)
				self.assertTrue(out.get("ok"), out)

		final = CHECKPOINT_EXPECTATIONS["CONSUMED_BY_TENDER"]
		self.assertTrue(frappe.db.exists("Procurement Plan", PLAN_CODE))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE))
		self.assertTrue(frappe.db.exists("Procurement Package", PKG_CODE))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))
		self.assertGreaterEqual(
			frappe.db.count("Planning Release Consumption Record", {"release_code": PKGREL_CODE}),
			final["records"]["consumption_records"],
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", PKG_CODE, "status"),
			final["package_status"],
		)
		self.assertTrue(
			cint(frappe.db.get_value("Procurement Package", PKG_CODE, "locked_after_release"))
		)
		self.assertTrue(frappe.db.exists("TM2 Tender", TENDER_CODE))
