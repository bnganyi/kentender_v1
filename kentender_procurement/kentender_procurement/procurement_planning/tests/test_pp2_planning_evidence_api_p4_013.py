# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-013 — Planning Evidence timeline read API."""

from __future__ import annotations

import json
import re

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
from kentender_procurement.procurement_planning.api.package_workspace import (
	get_pp_package_workspace,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	create_pp_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.api.planning_evidence import (
	get_pp_planning_evidence_timeline,
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
	PKGREL_CODE,
	PLAN_CODE,
	PLAN_NAME,
	TENDER_CODE,
	master_planning_audit_events_for_checkpoint,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.package_workspace import (
	get_package_workspace_context,
)
from kentender_procurement.procurement_planning.services.planning_evidence_api import (
	get_planning_evidence_timeline,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_OFFICER_USER = "procurement.officer@moh.test"

_UUID_RE = re.compile(
	r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
	re.IGNORECASE,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


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


class TestPP2PlanningEvidenceApiP4013(IntegrationTestCase):
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
		return seed

	def test_001_draft_package_empty_timeline(self):
		"""SEED-TEST-P4-013-001: Draft-only package excludes unrelated journey audit events."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		package_code = _include_and_create_package()
		out = get_planning_evidence_timeline(package_code, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual((out.get("package") or {}).get("code"), package_code)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", package_code, "status"),
			PKG_DRAFT,
		)
		for row in out.get("events") or []:
			object_code = (row.get("object") or {}).get("code") or row.get("object_code") or ""
			evidence_code = (row.get("evidence") or {}).get("code") or row.get("evidence_ref") or ""
			self.assertNotEqual(object_code, PKG_CODE)
			self.assertNotEqual(evidence_code, PKGREL_CODE)
			self.assertTrue(
				object_code.startswith(package_code)
				or evidence_code.startswith(package_code)
				or object_code == DEMAND_CODE
				or evidence_code == INCLUSION_CODE
			)

	def test_002_consumed_works_smoke_labels_and_refs(self):
		"""SEED-TEST-P4-013-002: CONSUMED WORKS timeline includes smoke labels and evidence refs."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_pp_planning_evidence_timeline(package_code=PKG_CODE)
		self.assertTrue(out.get("ok"), out)
		events = out.get("events") or []
		self.assertGreater(len(events), 0)

		labels = {str(row.get("label") or "") for row in events}
		evidence_codes = {
			str((row.get("evidence") or {}).get("code") or row.get("evidence_ref") or "")
			for row in events
		}

		self.assertIn("Demand included in procurement plan", labels)
		self.assertIn("Package released to Tender Management", labels)
		self.assertIn("Tender Management consumed release", labels)
		self.assertIn(INCLUSION_CODE, evidence_codes)
		self.assertIn(PKGREL_CODE, evidence_codes)
		self.assertIn(TENDER_CODE, evidence_codes)

	def test_003_events_ordered_ascending(self):
		"""SEED-TEST-P4-013-003: Timeline matches master audit order for CONSUMED checkpoint."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_planning_evidence_timeline(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		events = out.get("events") or []
		expected = master_planning_audit_events_for_checkpoint("CONSUMED_BY_TENDER")
		master_codes = [row["event_code"] for row in expected]
		master_events = [
			row for row in events if (row.get("technical") or {}).get("is_master_seed")
		]
		self.assertEqual(len(master_events), len(expected))
		self.assertEqual([row.get("event_code") for row in master_events], master_codes)
		occurred = [row.get("occurred_at") for row in events]
		self.assertEqual(occurred, sorted(occurred))

	def test_004_ref_triplets_not_raw_ids(self):
		"""SEED-TEST-P4-013-004: object/evidence refs use business codes, not raw UUID primary keys."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_planning_evidence_timeline(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		for row in out.get("events") or []:
			for key in ("object", "evidence"):
				ref = row.get(key) or {}
				code = str(ref.get("code") or "").strip()
				self.assertTrue(code)
				self.assertFalse(_UUID_RE.match(code), f"{key}.code must not be a raw UUID: {code}")
				self.assertTrue(str(ref.get("name") or "").strip())

	def test_005_officer_allowed(self):
		"""SEED-TEST-P4-013-005: Procurement Officer can read planning evidence timeline."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		officer = self._ensure_officer_user()
		frappe.set_user(officer)
		out = get_pp_planning_evidence_timeline(package_code=PKG_CODE)
		self.assertTrue(out.get("ok"), out)
		self.assertGreater(len(out.get("events") or []), 0)

	def test_006_guest_and_supplier_denied(self):
		"""SEED-TEST-P4-013-006: Guest and Supplier receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_planning_evidence_timeline(package_code=PKG_CODE)
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		supplier_email = f"supplier.evidence.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", supplier_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": supplier_email,
					"first_name": "Evidence",
					"last_name": "Supplier",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Supplier")
			self._cleanup.append(("User", supplier_email))

		frappe.set_user(supplier_email)
		supplier_out = get_pp_planning_evidence_timeline(package_code=PKG_CODE)
		self.assertFalse(supplier_out.get("ok"))
		self.assertEqual(supplier_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_007_unknown_package_not_found(self):
		"""SEED-TEST-P4-013-007: Unknown package code returns NOT_FOUND."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_planning_evidence_timeline("PKG-DOES-NOT-EXIST", "Administrator")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_008_api_delegates_to_service(self):
		"""SEED-TEST-P4-013-008: Whitelisted API delegates to planning evidence service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		frappe.set_user("Administrator")
		api_out = get_pp_planning_evidence_timeline(package_code=PKG_CODE)
		svc_out = get_planning_evidence_timeline(PKG_CODE, "Administrator")
		self.assertTrue(api_out.get("ok"), api_out)
		self.assertTrue(svc_out.get("ok"), svc_out)
		self.assertEqual(api_out.get("total"), svc_out.get("total"))
		self.assertEqual(
			[row.get("event_code") for row in api_out.get("events") or []],
			[row.get("event_code") for row in svc_out.get("events") or []],
		)

	def test_009_workspace_recent_events_subset_of_timeline(self):
		"""SEED-TEST-P4-013-009: Workspace recent_events event_codes are subset of full timeline."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		frappe.set_user("Administrator")
		timeline = get_planning_evidence_timeline(PKG_CODE, "Administrator")
		workspace = get_package_workspace_context(PKG_CODE, "Administrator")
		self.assertTrue(timeline.get("ok"), timeline)
		self.assertTrue(workspace.get("ok"), workspace)

		full_codes = {row.get("event_code") for row in timeline.get("events") or []}
		recent = (workspace.get("tabs") or {}).get("evidence") or {}
		recent_codes = {row.get("event_code") for row in recent.get("recent_events") or []}
		self.assertTrue(recent_codes)
		self.assertTrue(recent_codes.issubset(full_codes))

		api_workspace = get_pp_package_workspace(package_code=PKG_CODE)
		self.assertTrue(api_workspace.get("ok"), api_workspace)
		api_recent = (api_workspace.get("tabs") or {}).get("evidence") or {}
		api_recent_codes = {row.get("event_code") for row in api_recent.get("recent_events") or []}
		self.assertTrue(api_recent_codes.issubset(full_codes))
