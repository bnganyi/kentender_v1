# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-011 — Package release read/write service and API."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, today

from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.package_release import (
	get_pp_package_release,
	mark_pp_package_ready_for_release,
	release_pp_package_to_tender,
)
from kentender_procurement.procurement_planning.api.package_review import (
	record_pp_package_review_decision,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PLAN_ACTIVE,
	READINESS_PASSED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	FISCAL_YEAR,
	INCLUSION_CODE,
	PKG_CODE,
	PKG_REQUIRED_STD_TYPE,
	PLAN_CODE,
	PLAN_CREATOR_EMAIL,
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.package_method import (
	record_package_method_for_api,
)
from kentender_procurement.procurement_planning.services.package_readiness_api import (
	run_package_readiness_for_api,
)
from kentender_procurement.procurement_planning.services.package_release_api import (
	get_package_release_context,
	mark_package_ready_for_api,
	release_package_to_tender_for_api,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	reconcile_package_readiness_staleness,
)
from kentender_procurement.procurement_planning.services.package_workspace import (
	get_package_workspace_context,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReleaseToTender,
	PlanningPermission,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_JOURNEY_CODE = "JRN-MOH-2026-001"
_REVIEWER_USER = "planning.reviewer@moh.test"
_AUTHORITY_USER = "planning.authority@moh.test"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


def _works_payload(**overrides) -> dict:
	base = {
		"procurement_category": "Works",
		"procurement_method": "Open Tender",
		"required_std_category": "Works",
		"required_std_type": PKG_REQUIRED_STD_TYPE,
		"method_basis": "Template",
		"override_flag": False,
	}
	base.update(overrides)
	return base


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


def _journey_suffix(journey_code: str) -> str:
	jc = (journey_code or "").strip()
	if jc.upper().startswith("JRN-"):
		return jc[4:]
	return jc


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


def _release_core(out: dict) -> dict:
	skip = {
		"ok",
		"role_key",
		"package",
		"may_mark_ready",
		"may_release",
		"package_status",
		"locked_after_release",
	}
	return {key: value for key, value in out.items() if key not in skip}


class TestPP2PackageReleaseApiP4011(IntegrationTestCase):
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
			for review in frappe.get_all(
				"Package Review Decision",
				filters={"package_code": row.name},
				pluck="name",
			):
				if frappe.db.exists("Package Review Decision", review):
					frappe.delete_doc(
						"Package Review Decision",
						review,
						force=True,
						ignore_permissions=True,
					)
			for readiness in frappe.get_all(
				"Package Readiness Result",
				filters={"package_code": row.name},
				pluck="name",
			):
				if frappe.db.exists("Package Readiness Result", readiness):
					frappe.delete_doc(
						"Package Readiness Result",
						readiness,
						force=True,
						ignore_permissions=True,
					)
			for decision in frappe.get_all(
				"Package Method Decision",
				filters={"package_code": row.name},
				pluck="name",
			):
				if frappe.db.exists("Package Method Decision", decision):
					frappe.delete_doc(
						"Package Method Decision",
						decision,
						force=True,
						ignore_permissions=True,
					)
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

	def _ensure_reviewer_user(self) -> str:
		ensure_roles()
		moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
		dept = ensure_department(f"Dept Review {frappe.generate_hash(length=4)}", moh)
		upsert_seed_user(
			_REVIEWER_USER,
			"Planning Reviewer MOH",
			"Planning Reviewer",
			entity_name=moh,
			department_docname=dept,
		)
		return _REVIEWER_USER

	def _ensure_authority_user(self) -> str:
		frappe.set_user("Administrator")
		ensure_roles()
		moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
		dept = ensure_department(f"Dept Auth {frappe.generate_hash(length=4)}", moh)
		upsert_seed_user(
			_AUTHORITY_USER,
			"Planning Authority MOH",
			"Planning Authority",
			entity_name=moh,
			department_docname=dept,
		)
		return _AUTHORITY_USER

	def _ensure_planner_user(self) -> str:
		frappe.set_user("Administrator")
		ensure_roles()
		moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
		dept = ensure_department(f"Dept Plan {frappe.generate_hash(length=4)}", moh)
		upsert_seed_user(
			PLAN_CREATOR_EMAIL,
			"Procurement Planner MOH",
			"Procurement Planner",
			entity_name=moh,
			department_docname=dept,
		)
		return PLAN_CREATOR_EMAIL

	def _seed_upstream_handoffs(
		self, journey_code: str, demand_code: str, budget_line_code: str
	) -> None:
		suffix = _journey_suffix(journey_code)
		cards = (
			(
				f"DEMAPP-{suffix}",
				"Demand Approval Certificate",
				"Demands",
				"Procurement Planning",
				"Demand",
				demand_code,
			),
			(
				f"BUDCONF-{suffix}",
				"Budget Funding Confirmation",
				"Budget",
				"Demands",
				"Budget Line",
				budget_line_code,
			),
		)
		for handoff_code, title, source_mod, target_mod, src_type, src_code in cards:
			create_or_update_handoff_card(
				{
					"handoff_code": handoff_code,
					"handoff_title": title,
					"journey_code": journey_code,
					"source_module": source_mod,
					"target_module": target_mod,
					"status": "Consumed",
					"next_action": "Proceed to procurement planning.",
					"source_object_type": src_type,
					"source_object_code": src_code,
				}
			)
			self._cleanup.append(("Procurement Handoff Card", handoff_code))

	def _in_review_setup(self, package_code: str | None = None) -> str:
		package_code = package_code or self._ensure_works_package()
		method_out = record_package_method_for_api(
			package_code, _works_payload(), "Administrator"
		)
		self.assertTrue(method_out.get("ok"), method_out)
		if method_out.get("method_decision_code"):
			self._cleanup.append(("Package Method Decision", method_out["method_decision_code"]))

		submit_out = submit_package_for_review(package_code, "Administrator")
		self.assertTrue(submit_out.get("ok"), submit_out)
		submit_code = submit_out.get("review_decision_code")
		if submit_code:
			self._cleanup.append(("Package Review Decision", submit_code))
		frappe.db.commit()
		return package_code

	def _approve_package(self, package_code: str) -> None:
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		out = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps({"decision": "Approved"}),
		)
		self.assertTrue(out.get("ok"), out)
		review_code = out.get("review_decision_code")
		if review_code:
			self._cleanup.append(("Package Review Decision", review_code))
		frappe.set_user("Administrator")

	def _approved_with_passing_readiness(self) -> str:
		package_code = self._in_review_setup()
		self._approve_package(package_code)
		journey_code = (
			frappe.db.get_value("Procurement Package", package_code, "journey_code")
			or _JOURNEY_CODE
		)
		if not frappe.db.get_value("Procurement Package", package_code, "journey_code"):
			frappe.db.set_value(
				"Procurement Package",
				package_code,
				"journey_code",
				journey_code,
				update_modified=False,
			)
		self._seed_upstream_handoffs(journey_code, DEMAND_CODE, BUDGET_LINE_CODE)
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			{
				"schedule_start": today(),
				"schedule_end": add_days(today(), 30),
			},
			update_modified=False,
		)
		frappe.db.commit()

		readiness_out = run_package_readiness_for_api(package_code, "Administrator")
		self.assertTrue(readiness_out.get("ok"), readiness_out)
		self.assertEqual(readiness_out.get("result_status"), READINESS_PASSED)
		if readiness_out.get("readiness_code"):
			self._cleanup.append(("Package Readiness Result", readiness_out["readiness_code"]))
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_APPROVED,
		)
		return package_code

	def _xmv_ok(self):
		result = MagicMock()
		result.has_critical.return_value = False
		return result

	def _release_patches(self, *, has_tender: bool = True):
		return patch.multiple(
			"kentender_procurement.procurement_planning.services.package_release_service",
			deliver_procurement_package_release=MagicMock(),
			package_has_release_tender=MagicMock(return_value=has_tender),
			validate_package_for_release_xmv=MagicMock(return_value=self._xmv_ok()),
		)

	def test_001_approved_read_gates(self):
		"""SEED-TEST-P4-011-001: Approved package has no release; may_mark ready; may_release blocked."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		out = get_package_release_context(package_code, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(out.get("release"))
		self.assertEqual(out.get("package_status"), PKG_APPROVED)
		self.assertTrue((out.get("may_mark_ready") or {}).get("allowed"))
		self.assertFalse((out.get("may_release") or {}).get("allowed"))

	def test_002_mark_ready_via_api(self):
		"""SEED-TEST-P4-011-002: Mark ready via API transitions Approved → Ready for Release."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		out = mark_pp_package_ready_for_release(package_code=package_code)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("from_state"), PKG_APPROVED)
		self.assertEqual(out.get("to_state"), PKG_READY_FOR_RELEASE)
		self.assertEqual(out.get("status"), PKG_READY_FOR_RELEASE)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_READY_FOR_RELEASE,
		)

	def test_003_release_via_api_be_008(self):
		"""SEED-TEST-P4-011-003: Release via API creates PKGREL and Released to Tender state."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		mark_out = mark_pp_package_ready_for_release(package_code=package_code)
		self.assertTrue(mark_out.get("ok"), mark_out)

		expected_release = pkgrel_handoff_code_from_journey_code(_JOURNEY_CODE)
		authority = self._ensure_authority_user()
		frappe.set_user(authority)
		frappe.db.commit()

		with self._release_patches(has_tender=True):
			out = release_pp_package_to_tender(package_code=package_code)

		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("action"), "created")
		self.assertEqual(out.get("from_state"), PKG_READY_FOR_RELEASE)
		self.assertEqual(out.get("to_state"), PKG_RELEASED)
		self.assertEqual(out.get("release_code"), expected_release)
		self._cleanup.append(("Procurement Handoff Card", expected_release))

		pkg = frappe.get_doc("Procurement Package", package_code)
		self.assertEqual(pkg.status, PKG_RELEASED)
		self.assertEqual(pkg.release_code, expected_release)
		self.assertTrue(bool(pkg.locked_after_release))

	def test_004_read_after_release(self):
		"""SEED-TEST-P4-011-004: Read after release exposes release.handoff_code."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		self.assertTrue(
			mark_pp_package_ready_for_release(package_code=package_code).get("ok")
		)

		expected_release = pkgrel_handoff_code_from_journey_code(_JOURNEY_CODE)
		authority = self._ensure_authority_user()
		frappe.set_user(authority)
		frappe.db.commit()

		with self._release_patches(has_tender=True):
			release_out = release_pp_package_to_tender(package_code=package_code)
		self.assertTrue(release_out.get("ok"), release_out)
		self._cleanup.append(("Procurement Handoff Card", expected_release))

		frappe.set_user("Administrator")
		read_out = get_pp_package_release(package_code=package_code)
		self.assertTrue(read_out.get("ok"), read_out)
		release = read_out.get("release") or {}
		self.assertEqual(release.get("handoff_code"), expected_release)
		self.assertTrue(read_out.get("locked_after_release"))

	def test_005_second_release_recalled(self):
		"""SEED-TEST-P4-011-005: Second release returns action=recalled."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		self.assertTrue(
			mark_pp_package_ready_for_release(package_code=package_code).get("ok")
		)

		expected_release = pkgrel_handoff_code_from_journey_code(_JOURNEY_CODE)
		authority = self._ensure_authority_user()
		frappe.set_user(authority)
		frappe.db.commit()

		with self._release_patches(has_tender=True):
			first = release_pp_package_to_tender(package_code=package_code)
			self._cleanup.append(("Procurement Handoff Card", expected_release))
			second = release_pp_package_to_tender(package_code=package_code)

		self.assertTrue(first.get("ok"), first)
		self.assertEqual(first.get("action"), "created")
		self.assertTrue(second.get("ok"), second)
		self.assertEqual(second.get("action"), "recalled")
		self.assertEqual(second.get("release_code"), expected_release)

	def test_006_release_blocked_stale_readiness(self):
		"""SEED-TEST-P4-011-006: Release with stale readiness returns READINESS_STALE."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		self.assertTrue(
			mark_pp_package_ready_for_release(package_code=package_code).get("ok")
		)
		frappe.set_user("Administrator")
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"estimated_value",
			frappe.db.get_value("Procurement Package", package_code, "estimated_value") + 5000,
			update_modified=False,
		)
		reconcile = reconcile_package_readiness_staleness(package_code)
		self.assertTrue(reconcile.get("stale"))

		authority = self._ensure_authority_user()
		frappe.set_user(authority)
		out = release_pp_package_to_tender(package_code=package_code)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackageReleaseToTender.READINESS_STALE)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_READY_FOR_RELEASE,
		)

	def test_007_planner_denied_on_release_write(self):
		"""SEED-TEST-P4-011-007: Procurement Planner cannot release to tender."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		self.assertTrue(
			mark_pp_package_ready_for_release(package_code=package_code).get("ok")
		)

		planner = self._ensure_planner_user()
		frappe.set_user(planner)
		out = release_pp_package_to_tender(package_code=package_code)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			("PP_ACCESS_DENIED", PlanningPermission.NOT_PERMITTED),
		)

	def test_008_guest_and_officer_denied_on_read(self):
		"""SEED-TEST-P4-011-008: Guest and Procurement Officer receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_package_release(package_code=PKG_CODE)
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		officer_email = f"officer.release.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Release",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._cleanup.append(("User", officer_email))

		frappe.set_user(officer_email)
		officer_out = get_pp_package_release(package_code=PKG_CODE)
		self.assertFalse(officer_out.get("ok"))
		self.assertEqual(officer_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_009_api_delegates_to_service(self):
		"""SEED-TEST-P4-011-009: Whitelisted API delegates to release service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		frappe.set_user("Administrator")
		api_read = get_pp_package_release(package_code=package_code)
		svc_read = get_package_release_context(package_code, "Administrator")
		self.assertTrue(api_read.get("ok"), api_read)
		self.assertTrue(svc_read.get("ok"), svc_read)
		self.assertEqual(_release_core(api_read), _release_core(svc_read))

		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		api_mark = mark_pp_package_ready_for_release(package_code=package_code)
		svc_mark = mark_package_ready_for_api(package_code, reviewer)
		self.assertTrue(api_mark.get("ok"), api_mark)
		self.assertTrue(svc_mark.get("ok"), svc_mark)
		self.assertEqual(api_mark.get("status"), svc_mark.get("status"))

		frappe.set_user(reviewer)
		self.assertTrue(
			mark_pp_package_ready_for_release(package_code=package_code).get("ok")
		)

		expected_release = pkgrel_handoff_code_from_journey_code(_JOURNEY_CODE)
		authority = self._ensure_authority_user()
		frappe.set_user(authority)
		frappe.db.commit()
		with self._release_patches(has_tender=True):
			api_release = release_pp_package_to_tender(package_code=package_code)
			svc_release = release_package_to_tender_for_api(package_code, authority)
		self.assertTrue(api_release.get("ok"), api_release)
		self.assertTrue(svc_release.get("ok"), svc_release)
		self.assertEqual(api_release.get("release_code"), svc_release.get("release_code"))
		if api_release.get("release_code"):
			self._cleanup.append(("Procurement Handoff Card", expected_release))

	def test_010_matches_workspace_release_tab(self):
		"""SEED-TEST-P4-011-010: Dedicated release API release matches workspace tabs.release."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._approved_with_passing_readiness()
		release_out = get_package_release_context(package_code, "Administrator")
		workspace_out = get_package_workspace_context(package_code, "Administrator")
		self.assertTrue(release_out.get("ok"), release_out)
		self.assertTrue(workspace_out.get("ok"), workspace_out)
		self.assertEqual(
			release_out.get("release"),
			(workspace_out.get("tabs") or {}).get("release"),
		)
