# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-001 — get_approved_demands_awaiting_planning queue service and API (PP2-SMOKE-BE-002)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, getdate

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.procurement_planning.api.approved_demands import (
	get_pp_approved_demands_awaiting_planning,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
)
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import DEMAND_TITLE
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.prep import (
	ensure_works_demand_queue_ready,
)
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


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


def _find_row(rows: list[dict], demand_code: str) -> dict | None:
	code = (demand_code or "").strip()
	for row in rows or []:
		demand = row.get("demand") or {}
		if (demand.get("code") or "") == code:
			return row
	return None


class TestPP2ApprovedDemandQueueP4001(IntegrationTestCase):
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
		self._cleanup = []
		ensure_works_demand_queue_ready()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		ensure_works_demand_queue_ready()
		for doctype, name in reversed(getattr(self, "_cleanup", [])):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		self._cleanup = []
		frappe.db.commit()

	def _track(self, doctype: str, name: str) -> None:
		if not hasattr(self, "_cleanup"):
			self._cleanup = []
		self._cleanup.append((doctype, name))

	def _seed_budget_line(self) -> tuple[str | None, str | None, str | None]:
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name")
		if not bl_name:
			bl_name = frappe.db.get_value(
				"Budget Line",
				{"is_active": 1},
				"name",
				order_by="modified desc",
			)
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			return None, None, None
		data = ctx.get("data") or {}
		ent = data.get("procuring_entity")
		dept = ensure_department(f"Dept Queue {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_demand(
		self,
		*,
		demand_id: str,
		status: str = "Approved",
		budget_line: str | None = None,
		planning_status: str = "Not Planned",
	) -> str:
		bl_name, ent, dept = self._seed_budget_line()
		if not bl_name or not ent:
			raise RuntimeError("Budget line unavailable for queue test fixture")
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"demand_id": demand_id,
				"title": f"Queue probe {demand_id}",
				"procuring_entity": ent,
				"requesting_department": dept,
				"requested_by": "Administrator",
				"request_date": "2026-03-03",
				"required_by_date": "2026-12-31",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"requisition_type": "Works",
				"budget_line": budget_line or bl_name,
				"status": status,
				"planning_status": planning_status,
				"items": [
					{
						"item_description": "Probe works item",
						"category": "Works",
						"uom": "Lot",
						"quantity": 1,
						"estimated_unit_cost": 1000,
					}
				],
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._track("Demand", doc.name)
		frappe.db.commit()
		return demand_id

	def test_001_works_demand_appears_at_approved_demand_ready(self):
		"""SEED-TEST-P4-001-001 / PP2-SMOKE-BE-002: WORKS demand appears in Planning queue before inclusion."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_approved_demands_awaiting_planning({"search_text": DEMAND_CODE}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		row = _find_row(out.get("rows") or [], DEMAND_CODE)
		self.assertIsNotNone(row, out)
		assert row is not None

		demand = row["demand"]
		self.assertEqual(demand.get("code"), DEMAND_CODE)
		self.assertEqual(demand.get("name"), DEMAND_TITLE)
		self.assertTrue(row.get("department"))
		# Regression guard: `department` must be the human-readable
		# `Procuring Department.department_name`, never the Link field's
		# raw internal hash id (autoname="hash", e.g. "mkr2055b6p").
		demand_name = frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "name")
		dept_id = frappe.db.get_value("Demand", demand_name, "requesting_department")
		self.assertNotEqual(row.get("department"), dept_id)
		expected_dept_name = frappe.db.get_value("Procuring Department", dept_id, "department_name")
		self.assertEqual(row.get("department"), expected_dept_name)
		self.assertEqual(row.get("category"), "Works")
		self.assertEqual(flt(row.get("estimated_value")), flt(ESTIMATED_VALUE))
		self.assertEqual(row.get("currency"), "KES")
		self.assertEqual((row.get("budget_line") or {}).get("code"), BUDGET_LINE_CODE)
		self.assertEqual(row.get("planning_status"), "Ready for Planning")
		self.assertEqual(row.get("next_action"), "include_in_plan")
		self.assertIsNone(row.get("blocker_summary"))

		items = row.get("demand_items") or []
		self.assertGreaterEqual(len(items), 1)
		item_codes = {it.get("code") for it in items}
		self.assertIn(DEMAND_ITEM_CODE, item_codes)

		approval_date = row.get("approval_date")
		self.assertEqual(str(approval_date), "2026-03-05")

	def test_002_unapproved_demand_excluded(self):
		"""SEED-TEST-P4-001-002: Draft/unapproved demands do not appear in the queue."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_id = f"DEM-QUEUE-DRAFT-{frappe.generate_hash(length=6)}"
		self._mk_demand(demand_id=demand_id, status="Draft")

		out = get_approved_demands_awaiting_planning({}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(_find_row(out.get("rows") or [], demand_id))

	def test_003_approved_without_budget_excluded(self):
		"""SEED-TEST-P4-001-003: Approved demand without budget line is excluded."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_id = f"DEM-QUEUE-NOBUD-{frappe.generate_hash(length=6)}"
		self._mk_demand(demand_id=demand_id, status="Draft")
		demand_name = frappe.db.get_value("Demand", {"demand_id": demand_id}, "name")
		frappe.db.set_value(
			"Demand",
			demand_name,
			{"status": "Approved", "budget_line": None},
			update_modified=False,
		)
		frappe.db.commit()

		out = get_approved_demands_awaiting_planning({}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(_find_row(out.get("rows") or [], demand_id))

	def test_004_packaged_works_demand_excluded(self):
		"""SEED-TEST-P4-001-004: Active package line removes demand from queue."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(seed.get("ok"), seed)

		out = get_approved_demands_awaiting_planning({}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNone(_find_row(out.get("rows") or [], DEMAND_CODE))

	def test_005_whitelisted_api_delegates_for_administrator(self):
		"""SEED-TEST-P4-001-005: Whitelisted API returns queue rows for Administrator."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Administrator")
		out = get_pp_approved_demands_awaiting_planning(search_text=DEMAND_CODE)
		self.assertTrue(out.get("ok"), out)
		self.assertIsNotNone(_find_row(out.get("rows") or [], DEMAND_CODE))

	def _mk_approved_demand(self, *, demand_id: str) -> str:
		"""Create via the Draft->Approved doctype workflow is not exercised
		here (see test_003's same pattern) — insert as Draft, then bypass
		the status-transition guard with a direct db write, matching the
		existing fixtures' approach for "already approved" test rows."""
		self._mk_demand(demand_id=demand_id, status="Draft")
		demand_name = frappe.db.get_value("Demand", {"demand_id": demand_id}, "name")
		frappe.db.set_value("Demand", demand_name, "status", "Approved", update_modified=False)
		frappe.db.commit()
		return demand_name

	def test_007_department_filter_matches_department_name(self):
		"""W10 — the Needs Planning queue's `department` filter matches the
		human `Procuring Department.department_name`, never a raw hash id,
		exactly mirroring the other 5 workbench queues' behaviour."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_id = f"DEM-QUEUE-DEPT-{frappe.generate_hash(length=6)}"
		demand_name = self._mk_approved_demand(demand_id=demand_id)
		dept_id = frappe.db.get_value("Demand", demand_name, "requesting_department")
		dept_name = frappe.db.get_value("Procuring Department", dept_id, "department_name")
		self.assertTrue(dept_name)

		out = get_approved_demands_awaiting_planning({"department": dept_name}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertIsNotNone(_find_row(out.get("rows") or [], demand_id))

		miss = get_approved_demands_awaiting_planning(
			{"department": f"no-such-department-{frappe.generate_hash(length=6)}"}, "Administrator"
		)
		self.assertTrue(miss.get("ok"), miss)
		self.assertIsNone(_find_row(miss.get("rows") or [], demand_id))

	def test_008_value_range_filter(self):
		"""W10 — `value_range` buckets match `workbench_item_view_model`'s
		under_100m / 100m_500m / over_500m semantics."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_id = f"DEM-QUEUE-VALRNG-{frappe.generate_hash(length=6)}"
		demand_name = self._mk_approved_demand(demand_id=demand_id)
		frappe.db.set_value("Demand", demand_name, "total_amount", 600_000_000, update_modified=False)
		frappe.db.commit()

		hit = get_approved_demands_awaiting_planning({"value_range": "over_500m"}, "Administrator")
		self.assertTrue(hit.get("ok"), hit)
		self.assertIsNotNone(_find_row(hit.get("rows") or [], demand_id))

		miss = get_approved_demands_awaiting_planning({"value_range": "under_100m"}, "Administrator")
		self.assertTrue(miss.get("ok"), miss)
		self.assertIsNone(_find_row(miss.get("rows") or [], demand_id))

	def test_009_sort_by_value_desc(self):
		"""W10 — `sort=value_desc` orders queue rows by estimated value,
		highest first."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		low_id = f"DEM-QUEUE-SORTLOW-{frappe.generate_hash(length=6)}"
		high_id = f"DEM-QUEUE-SORTHIGH-{frappe.generate_hash(length=6)}"
		low_name = self._mk_approved_demand(demand_id=low_id)
		high_name = self._mk_approved_demand(demand_id=high_id)
		frappe.db.set_value("Demand", low_name, "total_amount", 1_000, update_modified=False)
		frappe.db.set_value("Demand", high_name, "total_amount", 900_000_000, update_modified=False)
		frappe.db.commit()

		out = get_approved_demands_awaiting_planning({"sort": "value_desc"}, "Administrator")
		self.assertTrue(out.get("ok"), out)
		codes = [(row.get("demand") or {}).get("code") for row in out.get("rows") or []]
		self.assertIn(high_id, codes)
		self.assertIn(low_id, codes)
		self.assertLess(codes.index(high_id), codes.index(low_id))

	def test_010_created_range_filter(self):
		"""W10 — `created_from`/`created_to` filter on the demand's finance
		approval date (`approval_date` on the formatted row)."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		demand_id = f"DEM-QUEUE-CREATED-{frappe.generate_hash(length=6)}"
		demand_name = self._mk_approved_demand(demand_id=demand_id)
		frappe.db.set_value("Demand", demand_name, "finance_approved_at", "2026-05-15", update_modified=False)
		frappe.db.commit()

		hit = get_approved_demands_awaiting_planning(
			{"created_from": "2026-05-01", "created_to": "2026-05-31"}, "Administrator"
		)
		self.assertTrue(hit.get("ok"), hit)
		self.assertIsNotNone(_find_row(hit.get("rows") or [], demand_id))

		miss = get_approved_demands_awaiting_planning(
			{"created_from": "2026-06-01", "created_to": "2026-06-30"}, "Administrator"
		)
		self.assertTrue(miss.get("ok"), miss)
		self.assertIsNone(_find_row(miss.get("rows") or [], demand_id))

	def test_006_guest_and_officer_denied(self):
		"""SEED-TEST-P4-001-006: Guest and Procurement Officer receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_approved_demands_awaiting_planning()
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		officer_email = f"officer.queue.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", officer_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer_email,
					"first_name": "Queue",
					"last_name": "Officer",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Procurement Officer")
			self._track("User", officer_email)

		frappe.set_user(officer_email)
		officer_out = get_pp_approved_demands_awaiting_planning()
		self.assertFalse(officer_out.get("ok"))
		self.assertEqual(officer_out.get("error_code"), "PP_ACCESS_DENIED")
