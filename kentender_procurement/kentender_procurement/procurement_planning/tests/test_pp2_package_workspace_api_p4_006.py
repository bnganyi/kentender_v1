# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-006 — Package workspace context service and API."""

from __future__ import annotations

import json

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.package_workspace import (
	get_pp_package_workspace,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PLAN_ACTIVE, READINESS_PASSED
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
	JOURNEY_CODE,
	PKG_CODE,
	PKGREL_CODE,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PKGREV_CODE,
	PLAN_CODE,
	PLAN_NAME,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.package_workspace import (
	get_package_workspace_context,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"

_TAB_KEYS = (
	"overview",
	"source_demand",
	"budget",
	"lines",
	"method",
	"readiness",
	"review",
	"release",
	"evidence",
	"advanced",
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


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


class TestPP2PackageWorkspaceApiP4006(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not _pp_ok() or not demand_consumers_live():
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

	def test_001_draft_workspace_has_required_sections(self):
		"""SEED-TEST-P4-006-001: Draft package workspace exposes all tab sections."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		out = get_package_workspace_context(package_code, "Administrator")
		self.assertTrue(out.get("ok"), out)

		for key in ("header", "journey", "right_panel", "tabs", "role_key"):
			self.assertIn(key, out, out)

		tabs = out.get("tabs") or {}
		for tab in _TAB_KEYS:
			self.assertIn(tab, tabs, tabs)

		header = out.get("header") or {}
		self.assertEqual((header.get("package") or {}).get("code"), package_code)
		self.assertEqual(header.get("status"), PKG_DRAFT)

		source = tabs.get("source_demand") or {}
		self.assertTrue(source.get("demand"))
		self.assertTrue(source.get("planning_inclusion"))

		budget = tabs.get("budget") or {}
		self.assertEqual((budget.get("budget_line") or {}).get("code"), BUDGET_LINE_CODE)

		readiness = tabs.get("readiness") or {}
		self.assertEqual(readiness.get("readiness_status"), "Not Run")

		self.assertIsNone(tabs.get("review"))
		self.assertIsNone(tabs.get("release"))

		panel = out.get("right_panel") or {}
		self.assertTrue(panel.get("current_state"))
		self.assertTrue((panel.get("next_action") or {}).get("key"))
		self.assertIsInstance(panel.get("actions"), dict)

	def test_002_lines_traceability_shape(self):
		"""SEED-TEST-P4-006-002: Lines tab exposes demand item → package line → budget refs."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		out = get_package_workspace_context(package_code, "Administrator")
		self.assertTrue(out.get("ok"), out)

		lines = (out.get("tabs") or {}).get("lines") or []
		self.assertGreaterEqual(len(lines), 1)
		line = lines[0]
		self.assertEqual((line.get("demand_item") or {}).get("code"), DEMAND_ITEM_CODE)
		self.assertTrue((line.get("package_line") or {}).get("code"))
		self.assertEqual((line.get("budget_line") or {}).get("code"), BUDGET_LINE_CODE)
		self.assertEqual(flt(line.get("amount")), flt(ESTIMATED_VALUE))

	def test_003_works_consumed_checkpoint_full_context(self):
		"""SEED-TEST-P4-006-003: WORKS consumed package returns full workspace context."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed not available: {seed}")

		if not frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}):
			self.skipTest("WORKS package seed not present on site.")

		if not frappe.db.exists("TM2 Tender", {"tender_code": TENDER_CODE}):
			self.skipTest("WORKS TM2 tender not present on site.")

		out = get_package_workspace_context(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)

		header = out.get("header") or {}
		self.assertEqual((header.get("package") or {}).get("code"), PKG_CODE)
		self.assertEqual(header.get("category"), "Works")
		self.assertEqual(header.get("method"), "Open Tender")

		method = (out.get("tabs") or {}).get("method") or {}
		self.assertEqual(method.get("procurement_category"), "Works")
		self.assertEqual(method.get("procurement_method"), "Open Tender")
		self.assertEqual(method.get("required_std_type"), PKG_REQUIRED_STD_TYPE)

		readiness = (out.get("tabs") or {}).get("readiness") or {}
		self.assertEqual(readiness.get("readiness_status"), READINESS_PASSED)
		self.assertTrue(readiness.get("current_result"))

		review = (out.get("tabs") or {}).get("review")
		self.assertIsNotNone(review)
		assert review is not None
		self.assertEqual(review.get("review_decision_code"), PKGREV_CODE)

		release = (out.get("tabs") or {}).get("release")
		self.assertIsNotNone(release)
		assert release is not None
		self.assertTrue(release.get("handoff_code"))

		tender = header.get("tender") or {}
		tender_code = tender.get("code") or (release or {}).get("tender_code")
		self.assertEqual(tender_code, TENDER_CODE)

		evidence = (out.get("tabs") or {}).get("evidence") or {}
		events = evidence.get("recent_events") or []
		self.assertGreater(len(events), 0)

		journey = out.get("journey") or {}
		self.assertEqual(journey.get("journey_code"), JOURNEY_CODE)
		self.assertTrue(journey.get("planning_steps"))
		inclusion = journey.get("planning_inclusion") or {}
		self.assertEqual(inclusion.get("handoff_code"), INCLUSION_CODE)
		release = journey.get("planning_release") or {}
		self.assertEqual(release.get("handoff_code"), PKGREL_CODE)

		panel = out.get("right_panel") or {}
		self.assertEqual((panel.get("next_action") or {}).get("key"), "view_tender")

	def test_004_service_and_api_delegate(self):
		"""SEED-TEST-P4-006-004: Whitelisted API delegates to workspace service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		frappe.set_user("Administrator")
		api_out = get_pp_package_workspace(package_code=package_code)
		svc_out = get_package_workspace_context(package_code, "Administrator")
		self.assertTrue(api_out.get("ok"), api_out)
		self.assertTrue(svc_out.get("ok"), svc_out)
		self.assertEqual(
			(api_out.get("header") or {}).get("status"),
			(svc_out.get("header") or {}).get("status"),
		)
		self.assertEqual(
			(api_out.get("right_panel") or {}).get("next_action"),
			(svc_out.get("right_panel") or {}).get("next_action"),
		)

	def test_005_guest_and_officer_denied(self):
		"""SEED-TEST-P4-006-005: Guest and Procurement Officer receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_package_workspace(package_code=PKG_CODE)
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		officer_email = f"officer.workspace.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Workspace",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._cleanup.append(("User", officer_email))

		frappe.set_user(officer_email)
		officer_out = get_pp_package_workspace(package_code=PKG_CODE)
		self.assertFalse(officer_out.get("ok"))
		self.assertEqual(officer_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_006_unknown_package_not_found(self):
		"""SEED-TEST-P4-006-006: Unknown package code returns NOT_FOUND."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_package_workspace_context("PKG-DOES-NOT-EXIST-006", "Administrator")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")
