# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-008 — Package method & category service and API."""

from __future__ import annotations

import json

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.package_method import (
	get_pp_package_method,
	record_pp_package_method_decision,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_IN_REVIEW, PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	FISCAL_YEAR,
	INCLUSION_CODE,
	PKG_CODE,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PLAN_CODE,
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.package_method import (
	get_package_method_context,
	record_package_method_for_api,
)
from kentender_procurement.procurement_planning.services.package_workspace import (
	get_package_workspace_context,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageMethodDecision,
	PlanningPermission,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_REVIEWER_USER = "planning.reviewer@moh.test"


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


def _method_core(out: dict) -> dict:
	skip = {"ok", "role_key", "package", "may_edit"}
	return {key: value for key, value in out.items() if key not in skip}


class TestPP2PackageMethodApiP4008(IntegrationTestCase):
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

	def test_001_draft_read_uses_package_source(self):
		"""SEED-TEST-P4-008-001: Draft package read falls back to package fields."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		out = get_package_method_context(package_code, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("source"), "package")
		self.assertIsNone(out.get("method_decision_code"))
		self.assertTrue((out.get("may_edit") or {}).get("allowed"))

	def test_002_write_works_method_be_005(self):
		"""SEED-TEST-P4-008-002: API records WORKS / Open Tender method (BE-005)."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		frappe.set_user("Administrator")
		out = record_pp_package_method_decision(
			package_code=package_code,
			payload=json.dumps(_works_payload()),
		)
		self.assertTrue(out.get("ok"), out)
		self.assertIn(out.get("action"), ("created", "superseded", "existing"))
		decision_code = out.get("method_decision_code")
		assert decision_code
		self._cleanup.append(("Package Method Decision", decision_code))

		decision = (out.get("method_decision") or {})
		self.assertEqual(decision.get("procurement_category"), PKG_PROCUREMENT_CATEGORY)
		self.assertEqual(decision.get("procurement_method"), "Open Tender")
		self.assertEqual(decision.get("required_std_type"), PKG_REQUIRED_STD_TYPE)
		self.assertFalse(decision.get("override_flag"))
		self.assertTrue(str(decision_code).startswith("METHDEC-"))

	def test_003_read_after_write_uses_method_decision(self):
		"""SEED-TEST-P4-008-003: Read after write exposes method_decision source."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		write_out = record_package_method_for_api(package_code, _works_payload(), "Administrator")
		self.assertTrue(write_out.get("ok"), write_out)
		if write_out.get("method_decision_code"):
			self._cleanup.append(("Package Method Decision", write_out["method_decision_code"]))

		read_out = get_package_method_context(package_code, "Administrator")
		self.assertTrue(read_out.get("ok"), read_out)
		self.assertEqual(read_out.get("source"), "method_decision")
		self.assertEqual(read_out.get("procurement_category"), PKG_PROCUREMENT_CATEGORY)
		self.assertEqual(read_out.get("procurement_method"), "Open Tender")
		self.assertEqual(read_out.get("required_std_type"), PKG_REQUIRED_STD_TYPE)

	def test_004_idempotent_rewrite_returns_existing(self):
		"""SEED-TEST-P4-008-004: Same payload rewrite is idempotent."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		payload = _works_payload()
		first = record_package_method_for_api(package_code, payload, "Administrator")
		self.assertTrue(first.get("ok"), first)
		if first.get("method_decision_code"):
			self._cleanup.append(("Package Method Decision", first["method_decision_code"]))

		second = record_pp_package_method_decision(
			package_code=package_code,
			payload=json.dumps(payload),
		)
		self.assertTrue(second.get("ok"), second)
		self.assertEqual(second.get("action"), "existing")
		self.assertEqual(second.get("method_decision_code"), first.get("method_decision_code"))

	def test_005_api_delegates_to_service(self):
		"""SEED-TEST-P4-008-005: Whitelisted API delegates to method service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		frappe.set_user("Administrator")
		api_read = get_pp_package_method(package_code=package_code)
		svc_read = get_package_method_context(package_code, "Administrator")
		self.assertTrue(api_read.get("ok"), api_read)
		self.assertTrue(svc_read.get("ok"), svc_read)
		self.assertEqual(_method_core(api_read), _method_core(svc_read))

		api_write = record_pp_package_method_decision(
			package_code=package_code,
			payload=json.dumps(_works_payload()),
		)
		svc_write = record_package_method_for_api(package_code, _works_payload(), "Administrator")
		self.assertTrue(api_write.get("ok"), api_write)
		self.assertTrue(svc_write.get("ok"), svc_write)
		self.assertEqual(api_write.get("method_decision_code"), svc_write.get("method_decision_code"))
		if api_write.get("method_decision_code"):
			self._cleanup.append(("Package Method Decision", api_write["method_decision_code"]))

	def test_006_guest_and_officer_denied_on_read(self):
		"""SEED-TEST-P4-008-006: Guest and Procurement Officer receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_package_method(package_code=PKG_CODE)
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		officer_email = f"officer.method.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Method",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._cleanup.append(("User", officer_email))

		frappe.set_user(officer_email)
		officer_out = get_pp_package_method(package_code=PKG_CODE)
		self.assertFalse(officer_out.get("ok"))
		self.assertEqual(officer_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_007_reviewer_denied_on_write(self):
		"""SEED-TEST-P4-008-007: Planning Reviewer cannot record method decisions."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		if not frappe.db.exists("User", _REVIEWER_USER):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": _REVIEWER_USER,
					"first_name": "Planning",
					"last_name": "Reviewer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Planning Reviewer")
			self._cleanup.append(("User", _REVIEWER_USER))

		frappe.set_user(_REVIEWER_USER)
		out = record_pp_package_method_decision(
			package_code=package_code,
			payload=json.dumps(_works_payload()),
		)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			("PP_ACCESS_DENIED", PlanningPermission.NOT_PERMITTED),
		)

	def test_008_in_review_write_blocked(self):
		"""SEED-TEST-P4-008-008: In Review package write is blocked by state guard."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"status",
			PKG_IN_REVIEW,
			update_modified=False,
		)
		frappe.db.commit()

		frappe.set_user("Administrator")
		out = record_pp_package_method_decision(
			package_code=package_code,
			payload=json.dumps(_works_payload()),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackageMethodDecision.LOCKED_AFTER_RELEASE)

	def test_009_matches_workspace_method_tab(self):
		"""SEED-TEST-P4-008-009: Dedicated method API matches workspace tabs.method."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		write_out = record_package_method_for_api(package_code, _works_payload(), "Administrator")
		self.assertTrue(write_out.get("ok"), write_out)
		if write_out.get("method_decision_code"):
			self._cleanup.append(("Package Method Decision", write_out["method_decision_code"]))

		method_out = get_package_method_context(package_code, "Administrator")
		workspace_out = get_package_workspace_context(package_code, "Administrator")
		self.assertTrue(method_out.get("ok"), method_out)
		self.assertTrue(workspace_out.get("ok"), workspace_out)
		self.assertEqual(
			_method_core(method_out),
			(workspace_out.get("tabs") or {}).get("method"),
		)
