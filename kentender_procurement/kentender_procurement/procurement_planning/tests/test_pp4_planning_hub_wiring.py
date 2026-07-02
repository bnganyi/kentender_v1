# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP4 — Planning Hub wiring backend contract (HUB-BE-001..008).

Run:
  bench --site kentender.midas.com run-tests --app kentender_procurement \\
    --module kentender_procurement.procurement_planning.tests.test_pp4_planning_hub_wiring
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.planning_hub import (
	get_pp_planning_hub_plans_page,
	get_pp_planning_hub_shell_data,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_CLOSED, PLAN_DRAFT
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PLAN_APPROVER_EMAIL,
	PLAN_CODE,
	PLAN_CREATOR_EMAIL,
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.services.procurement_plans_view_model import (
	_plan_blockers_count,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP4PlanningHubWiring(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False
		self._original_status = frappe.db.get_value("Procurement Plan", PLAN_CODE, "status")

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		if self._original_status and frappe.db.exists("Procurement Plan", PLAN_CODE):
			frappe.db.set_value(
				"Procurement Plan",
				PLAN_CODE,
				"status",
				self._original_status,
				update_modified=False,
			)
			frappe.db.commit()

	def test_hub_be_001_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_planning_hub_shell_data()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_hub_be_002_shell_response_shape(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.set_user("Administrator")
		out = get_pp_planning_hub_shell_data()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		for key in ("active_plan", "hero_stats", "ledger_preview", "header_actions", "cta_actions"):
			self.assertIn(key, out, f"missing shell key: {key}")
		self.assertIsInstance(out.get("hero_stats"), list)
		self.assertEqual(len(out.get("hero_stats") or []), 5)
		ledger = out.get("ledger_preview") or {}
		self.assertIn("rows", ledger)
		self.assertIn("total", ledger)

	def test_hub_be_003_active_plan_hero_from_works_seed(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.db.set_value("Procurement Plan", PLAN_CODE, "status", PLAN_ACTIVE, update_modified=False)
		frappe.db.commit()
		frappe.set_user("Administrator")
		out = get_pp_planning_hub_shell_data()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		active = out.get("active_plan") or {}
		self.assertTrue(active.get("has_active_plan"))
		self.assertEqual(active.get("code"), PLAN_CODE)
		self.assertIn(PLAN_NAME, active.get("name") or active.get("plan_title") or "")

	def test_hub_be_004_no_active_plan_gate_shape(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.db.set_value("Procurement Plan", PLAN_CODE, "status", PLAN_DRAFT, update_modified=False)
		frappe.db.commit()
		frappe.set_user("Administrator")
		out = get_pp_planning_hub_shell_data()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		active = out.get("active_plan") or {}
		self.assertFalse(active.get("has_active_plan"))
		self.assertIn("primary_action", active)
		self.assertIn("secondary_action", active)
		self.assertEqual((active.get("primary_action") or {}).get("action"), "create_plan")

	def test_hub_be_005_ledger_rows_expose_code_and_name_not_pk(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.set_user("Administrator")
		out = get_pp_planning_hub_plans_page()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		rows = out.get("rows") or []
		self.assertTrue(rows, "expected at least one ledger row from seed")
		match = next((r for r in rows if r.get("code") == PLAN_CODE), None)
		self.assertIsNotNone(match)
		self.assertTrue(match.get("name"))
		self.assertEqual(match.get("code"), PLAN_CODE)
		self.assertTrue(str(match.get("code") or "").startswith("PLAN-"))
		self.assertNotIn(" ", str(match.get("code") or ""))

	def test_hub_be_006_blocked_kpi_matches_service(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.db.set_value("Procurement Plan", PLAN_CODE, "status", PLAN_ACTIVE, update_modified=False)
		frappe.db.commit()
		frappe.set_user("Administrator")
		expected = _plan_blockers_count(PLAN_CODE, actor="Administrator")
		out = get_pp_planning_hub_shell_data()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		stats = {s.get("id"): s for s in (out.get("hero_stats") or [])}
		blocked = stats.get("blocked_items") or {}
		self.assertEqual(int(blocked.get("value") or 0), expected)

	def test_hub_be_007_close_plan_flag_authority_only_on_active(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.db.set_value("Procurement Plan", PLAN_CODE, "status", PLAN_ACTIVE, update_modified=False)
		frappe.db.commit()
		if not frappe.db.exists("User", PLAN_APPROVER_EMAIL):
			self.skipTest("Planning Authority user not seeded")
		if not frappe.db.exists("User", PLAN_CREATOR_EMAIL):
			self.skipTest("Procurement Planner user not seeded")
		frappe.set_user(PLAN_APPROVER_EMAIL)
		auth_out = get_pp_planning_hub_shell_data()
		self.assertTrue(auth_out.get("ok"))
		self.assertTrue((auth_out.get("header_actions") or {}).get("show_close_plan"))
		frappe.set_user(PLAN_CREATOR_EMAIL)
		planner_out = get_pp_planning_hub_shell_data()
		self.assertTrue(planner_out.get("ok"))
		self.assertFalse((planner_out.get("header_actions") or {}).get("show_close_plan"))

	def test_hub_be_008_closed_plan_row_action_archive(self) -> None:
		if self._skip:
			self.skipTest("Procurement Plan not installed")
		if not frappe.db.exists("Procurement Plan", PLAN_CODE):
			self.skipTest(f"{PLAN_CODE} not seeded")
		frappe.db.set_value("Procurement Plan", PLAN_CODE, "status", PLAN_CLOSED, update_modified=False)
		frappe.db.commit()
		frappe.set_user("Administrator")
		out = get_pp_planning_hub_plans_page()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		match = next((r for r in (out.get("rows") or []) if r.get("code") == PLAN_CODE), None)
		self.assertIsNotNone(match)
		self.assertEqual(match.get("row_action"), "archive")
