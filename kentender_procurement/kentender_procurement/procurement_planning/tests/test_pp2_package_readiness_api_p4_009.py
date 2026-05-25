# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-009 — Package readiness read/run service and API."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, today

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.package_readiness import (
	get_pp_package_readiness,
	run_pp_package_readiness_checks,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PLAN_ACTIVE,
	READINESS_NOT_RUN,
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
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.package_method import (
	record_package_method_for_api,
)
from kentender_procurement.procurement_planning.services.package_readiness_api import (
	get_package_readiness_context,
	run_package_readiness_for_api,
)
from kentender_procurement.procurement_planning.services.package_workspace import (
	get_package_workspace_context,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReadiness,
	PlanningPermission,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_JOURNEY_CODE = "JRN-MOH-2026-001"


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
	from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
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


def _journey_suffix(journey_code: str) -> str:
	jc = (journey_code or "").strip()
	if jc.upper().startswith("JRN-"):
		return jc[4:]
	return jc


def _readiness_core(out: dict) -> dict:
	skip = {"ok", "role_key", "package", "may_run"}
	return {key: value for key, value in out.items() if key not in skip}


class TestPP2PackageReadinessApiP4009(IntegrationTestCase):
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

	def _seed_upstream_handoffs(
		self, journey_code: str, demand_code: str, budget_line_code: str
	) -> None:
		suffix = _journey_suffix(journey_code)
		cards = (
			(
				f"DEMAPP-{suffix}",
				"Demand Approval Certificate",
				"Demand Intake and Approval",
				"Procurement Planning",
				"Demand",
				demand_code,
			),
			(
				f"BUDCONF-{suffix}",
				"Budget Funding Confirmation",
				"Budget",
				"Demand Intake and Approval",
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

	def _seed_approved_review(self, package_code: str) -> str:
		code = f"PKGREV-{package_code}-001"
		if frappe.db.exists("Package Review Decision", code):
			return code
		doc = frappe.get_doc(
			{
				"doctype": "Package Review Decision",
				"review_decision_code": code,
				"package_code": package_code,
				"decision_type": "Approved",
				"decided_by": "Administrator",
				"decided_at": now_datetime(),
				"from_state": "In Review",
				"to_state": "Approved",
				"decision_reason": "Approved for readiness test.",
			}
		)
		doc.insert(ignore_permissions=True)
		self._cleanup.append(("Package Review Decision", code))
		return code

	def _complete_readiness_setup(self, package_code: str) -> str:
		method_out = record_package_method_for_api(
			package_code, _works_payload(), "Administrator"
		)
		self.assertTrue(method_out.get("ok"), method_out)
		if method_out.get("method_decision_code"):
			self._cleanup.append(("Package Method Decision", method_out["method_decision_code"]))

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
		self._seed_approved_review(package_code)
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
		return package_code

	def _full_readiness_setup(self) -> str:
		return self._complete_readiness_setup(self._ensure_works_package())

	def test_001_draft_read_not_run(self):
		"""SEED-TEST-P4-009-001: Draft package readiness is Not Run with may_run allowed."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		out = get_package_readiness_context(package_code, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("readiness_status"), READINESS_NOT_RUN)
		self.assertIsNone(out.get("current_result"))
		self.assertTrue((out.get("may_run") or {}).get("allowed"))

	def test_002_run_passes_be_006(self):
		"""SEED-TEST-P4-009-002: Run via API passes BE-006 after full setup."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._full_readiness_setup()
		frappe.set_user("Administrator")
		out = run_pp_package_readiness_checks(package_code=package_code)
		self.assertTrue(out.get("ok"), out)
		readiness_code = out.get("readiness_code")
		self.assertTrue(readiness_code)
		self._cleanup.append(("Package Readiness Result", readiness_code))

		self.assertEqual(out.get("result_status"), READINESS_PASSED)
		self.assertEqual(out.get("blocking_failure_count"), 0)
		self.assertFalse(out.get("stale"))
		self.assertEqual(len(out.get("checks") or []), 15)

	def test_003_read_after_run_populated(self):
		"""SEED-TEST-P4-009-003: Read after run exposes current_result and Passed status."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._full_readiness_setup()
		run_out = run_package_readiness_for_api(package_code, "Administrator")
		self.assertTrue(run_out.get("ok"), run_out)
		if run_out.get("readiness_code"):
			self._cleanup.append(("Package Readiness Result", run_out["readiness_code"]))

		read_out = get_pp_package_readiness(package_code=package_code)
		self.assertTrue(read_out.get("ok"), read_out)
		self.assertEqual(read_out.get("readiness_status"), READINESS_PASSED)
		current = read_out.get("current_result") or {}
		self.assertTrue(current.get("readiness_code"))
		self.assertEqual(len(current.get("checks") or []), 15)

	def test_004_second_run_recalled(self):
		"""SEED-TEST-P4-009-004: Second run returns action=recalled."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._full_readiness_setup()
		first = run_pp_package_readiness_checks(package_code=package_code)
		self.assertTrue(first.get("ok"), first)
		if first.get("readiness_code"):
			self._cleanup.append(("Package Readiness Result", first["readiness_code"]))

		second = run_pp_package_readiness_checks(package_code=package_code)
		self.assertTrue(second.get("ok"), second)
		self.assertEqual(second.get("action"), "recalled")
		self.assertEqual(second.get("readiness_code"), first.get("readiness_code"))

	def test_005_api_delegates_to_service(self):
		"""SEED-TEST-P4-009-005: Whitelisted API delegates to readiness service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		frappe.set_user("Administrator")
		api_read = get_pp_package_readiness(package_code=package_code)
		svc_read = get_package_readiness_context(package_code, "Administrator")
		self.assertTrue(api_read.get("ok"), api_read)
		self.assertTrue(svc_read.get("ok"), svc_read)
		self.assertEqual(_readiness_core(api_read), _readiness_core(svc_read))

		self._complete_readiness_setup(package_code)
		api_run = run_pp_package_readiness_checks(package_code=package_code)
		svc_run = run_package_readiness_for_api(package_code, "Administrator")
		self.assertTrue(api_run.get("ok"), api_run)
		self.assertTrue(svc_run.get("ok"), svc_run)
		self.assertEqual(api_run.get("readiness_code"), svc_run.get("readiness_code"))
		if api_run.get("readiness_code"):
			self._cleanup.append(("Package Readiness Result", api_run["readiness_code"]))

	def test_006_guest_and_officer_denied_on_read(self):
		"""SEED-TEST-P4-009-006: Guest and Procurement Officer receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_package_readiness(package_code=PKG_CODE)
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		officer_email = f"officer.readiness.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Readiness",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._cleanup.append(("User", officer_email))

		frappe.set_user(officer_email)
		officer_out = get_pp_package_readiness(package_code=PKG_CODE)
		self.assertFalse(officer_out.get("ok"))
		self.assertEqual(officer_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_007_officer_denied_on_run(self):
		"""SEED-TEST-P4-009-007: Procurement Officer cannot run readiness checks."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		officer_email = f"officer.run.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Run",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._cleanup.append(("User", officer_email))

		frappe.set_user(officer_email)
		out = run_pp_package_readiness_checks(package_code=package_code)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			("PP_ACCESS_DENIED", PlanningPermission.NOT_PERMITTED),
		)

	def test_008_locked_after_release_blocked(self):
		"""SEED-TEST-P4-009-008: locked_after_release blocks run with LOCKED_AFTER_RELEASE."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._full_readiness_setup()
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"locked_after_release",
			1,
			update_modified=False,
		)
		frappe.db.commit()

		frappe.set_user("Administrator")
		out = run_pp_package_readiness_checks(package_code=package_code)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackageReadiness.LOCKED_AFTER_RELEASE)

	def test_009_matches_workspace_readiness_tab(self):
		"""SEED-TEST-P4-009-009: Dedicated readiness API matches workspace tabs.readiness."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._full_readiness_setup()
		run_out = run_package_readiness_for_api(package_code, "Administrator")
		self.assertTrue(run_out.get("ok"), run_out)
		if run_out.get("readiness_code"):
			self._cleanup.append(("Package Readiness Result", run_out["readiness_code"]))

		readiness_out = get_package_readiness_context(package_code, "Administrator")
		workspace_out = get_package_workspace_context(package_code, "Administrator")
		self.assertTrue(readiness_out.get("ok"), readiness_out)
		self.assertTrue(workspace_out.get("ok"), workspace_out)
		self.assertEqual(
			_readiness_core(readiness_out),
			(workspace_out.get("tabs") or {}).get("readiness"),
		)
