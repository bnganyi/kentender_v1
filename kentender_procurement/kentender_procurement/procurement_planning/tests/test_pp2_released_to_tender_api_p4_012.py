# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-012 — Released to Tender list and Planning Release Package detail API."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.api.released_to_tender import (
	get_pp_planning_release_package,
	get_pp_released_to_tender,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_DRAFT,
	PLAN_ACTIVE,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	INCLUSION_CODE,
	PKG_CODE,
	PKGCONSUME_CODE,
	PKGREL_CODE,
	PLAN_CODE,
	PLAN_NAME,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.package_release_api import (
	get_package_release_context,
)
from kentender_procurement.procurement_planning.services.released_to_tender_api import (
	get_planning_release_package_context,
	get_released_to_tender_rows,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_OFFICER_USER = "procurement.officer@moh.test"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


def _find_row(rows: list[dict], release_code: str) -> dict | None:
	for row in rows or []:
		release = row.get("release") or {}
		if release.get("code") == release_code:
			return row
	return None


def _ensure_works_demand_queue_ready() -> None:
	clear_master_planning_seed()
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
			"fiscal_year": 2026,
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


class TestPP2ReleasedToTenderApiP4012(IntegrationTestCase):
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

	def _ensure_officer_user(self) -> str:
		frappe.set_user("Administrator")
		ensure_roles()
		moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
		dept = ensure_department(f"Dept Officer {frappe.generate_hash(length=4)}", moh)
		upsert_seed_user(
			_OFFICER_USER,
			"Procurement Officer MOH",
			"Procurement Officer",
			entity_name=moh,
			department_docname=dept,
		)
		return _OFFICER_USER

	def _load_consumed_works_seed(self) -> dict:
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed not available: {seed}")
		if not frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}):
			self.skipTest("WORKS package seed not present on site.")
		if not frappe.db.exists("TM2 Tender", {"tender_code": TENDER_CODE}):
			self.skipTest("WORKS TM2 tender not present on site.")
		return seed

	def test_001_draft_package_excluded_from_list(self):
		"""SEED-TEST-P4-012-001: Draft packages are excluded from Released to Tender list."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = _include_and_create_package()
		out = get_released_to_tender_rows({}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(_find_row(out.get("rows") or [], PKGREL_CODE))
		self.assertIsNone(
			next(
				(
					row
					for row in out.get("rows") or []
					if (row.get("package") or {}).get("code") == package_code
				),
				None,
			)
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_DRAFT,
		)

	def test_002_consumed_works_list_row(self):
		"""SEED-TEST-P4-012-002: CONSUMED WORKS seed appears with PKGREL, tender, PKGCONSUME."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_pp_released_to_tender()
		self.assertTrue(out.get("ok"), out)
		row = _find_row(out.get("rows") or [], PKGREL_CODE)
		self.assertIsNotNone(row, out)
		assert row is not None

		self.assertEqual((row.get("package") or {}).get("code"), PKG_CODE)
		tender = row.get("tender") or {}
		tender_code = tender.get("code") or (row.get("consumption") or {}).get("target_object_code")
		self.assertEqual(tender_code, TENDER_CODE)
		consumption = row.get("consumption") or {}
		self.assertEqual(consumption.get("status"), "Consumed")
		self.assertEqual(consumption.get("consumption_code"), PKGCONSUME_CODE)
		self.assertEqual((row.get("next_action") or {}).get("key"), "view_tender")

	def test_003_detail_returns_handoff_and_consumption(self):
		"""SEED-TEST-P4-012-003: Detail returns locked/passed-forward summaries and consumption."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_pp_planning_release_package(release_code=PKGREL_CODE)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("release_code"), PKGREL_CODE)
		self.assertEqual((out.get("package") or {}).get("code"), PKG_CODE)

		handoff = out.get("handoff") or {}
		self.assertEqual(handoff.get("handoff_code"), PKGREL_CODE)
		self.assertTrue(handoff.get("locked_summary"))
		self.assertTrue(handoff.get("passed_forward_summary"))

		consumption = out.get("consumption") or {}
		self.assertEqual(consumption.get("status"), "Consumed")
		self.assertEqual(consumption.get("consumption_code"), PKGCONSUME_CODE)
		self.assertEqual(consumption.get("target_object_code"), TENDER_CODE)

	def test_004_detail_release_matches_package_release_api(self):
		"""SEED-TEST-P4-012-004: Detail release block matches P4-011 package release read."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		detail = get_planning_release_package_context(PKGREL_CODE, "Administrator")
		release_ctx = get_package_release_context(PKG_CODE, "Administrator")
		self.assertTrue(detail.get("ok"), detail)
		self.assertTrue(release_ctx.get("ok"), release_ctx)
		self.assertEqual(detail.get("release"), release_ctx.get("release"))

	def test_005_officer_allowed_on_list(self):
		"""SEED-TEST-P4-012-005: Procurement Officer can read Released to Tender list."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		officer = self._ensure_officer_user()
		frappe.set_user(officer)
		out = get_pp_released_to_tender()
		self.assertTrue(out.get("ok"), out)
		self.assertIsNotNone(_find_row(out.get("rows") or [], PKGREL_CODE))

	def test_006_guest_and_supplier_denied(self):
		"""SEED-TEST-P4-012-006: Guest and Supplier receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_released_to_tender()
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		supplier_email = f"supplier.released.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", supplier_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": supplier_email,
					"first_name": "Released",
					"last_name": "Supplier",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Supplier")
			self._cleanup.append(("User", supplier_email))

		frappe.set_user(supplier_email)
		supplier_out = get_pp_released_to_tender()
		self.assertFalse(supplier_out.get("ok"))
		self.assertEqual(supplier_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_007_search_and_filter(self):
		"""SEED-TEST-P4-012-007: Search and consumption filter match WORKS release row."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		search_out = get_pp_released_to_tender(search_text=PKGREL_CODE)
		self.assertTrue(search_out.get("ok"), search_out)
		self.assertIsNotNone(_find_row(search_out.get("rows") or [], PKGREL_CODE))

		consumed_out = get_pp_released_to_tender(consumption_status="Consumed")
		self.assertTrue(consumed_out.get("ok"), consumed_out)
		self.assertIsNotNone(_find_row(consumed_out.get("rows") or [], PKGREL_CODE))

		miss = get_pp_released_to_tender(consumption_status="Not Consumed")
		self.assertTrue(miss.get("ok"), miss)
		self.assertIsNone(_find_row(miss.get("rows") or [], PKGREL_CODE))

	def test_008_api_delegates_to_service(self):
		"""SEED-TEST-P4-012-008: Whitelisted API delegates to released-to-tender service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		frappe.set_user("Administrator")
		api_list = get_pp_released_to_tender(search_text=PKG_CODE)
		svc_list = get_released_to_tender_rows({"search_text": PKG_CODE}, "Administrator")
		self.assertTrue(api_list.get("ok"), api_list)
		self.assertTrue(svc_list.get("ok"), svc_list)
		self.assertEqual(api_list.get("total"), svc_list.get("total"))
		self.assertEqual(
			(api_list.get("rows") or [{}])[0].get("release"),
			(svc_list.get("rows") or [{}])[0].get("release"),
		)

		api_detail = get_pp_planning_release_package(release_code=PKGREL_CODE)
		svc_detail = get_planning_release_package_context(PKGREL_CODE, "Administrator")
		self.assertTrue(api_detail.get("ok"), api_detail)
		self.assertTrue(svc_detail.get("ok"), svc_detail)
		self.assertEqual(api_detail.get("release_code"), svc_detail.get("release_code"))
		self.assertEqual(api_detail.get("handoff"), svc_detail.get("handoff"))
		self.assertEqual(api_detail.get("consumption"), svc_detail.get("consumption"))
