# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-010 — Package review read/write service and API."""

from __future__ import annotations

import json

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
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
from kentender_procurement.procurement_planning.api.package_review import (
	get_pp_package_review,
	record_pp_package_review_decision,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_IN_REVIEW,
	PKG_RETURNED,
	PLAN_ACTIVE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
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
from kentender_procurement.procurement_planning.services.package_review_api import (
	get_package_review_context,
	record_package_review_for_api,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.package_workspace import (
	get_package_workspace_context,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReviewDecision,
	PlanningPermission,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_REVIEWER_USER = "planning.reviewer@moh.test"
_DECISION_SUBMITTED = "Submitted for Review"


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


def _review_core(out: dict) -> dict:
	skip = {"ok", "role_key", "package", "may_approve", "may_return", "package_status"}
	return {key: value for key, value in out.items() if key not in skip}


class TestPP2PackageReviewApiP4010(IntegrationTestCase):
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

	def _ensure_planner_user(self) -> str:
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

	def _audit_count(self, package_code: str, event_type: str) -> int:
		return frappe.db.count(
			"Planning Audit Event",
			{"object_code": package_code, "event_type": event_type},
		)

	def test_001_draft_read_no_review(self):
		"""SEED-TEST-P4-010-001: Draft package has no review and cannot approve/return."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		out = get_package_review_context(package_code, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(out.get("latest_review"))
		self.assertFalse((out.get("may_approve") or {}).get("allowed"))
		self.assertFalse((out.get("may_return") or {}).get("allowed"))

	def test_002_in_review_read_after_submit(self):
		"""SEED-TEST-P4-010-002: After submit, read shows Submitted decision and may_* allowed."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		out = get_pp_package_review(package_code=package_code)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("package_status"), PKG_IN_REVIEW)
		latest = out.get("latest_review") or {}
		self.assertEqual(latest.get("decision_type"), _DECISION_SUBMITTED)
		self.assertTrue((out.get("may_approve") or {}).get("allowed"))
		self.assertTrue((out.get("may_return") or {}).get("allowed"))

	def test_003_approve_via_api_be_007(self):
		"""SEED-TEST-P4-010-003: Approve via API completes BE-007 In Review → Approved."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		out = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps({"decision": "Approved"}),
		)
		self.assertTrue(out.get("ok"), out)
		review_code = out.get("review_decision_code")
		self.assertTrue(review_code)
		self._cleanup.append(("Package Review Decision", review_code))

		self.assertEqual(out.get("from_state"), PKG_IN_REVIEW)
		self.assertEqual(out.get("to_state"), PKG_APPROVED)
		self.assertEqual(out.get("status"), PKG_APPROVED)
		self.assertEqual(frappe.db.get_value("Procurement Package", package_code, "status"), PKG_APPROVED)
		self.assertEqual(self._audit_count(package_code, "Package Approved"), 1)

	def test_004_return_with_reason_and_correction(self):
		"""SEED-TEST-P4-010-004: Return via API persists reason and required correction."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		reviewer = self._ensure_reviewer_user()
		reason = "Missing budget justification"
		correction = "Attach signed budget memo"
		frappe.set_user(reviewer)
		out = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps(
				{
					"decision": "Returned for Correction",
					"reason": reason,
					"required_correction": correction,
				}
			),
		)
		self.assertTrue(out.get("ok"), out)
		review_code = out.get("review_decision_code")
		self.assertTrue(review_code)
		self._cleanup.append(("Package Review Decision", review_code))

		self.assertEqual(out.get("to_state"), PKG_RETURNED)
		row = frappe.get_doc("Package Review Decision", review_code)
		self.assertEqual(row.decision_reason, reason)
		self.assertEqual(row.required_correction, correction)
		self.assertEqual(frappe.db.get_value("Procurement Package", package_code, "status"), PKG_RETURNED)

	def test_005_return_missing_reason(self):
		"""SEED-TEST-P4-010-005: Return without reason is blocked."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		out = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps(
				{
					"decision": "Returned for Correction",
					"required_correction": "Fix scope",
				}
			),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackageReviewDecision.RETURN_REASON_REQUIRED)

	def test_006_return_missing_correction(self):
		"""SEED-TEST-P4-010-006: Return without required correction is blocked."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		out = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps(
				{
					"decision": "Returned for Correction",
					"reason": "Incomplete",
				}
			),
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackageReviewDecision.RETURN_CORRECTION_REQUIRED)

	def test_007_second_approve_recalled(self):
		"""SEED-TEST-P4-010-007: Second approve returns action=recalled."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		first = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps({"decision": "Approved"}),
		)
		self.assertTrue(first.get("ok"), first)
		review_code = first.get("review_decision_code")
		self.assertTrue(review_code)
		self._cleanup.append(("Package Review Decision", review_code))

		second = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps({"decision": "Approved"}),
		)
		self.assertTrue(second.get("ok"), second)
		self.assertEqual(second.get("action"), "recalled")
		self.assertEqual(second.get("review_decision_code"), review_code)

	def test_008_api_delegates_to_service(self):
		"""SEED-TEST-P4-010-008: Whitelisted API delegates to review service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._ensure_works_package()
		frappe.set_user("Administrator")
		api_read = get_pp_package_review(package_code=package_code)
		svc_read = get_package_review_context(package_code, "Administrator")
		self.assertTrue(api_read.get("ok"), api_read)
		self.assertTrue(svc_read.get("ok"), svc_read)
		self.assertEqual(_review_core(api_read), _review_core(svc_read))

		package_code = self._in_review_setup(package_code)
		reviewer = self._ensure_reviewer_user()
		frappe.set_user(reviewer)
		api_write = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps({"decision": "Approved"}),
		)
		svc_write = record_package_review_for_api(
			package_code, {"decision": "Approved"}, reviewer
		)
		self.assertTrue(api_write.get("ok"), api_write)
		self.assertTrue(svc_write.get("ok"), svc_write)
		self.assertEqual(api_write.get("review_decision_code"), svc_write.get("review_decision_code"))
		if api_write.get("review_decision_code"):
			self._cleanup.append(("Package Review Decision", api_write["review_decision_code"]))

	def test_009_guest_and_officer_denied_on_read(self):
		"""SEED-TEST-P4-010-009: Guest and Procurement Officer receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_package_review(package_code=PKG_CODE)
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		officer_email = f"officer.review.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Review",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._cleanup.append(("User", officer_email))

		frappe.set_user(officer_email)
		officer_out = get_pp_package_review(package_code=PKG_CODE)
		self.assertFalse(officer_out.get("ok"))
		self.assertEqual(officer_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_010_planner_denied_on_write(self):
		"""SEED-TEST-P4-010-010: Procurement Planner cannot record review decisions."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		planner = self._ensure_planner_user()
		frappe.set_user(planner)
		out = record_pp_package_review_decision(
			package_code=package_code,
			payload=json.dumps({"decision": "Approved"}),
		)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			("PP_ACCESS_DENIED", PlanningPermission.NOT_PERMITTED),
		)

	def test_011_matches_workspace_review_tab(self):
		"""SEED-TEST-P4-010-011: Dedicated review API latest_review matches workspace tabs.review."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = self._in_review_setup()
		review_out = get_package_review_context(package_code, "Administrator")
		workspace_out = get_package_workspace_context(package_code, "Administrator")
		self.assertTrue(review_out.get("ok"), review_out)
		self.assertTrue(workspace_out.get("ok"), workspace_out)
		self.assertEqual(
			review_out.get("latest_review"),
			(workspace_out.get("tabs") or {}).get("review"),
		)
