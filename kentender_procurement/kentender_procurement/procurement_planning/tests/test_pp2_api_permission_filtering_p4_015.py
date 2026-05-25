# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-015 — Consolidated PP2 API permission filtering (roles §13.1 / PP2-NG-011)."""

from __future__ import annotations

import json
from collections.abc import Callable

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)
from kentender_procurement.procurement_planning.api.approved_demands import (
	get_pp_approved_demand_planning_drawer,
	get_pp_approved_demands_awaiting_planning,
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.package_lines import (
	get_pp_package_line_traceability,
)
from kentender_procurement.procurement_planning.api.package_method import (
	get_pp_package_method,
	record_pp_package_method_decision,
)
from kentender_procurement.procurement_planning.api.package_readiness import (
	get_pp_package_readiness,
	run_pp_package_readiness_checks,
)
from kentender_procurement.procurement_planning.api.package_release import (
	get_pp_package_release,
	mark_pp_package_ready_for_release,
	release_pp_package_to_tender,
)
from kentender_procurement.procurement_planning.api.package_review import (
	get_pp_package_review,
	record_pp_package_review_decision,
)
from kentender_procurement.procurement_planning.api.package_workbench import (
	get_pp_package_workbench,
)
from kentender_procurement.procurement_planning.api.package_workspace import (
	get_pp_package_workspace,
)
from kentender_procurement.procurement_planning.api.planning_evidence import (
	get_pp_planning_evidence_timeline,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.api.planning_journey import (
	get_pp_planning_journey_handoffs,
)
from kentender_procurement.procurement_planning.api.released_to_tender import (
	get_pp_planning_release_package,
	get_pp_released_to_tender,
)
from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	INCLUSION_CODE,
	PKG_CODE,
	PKGREL_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PlanningPermission,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_OFFICER_USER = "procurement.officer@moh.test"
_TENDER_MANAGER_USER = "tender.manager.p4015@moh.test"
_BUDGET_OFFICER_USER = "budget.officer.p4015@moh.test"
_MOE_PLANNER = "planner.moe.scope@test.local"

_DENIED_READ_CODES = frozenset(
	(
		"PP_ACCESS_DENIED",
		PlanningPermission.NOT_PERMITTED,
	)
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


def _bootstrap_upstream_only() -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	ensure_procuring_entity(C.ENTITY_MOE, "Ministry of Education")
	from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
	from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
	from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey

	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")


def _find_demand_row(rows: list[dict], demand_code: str) -> dict | None:
	for row in rows or []:
		demand = row.get("demand") or {}
		if demand.get("code") == demand_code or row.get("demand_code") == demand_code:
			return row
		if row.get("demand_id") == demand_code:
			return row
	return None


class TestPP2ApiPermissionFilteringP4015(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not _pp_ok():
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
		clear_master_planning_seed()
		frappe.db.commit()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()
		for doctype, name in reversed(getattr(self, "_cleanup", [])):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _load_consumed_works_seed(self) -> None:
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed not available: {seed}")
		if not frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}):
			self.skipTest("WORKS package seed not present on site.")

	def _ensure_supplier_user(self) -> str:
		email = f"supplier.p4015.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "PP2",
					"last_name": "Supplier",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Supplier")
			self._cleanup.append(("User", email))
		return email

	def _ensure_officer_user(self) -> str:
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

	def _ensure_role(self, role_name: str) -> None:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)

	def _ensure_tender_manager_user(self) -> str:
		self._ensure_role("Tender Manager")
		ensure_roles()
		moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
		dept = ensure_department(f"Dept TM {frappe.generate_hash(length=4)}", moh)
		upsert_seed_user(
			_TENDER_MANAGER_USER,
			"Tender Manager MOH",
			"Tender Manager",
			entity_name=moh,
			department_docname=dept,
		)
		return _TENDER_MANAGER_USER

	def _ensure_budget_officer_user(self) -> str:
		self._ensure_role("Budget Officer")
		ensure_roles()
		moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
		dept = ensure_department(f"Dept Budget {frappe.generate_hash(length=4)}", moh)
		upsert_seed_user(
			_BUDGET_OFFICER_USER,
			"Budget Officer MOH",
			"Budget Officer",
			entity_name=moh,
			department_docname=dept,
		)
		return _BUDGET_OFFICER_USER

	def _ensure_moe_planner(self) -> str:
		ensure_roles()
		moe = ensure_procuring_entity(C.ENTITY_MOE, "Ministry of Education")
		dept = ensure_department(f"Dept MOE {frappe.generate_hash(length=4)}", moe)
		upsert_seed_user(
			_MOE_PLANNER,
			"Planner MOE Scope",
			"Procurement Planner",
			entity_name=moe,
			department_docname=dept,
		)
		return _MOE_PLANNER

	def _p4_read_endpoints(self) -> list[tuple[str, Callable[..., dict]]]:
		return [
			("queue", get_pp_approved_demands_awaiting_planning),
			("drawer", lambda: get_pp_approved_demand_planning_drawer(demand_code=DEMAND_CODE)),
			("workbench", get_pp_package_workbench),
			("workspace", lambda: get_pp_package_workspace(package_code=PKG_CODE)),
			("lines", lambda: get_pp_package_line_traceability(package_code=PKG_CODE)),
			("method", lambda: get_pp_package_method(package_code=PKG_CODE)),
			("readiness", lambda: get_pp_package_readiness(package_code=PKG_CODE)),
			("review", lambda: get_pp_package_review(package_code=PKG_CODE)),
			("release_read", lambda: get_pp_package_release(package_code=PKG_CODE)),
			("released_list", get_pp_released_to_tender),
			(
				"release_detail",
				lambda: get_pp_planning_release_package(release_code=PKGREL_CODE),
			),
			("evidence", lambda: get_pp_planning_evidence_timeline(package_code=PKG_CODE)),
			("journey", lambda: get_pp_planning_journey_handoffs(package_code=PKG_CODE)),
		]

	def _p4_write_endpoints(self) -> list[tuple[str, Callable[..., dict]]]:
		return [
			(
				"include",
				lambda: include_pp_demand_in_procurement_plan(
					demand_code=DEMAND_CODE,
					procurement_plan_code=PLAN_CODE,
					demand_item_codes=json.dumps([DEMAND_ITEM_CODE]),
				),
			),
			(
				"create_package",
				lambda: create_pp_package_from_planning_inclusion(inclusion_code=INCLUSION_CODE),
			),
			(
				"method_write",
				lambda: record_pp_package_method_decision(
					package_code=PKG_CODE,
					payload=json.dumps({"procurement_category": "Works"}),
				),
			),
			(
				"readiness_write",
				lambda: run_pp_package_readiness_checks(package_code=PKG_CODE),
			),
			(
				"review_write",
				lambda: record_pp_package_review_decision(
					package_code=PKG_CODE,
					payload=json.dumps({"decision": "Approve"}),
				),
			),
			(
				"mark_ready",
				lambda: mark_pp_package_ready_for_release(package_code=PKG_CODE),
			),
			(
				"release_write",
				lambda: release_pp_package_to_tender(package_code=PKG_CODE),
			),
		]

	def test_001_supplier_denied_on_all_p4_read_endpoints(self):
		"""SEED-TEST-P4-015-001: Supplier receives PP_ACCESS_DENIED on all P4 read APIs."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		supplier = self._ensure_supplier_user()
		frappe.set_user(supplier)
		for label, call in self._p4_read_endpoints():
			with self.subTest(endpoint=label):
				out = call()
				self.assertFalse(out.get("ok"), out)
				self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_002_guest_denied_on_all_p4_read_endpoints(self):
		"""SEED-TEST-P4-015-002: Guest receives PP_ACCESS_DENIED on all P4 read APIs."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		frappe.set_user("Guest")
		for label, call in self._p4_read_endpoints():
			with self.subTest(endpoint=label):
				out = call()
				self.assertFalse(out.get("ok"), out)
				self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_003_supplier_denied_on_p4_write_endpoints(self):
		"""SEED-TEST-P4-015-003: Supplier is denied on P4 write APIs."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		supplier = self._ensure_supplier_user()
		frappe.set_user(supplier)
		for label, call in self._p4_write_endpoints():
			with self.subTest(endpoint=label):
				out = call()
				self.assertFalse(out.get("ok"), out)
				self.assertIn(out.get("error_code"), _DENIED_READ_CODES)

	def test_004_officer_role_contrast_internal_vs_extended_reads(self):
		"""SEED-TEST-P4-015-004: Officer denied internal reads but allowed extended reads."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		officer = self._ensure_officer_user()
		frappe.set_user(officer)

		internal = {
			"queue": get_pp_approved_demands_awaiting_planning(),
			"workbench": get_pp_package_workbench(),
			"workspace": get_pp_package_workspace(package_code=PKG_CODE),
		}
		for label, out in internal.items():
			with self.subTest(surface=label):
				self.assertFalse(out.get("ok"), out)
				self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

		extended = {
			"released_list": get_pp_released_to_tender(),
			"evidence": get_pp_planning_evidence_timeline(package_code=PKG_CODE),
			"journey": get_pp_planning_journey_handoffs(package_code=PKG_CODE),
		}
		for label, out in extended.items():
			with self.subTest(surface=label):
				self.assertTrue(out.get("ok"), out)

	def test_005_moe_planner_denied_moh_package_workspace(self):
		"""SEED-TEST-P4-015-005: MOE-scoped planner cannot read MOH package workspace."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		moe_planner = self._ensure_moe_planner()
		frappe.set_user(moe_planner)
		out = get_pp_package_workspace(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("error_code"), "NO_PACKAGE_PERMISSION")

	def test_006_moe_planner_queue_excludes_moh_demand(self):
		"""SEED-TEST-P4-015-006: MOE-scoped planner queue excludes MOH WORKS demand."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		clear_master_planning_seed()
		frappe.db.commit()
		from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
		from kentender_procurement.demand_intake.seeds.works_master_demand_seed import (
			upsert_works_master_demand,
		)

		assert upsert_works_master_budget().get("ok")
		assert upsert_works_master_demand().get("ok")

		moe_planner = self._ensure_moe_planner()
		frappe.set_user(moe_planner)
		out = get_pp_approved_demands_awaiting_planning(search_text=DEMAND_CODE)
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(_find_demand_row(out.get("rows") or [], DEMAND_CODE))

	def test_007_gate_registry_matches_planner_and_supplier_profiles(self):
		"""SEED-TEST-P4-015-007: pp_api_gates profiles align with planner allow / supplier deny."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		planner = "planner@moh.test"
		if not frappe.db.exists("User", planner):
			moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
			dept = ensure_department(C.DEPT_PROC, moh)
			upsert_seed_user(
				planner,
				"Procurement Planner MOH",
				"Procurement Planner",
				entity_name=moh,
				department_docname=dept,
			)

		supplier = self._ensure_supplier_user()
		internal_profiles = (
			pp_api_gates.PLANNING_QUEUE_READ,
			pp_api_gates.PLANNING_PACKAGE_READ,
		)
		readiness_profile = (pp_api_gates.PLANNING_READINESS_READ,)
		extended_profiles = (
			pp_api_gates.RELEASED_TO_TENDER_READ,
			pp_api_gates.PLANNING_EVIDENCE_READ,
		)

		frappe.set_user(planner)
		for profile in internal_profiles + readiness_profile + extended_profiles:
			with self.subTest(user="planner", profile=profile):
				self.assertTrue(pp_api_gates.user_may_access(profile, planner))
				self.assertTrue(pp_api_gates.check_profile_access(profile, planner))

		frappe.set_user(supplier)
		for profile in internal_profiles + readiness_profile + extended_profiles:
			with self.subTest(user="supplier", profile=profile):
				self.assertFalse(pp_api_gates.user_may_access(profile, supplier))
				self.assertFalse(pp_api_gates.check_profile_access(profile, supplier))

		frappe.set_user("Administrator")
		tm = self._ensure_tender_manager_user()
		budget = self._ensure_budget_officer_user()
		self.assertEqual(resolve_pp_role_key(tm), "tender_manager")
		self.assertEqual(resolve_pp_role_key(budget), "budget")
		self.assertFalse(pp_api_gates.user_may_access(pp_api_gates.PLANNING_PACKAGE_READ, budget))
		self.assertTrue(pp_api_gates.user_may_access(pp_api_gates.PLANNING_READINESS_READ, budget))
		self.assertTrue(
			pp_api_gates.check_profile_access(
				pp_api_gates.PLANNING_READINESS_READ,
				budget,
				require_planning_read=False,
				require_package_read=False,
			)
		)

	def test_008_tender_manager_and_budget_officer_extended_reads(self):
		"""SEED-TEST-P4-015-008: TM/BO allowed on extended reads; BO may read readiness only."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		frappe.set_user("Administrator")
		tm = self._ensure_tender_manager_user()
		budget = self._ensure_budget_officer_user()

		frappe.set_user(tm)
		for label, call in (
			("released_list", get_pp_released_to_tender),
			("evidence", lambda: get_pp_planning_evidence_timeline(package_code=PKG_CODE)),
			("journey", lambda: get_pp_planning_journey_handoffs(package_code=PKG_CODE)),
		):
			with self.subTest(role="tender_manager", surface=label):
				out = call()
				self.assertTrue(out.get("ok"), out)
				self.assertEqual(out.get("role_key"), "tender_manager")

		internal = get_pp_package_workspace(package_code=PKG_CODE)
		self.assertFalse(internal.get("ok"))
		self.assertEqual(internal.get("error_code"), "PP_ACCESS_DENIED")

		frappe.set_user(budget)
		readiness = get_pp_package_readiness(package_code=PKG_CODE)
		self.assertTrue(readiness.get("ok"), readiness)
		self.assertEqual(readiness.get("role_key"), "budget")
		self.assertFalse((readiness.get("may_run") or {}).get("allowed"))

		run_out = run_pp_package_readiness_checks(package_code=PKG_CODE)
		self.assertFalse(run_out.get("ok"))
		self.assertIn(
			run_out.get("error_code"),
			("PP_ACCESS_DENIED", PlanningPermission.NOT_PERMITTED),
		)

		for label, call in (
			("released_list", get_pp_released_to_tender),
			("evidence", lambda: get_pp_planning_evidence_timeline(package_code=PKG_CODE)),
			("journey", lambda: get_pp_planning_journey_handoffs(package_code=PKG_CODE)),
		):
			with self.subTest(role="budget_officer", surface=label):
				out = call()
				self.assertTrue(out.get("ok"), out)
				self.assertEqual(out.get("role_key"), "budget")

		workspace = get_pp_package_workspace(package_code=PKG_CODE)
		self.assertFalse(workspace.get("ok"))
		self.assertEqual(workspace.get("error_code"), "PP_ACCESS_DENIED")
