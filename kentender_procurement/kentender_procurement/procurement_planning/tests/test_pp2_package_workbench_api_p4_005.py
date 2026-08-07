# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-005 — Package workbench list service and API."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.package_workbench import (
	get_pp_package_workbench,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_DRAFT,
	PLAN_ACTIVE,
	WB_IN_PREPARATION,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	FISCAL_YEAR,
	INCLUSION_CODE,
	PKG_CODE,
	PKG_PROCUREMENT_CATEGORY,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_NAME,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.package_workbench import (
	get_package_workbench_rows,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"


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


def _include_and_create_package() -> str:
	out = include_pp_demand_in_procurement_plan(
		demand_code=DEMAND_CODE,
		procurement_plan_code=PLAN_CODE,
		demand_item_codes=json.dumps([DEMAND_ITEM_CODE]),
	)
	assert out.get("ok"), out
	create_out = create_pp_package_from_planning_inclusion(inclusion_code=out.get("inclusion_code"))
	assert create_out.get("ok"), create_out
	package_code = create_out.get("package_code")
	assert package_code
	return str(package_code)


def _find_row(rows: list[dict], package_code: str) -> dict | None:
	for row in rows or []:
		pkg = row.get("package") or {}
		if pkg.get("code") == package_code or pkg.get("id") == package_code:
			return row
	return None


class TestPP2PackageWorkbenchApiP4005(IntegrationTestCase):
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

	def _ensure_works_package(self) -> str:
		if not _require_template():
			self.skipTest("No active Procurement Template with profiles available")
		return _include_and_create_package()

	def test_001_works_draft_package_row_shape(self):
		"""SEED-TEST-P4-005-001: Draft WORKS package row includes tracker fields."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		out = get_package_workbench_rows({"search_text": package_code}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		row = _find_row(out.get("rows") or [], package_code)
		self.assertIsNotNone(row, out)
		assert row is not None

		pkg = row.get("package") or {}
		self.assertEqual(pkg.get("code"), package_code)
		self.assertEqual(pkg.get("name"), PKG_TITLE)
		self.assertEqual(row.get("status"), PKG_DRAFT)
		self.assertEqual(row.get("workbench_group"), WB_IN_PREPARATION)
		self.assertEqual(row.get("readiness_status"), "Not Run")
		self.assertEqual(row.get("category"), PKG_PROCUREMENT_CATEGORY)
		self.assertEqual(flt(row.get("estimated_value")), flt(ESTIMATED_VALUE))
		self.assertEqual(row.get("currency"), "KES")
		self.assertEqual((row.get("budget_line") or {}).get("code"), BUDGET_LINE_CODE)
		self.assertIsNone(row.get("tender"))
		next_action = row.get("next_action") or {}
		self.assertEqual(next_action.get("key"), "complete_package")
		self.assertTrue(next_action.get("label"))

	def test_002_search_filters_by_package_code(self):
		"""SEED-TEST-P4-005-002: Search text filters package rows."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		search_stem = package_code.rsplit("-", 1)[0]
		out = get_package_workbench_rows({"search_text": search_stem}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNotNone(_find_row(out.get("rows") or [], package_code))

		miss = get_package_workbench_rows({"search_text": "PKG-NO-MATCH-999"}, "Administrator")
		self.assertTrue(miss.get("ok"), miss)
		self.assertIsNone(_find_row(miss.get("rows") or [], package_code))

	def test_003_status_filter_excludes_other_statuses(self):
		"""SEED-TEST-P4-005-003: Status filter returns only matching packages."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		match = get_package_workbench_rows({"status": PKG_DRAFT}, "Administrator")
		self.assertTrue(match.get("ok"), match)
		self.assertIsNotNone(_find_row(match.get("rows") or [], package_code))

		miss = get_package_workbench_rows({"status": PKG_CONSUMED}, "Administrator")
		self.assertTrue(miss.get("ok"), miss)
		self.assertIsNone(_find_row(miss.get("rows") or [], package_code))

	def test_004_service_and_api_delegate(self):
		"""SEED-TEST-P4-005-004: Whitelisted API delegates to service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		frappe.set_user("Administrator")
		api_out = get_pp_package_workbench(search_text=package_code)
		svc_out = get_package_workbench_rows({"search_text": package_code}, "Administrator")
		self.assertTrue(api_out.get("ok"), api_out)
		self.assertTrue(svc_out.get("ok"), svc_out)
		self.assertEqual(api_out.get("total"), svc_out.get("total"))
		api_row = _find_row(api_out.get("rows") or [], package_code)
		svc_row = _find_row(svc_out.get("rows") or [], package_code)
		self.assertIsNotNone(api_row)
		self.assertIsNotNone(svc_row)
		assert api_row is not None and svc_row is not None
		self.assertEqual(api_row.get("status"), svc_row.get("status"))
		self.assertEqual(
			(api_row.get("next_action") or {}).get("key"),
			(svc_row.get("next_action") or {}).get("key"),
		)

	def test_005_guest_and_officer_denied(self):
		"""SEED-TEST-P4-005-005: Guest and Procurement Officer receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_package_workbench()
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		officer_email = f"officer.workbench.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Workbench",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._cleanup.append(("User", officer_email))

		frappe.set_user(officer_email)
		officer_out = get_pp_package_workbench()
		self.assertFalse(officer_out.get("ok"))
		self.assertEqual(officer_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_006_consumed_works_row_when_master_seed_present(self):
		"""SEED-TEST-P4-005-006: Consumed WORKS package shows tender and view_tender action."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed not available: {seed}")

		if not frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}):
			self.skipTest("WORKS package seed not present on site.")

		if not frappe.db.exists("TM2 Tender", {"tender_code": TENDER_CODE}):
			self.skipTest("WORKS TM2 tender not present on site.")

		out = get_package_workbench_rows({"search_text": PKG_CODE}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		row = _find_row(out.get("rows") or [], PKG_CODE)
		self.assertIsNotNone(row, out)
		assert row is not None

		handoff = row.get("planning_release_handoff") or {}
		handoff_status = str(handoff.get("status") or "").strip()
		if row.get("status") == PKG_CONSUMED:
			self.assertEqual(row.get("status"), PKG_CONSUMED)
		elif handoff_status == "Consumed":
			self.assertEqual(handoff_status, "Consumed")
		else:
			self.fail(f"Expected consumed WORKS package; got status={row.get('status')} handoff={handoff_status}")

		tender = row.get("tender") or {}
		tender_code = tender.get("code") or handoff.get("tender_code")
		self.assertEqual(tender_code, TENDER_CODE)
		next_action = row.get("next_action") or {}
		self.assertEqual(next_action.get("key"), "view_tender")
