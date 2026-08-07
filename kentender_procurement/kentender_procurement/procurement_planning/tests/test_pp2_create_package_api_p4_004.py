# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-004 — Create package from planning inclusion whitelisted API (PP2-SMOKE-BE-004)."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	FISCAL_YEAR,
	INCLUSION_CODE,
	PKG_PROCUREMENT_CATEGORY,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import PackageFromInclusion
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_REVIEWER_USER = "planning.reviewer@moh.test"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


def _require_template() -> str | None:
	tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
	if not tpl:
		return None
	row = frappe.db.get_value(
		"Procurement Template",
		tpl[0],
		("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"),
		as_dict=True,
	)
	if not row or not all(row.values()):
		return None
	return tpl[0]


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
	from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
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


def _include_via_api() -> dict:
	return include_pp_demand_in_procurement_plan(
		demand_code=DEMAND_CODE,
		procurement_plan_code=PLAN_CODE,
		demand_item_codes=json.dumps([DEMAND_ITEM_CODE]),
	)


def _create_via_api(inclusion_code: str = INCLUSION_CODE) -> dict:
	return create_pp_package_from_planning_inclusion(inclusion_code=inclusion_code)


class TestPP2CreatePackageApiP4004(IntegrationTestCase):
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
		for row in frappe.get_all(
			"Procurement Package",
			filters={"planning_inclusion_code": INCLUSION_CODE},
			fields=["name"],
		):
			for line_name in frappe.get_all(
				"Procurement Package Line",
				filters={"package_id": row.name},
				pluck="name",
			):
				if frappe.db.exists("Procurement Package Line", line_name):
					frappe.delete_doc(
						"Procurement Package Line",
						line_name,
						force=True,
						ignore_permissions=True,
					)
			if frappe.db.exists("Procurement Package", row.name):
				frappe.delete_doc(
					"Procurement Package",
					row.name,
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

	def _ensure_works_inclusion(self) -> str:
		out = _include_via_api()
		self.assertTrue(out.get("ok"), out)
		inclusion_code = out.get("inclusion_code")
		self.assertTrue(inclusion_code)
		self._track_inclusion(inclusion_code)
		return inclusion_code

	def _track_inclusion(self, inclusion_code: str | None) -> None:
		if inclusion_code and frappe.db.exists("Procurement Handoff Card", inclusion_code):
			self._cleanup.append(("Procurement Handoff Card", inclusion_code))

	def _track_package(self, package_code: str | None, line_codes: list[str] | None = None) -> None:
		if package_code and frappe.db.exists("Procurement Package", package_code):
			self._cleanup.append(("Procurement Package", package_code))
		for line_code in line_codes or []:
			line_name = frappe.db.get_value(
				"Procurement Package Line",
				{"package_line_code": line_code},
				"name",
			)
			if line_name:
				self._cleanup.append(("Procurement Package Line", line_name))

	def test_001_works_create_package_from_inclusion(self):
		"""SEED-TEST-P4-004-001: API create returns package with WORKS traceability (BE-004)."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		if not _require_template():
			self.skipTest("No active Procurement Template with profiles available")

		inclusion_code = self._ensure_works_inclusion()
		out = _create_via_api(inclusion_code)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("inclusion_code"), INCLUSION_CODE)
		self.assertEqual(out.get("demand_code"), DEMAND_CODE)
		self.assertEqual(out.get("budget_line_code"), BUDGET_LINE_CODE)
		self.assertEqual(out.get("status"), PKG_DRAFT)

		package_code = out.get("package_code")
		self.assertTrue(package_code)
		line_codes = out.get("package_line_codes") or []
		self.assertEqual(len(line_codes), 1)
		self._track_package(package_code, line_codes)

		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual((pkg.package_name or "").strip(), PKG_TITLE)
		self.assertEqual((pkg.procurement_category or "").strip(), PKG_PROCUREMENT_CATEGORY)
		self.assertEqual(flt(pkg.estimated_value), flt(ESTIMATED_VALUE))
		self.assertEqual(pkg.planning_inclusion_code, inclusion_code)

		line = frappe.get_doc("Procurement Package Line", {"package_line_code": line_codes[0]})
		self.assertEqual((line.demand_item_code or "").strip(), DEMAND_ITEM_CODE)
		budget_line_name = frappe.db.get_value(
			"Budget Line",
			{"budget_line_code": BUDGET_LINE_CODE},
			"name",
		)
		self.assertEqual(line.budget_line_id, budget_line_name or BUDGET_LINE_CODE)
		self.assertEqual(flt(line.amount), flt(ESTIMATED_VALUE))

		inclusion = out.get("inclusion") or {}
		self.assertEqual(inclusion.get("status"), "Packaged")
		self.assertEqual(inclusion.get("created_package_code"), package_code)

	def test_002_second_call_is_idempotent(self):
		"""SEED-TEST-P4-004-002: Second identical API call returns existing package."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		if not _require_template():
			self.skipTest("No active Procurement Template with profiles available")

		inclusion_code = self._ensure_works_inclusion()
		first = _create_via_api(inclusion_code)
		self.assertTrue(first.get("ok"), first)
		package_code = first.get("package_code")
		self.assertTrue(package_code)
		self._track_package(package_code, first.get("package_line_codes"))

		count_after_first = frappe.db.count(
			"Procurement Package",
			{"planning_inclusion_code": inclusion_code, "is_active": 1},
		)

		second = _create_via_api(inclusion_code)
		self.assertTrue(second.get("ok"), second)
		self.assertEqual(second.get("action"), "existing")
		self.assertEqual(second.get("package_code"), package_code)

		count_after_second = frappe.db.count(
			"Procurement Package",
			{"planning_inclusion_code": inclusion_code, "is_active": 1},
		)
		self.assertEqual(count_after_first, count_after_second)

	def test_003_unknown_inclusion_returns_not_found(self):
		"""SEED-TEST-P4-004-003: Unknown inclusion code returns structured error."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = _create_via_api("PLANINCL-DOES-NOT-EXIST-004")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackageFromInclusion.INCLUSION_NOT_FOUND)

	def test_004_whitelisted_api_delegates_for_administrator(self):
		"""SEED-TEST-P4-004-004: Administrator succeeds via whitelisted API."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		if not _require_template():
			self.skipTest("No active Procurement Template with profiles available")

		inclusion_code = self._ensure_works_inclusion()
		frappe.set_user("Administrator")
		out = _create_via_api(inclusion_code)
		self.assertTrue(out.get("ok"), out)
		self.assertIn(out.get("action"), ("created", "existing"))
		self._track_package(out.get("package_code"), out.get("package_line_codes"))

	def test_005_guest_denied(self):
		"""SEED-TEST-P4-004-005: Guest receives PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		out = _create_via_api(INCLUSION_CODE)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_006_planning_reviewer_denied(self):
		"""SEED-TEST-P4-004-006: Planning Reviewer cannot create package from inclusion."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		if not frappe.db.exists("User", _REVIEWER_USER):
			self.skipTest(f"User {_REVIEWER_USER} not present on site")

		frappe.set_user(_REVIEWER_USER)
		out = _create_via_api(INCLUSION_CODE)
		self.assertFalse(out.get("ok"))
		self.assertIn(out.get("error_code"), ("PP_ACCESS_DENIED", "PP2-BLOCK-NOT-PERMITTED"))
