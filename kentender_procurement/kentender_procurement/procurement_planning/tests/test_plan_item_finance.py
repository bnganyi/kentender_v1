# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-007 / PLN-FR-040…049 — Plan Item Finance request, confirm, return."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cstr, flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import (
	ERR_INSUFFICIENT_FUNDING,
	FINANCE_AWAITING,
	FINANCE_CONFIRMED,
	FINANCE_NOT_REQUESTED,
	FINANCE_RETURNED,
	FINANCE_STALE,
)
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	confirm_plan_item_funding,
	get_plan_finance_task,
	request_plan_item_finance,
	return_plan_item_from_finance,
)
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	release_draft_finance_effects,
	remove_plan_item_from_plan,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	update_plan_item,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	attach_demand_funding,
	complete_plan_item_for_signoff,
	create_plan_as_planner,
	ensure_budget_officer_user,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	make_test_budget_line,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	ensure_admin_only,
	ensure_user_with_roles,
	PE_MOH,
)


class TestPlanItemFinance(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _token(self, version: str) -> str:
		return frappe.db.get_value("Procurement Plan Version", version, "concurrency_token") or ""

	def _ready_item(self, *, amount: float = 1_000_000, approved: float = 10_000_000):
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Finance confirm plan")
		d = make_approved_demand(title="Finance demand", item_amount=amount)
		funding = make_test_budget_line(approved_amount=approved)
		attach_demand_funding(
			demand=d["demand"],
			budget_line=funding["budget_line"],
			budget=funding["budget"],
			amount=amount,
		)
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		return {
			"planner": planner,
			"plan": plan,
			"demand": d,
			"funding": funding,
			"plan_item": added["plan_item"],
			"bo": ensure_budget_officer_user(),
		}

	def test_schema_finance_fields_exist(self) -> None:
		meta = frappe.get_meta("Procurement Plan Item Version")
		self.assertIsNotNone(meta.get_field("finance_status"))
		self.assertIsNotNone(meta.get_field("finance_snapshot_amount"))
		self.assertIsNotNone(meta.get_field("finance_reservation"))
		self.assertIsNotNone(frappe.get_meta("Plan Decision").get_field("plan_item"))

	def test_completeness_does_not_confirm_finance(self) -> None:
		ctx = self._ready_item()
		iv = frappe.db.get_value(
			"Procurement Plan Item", ctx["plan_item"], "draft_item_version"
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "finance_status")
			or FINANCE_NOT_REQUESTED,
			FINANCE_NOT_REQUESTED,
		)
		builder = get_plan_builder(plan=ctx["plan"]["plan"], user=ctx["planner"])
		row = next(r for r in builder["items"] if r["plan_item"] == ctx["plan_item"])
		self.assertEqual(row["finance_status_label"], FINANCE_NOT_REQUESTED)

	def test_request_finance_creates_awaiting_idempotently(self) -> None:
		ctx = self._ready_item()
		first = update_plan_item(
			plan_item=ctx["plan_item"], user=ctx["planner"], request_finance=True
		)
		self.assertTrue(first["ok"], first)
		self.assertTrue(first.get("complete"))
		self.assertEqual(first.get("finance_status"), FINANCE_AWAITING)
		second = request_plan_item_finance(plan_item=ctx["plan_item"], user=ctx["planner"])
		self.assertTrue(second["ok"])
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(second.get("finance_status"), FINANCE_AWAITING)
		builder = get_plan_builder(plan=ctx["plan"]["plan"], user=ctx["planner"])
		row = next(r for r in builder["items"] if r["plan_item"] == ctx["plan_item"])
		self.assertEqual(row["finance_status_label"], FINANCE_AWAITING)
		bo_builder = get_plan_builder(plan=ctx["plan"]["plan"], user=ctx["bo"])
		self.assertTrue(bo_builder.get("ok"), bo_builder)
		self.assertTrue(bo_builder.get("read_only"))
		bo_row = next(r for r in bo_builder["items"] if r["plan_item"] == ctx["plan_item"])
		self.assertTrue(bo_row.get("can_open_finance_task"))
		self.assertFalse(bo_builder.get("can_add_demand"))

	def test_confirm_reserves_and_retry_is_idempotent(self) -> None:
		ctx = self._ready_item()
		update_plan_item(plan_item=ctx["plan_item"], user=ctx["planner"], request_finance=True)
		line = ctx["funding"]["budget_line"]
		before = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		first = confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertTrue(first["ok"], first)
		self.assertEqual(first["finance_status"], FINANCE_CONFIRMED)
		self.assertTrue(first.get("reservation"))
		after = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		self.assertAlmostEqual(after - before, 1_000_000, places=2)
		second = confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertTrue(second["ok"], second)
		self.assertTrue(second.get("idempotent"))
		again = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		self.assertAlmostEqual(again, after, places=2)
		self.assertTrue(
			frappe.db.exists(
				"Plan Decision",
				{"plan_item": ctx["plan_item"], "decision_type": "Finance confirmation"},
			)
		)

	def test_confirm_reuses_existing_demand_reservation(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Reuse RSV plan")
		d = make_approved_demand(title="Reuse RSV demand", item_amount=1_000_000)
		funding = make_test_budget_line(approved_amount=10_000_000, reserved_amount=1_000_000)
		rsv = frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": f"RSV-PLN-{frappe.generate_hash(length=6).upper()}",
				"budget": funding["budget"],
				"budget_line": funding["budget_line"],
				"original_amount": 1_000_000,
				"remaining_reserved": 1_000_000,
				"status": "Reserved",
				"currency": "KES",
				"demand_code": d["demand_code"],
				"demand_title": "Reuse RSV demand",
				"event_date": "2027-08-15",
			}
		)
		rsv.insert(ignore_permissions=True)
		attach_demand_funding(
			demand=d["demand"],
			budget_line=funding["budget_line"],
			budget=funding["budget"],
			amount=1_000_000,
			reservation=rsv.name,
		)
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		complete_plan_item_for_signoff(plan_item=added["plan_item"], user=planner)
		update_plan_item(plan_item=added["plan_item"], user=planner, request_finance=True)
		bo = ensure_budget_officer_user()
		before = flt(frappe.db.get_value("Budget Line", funding["budget_line"], "amount_reserved"))
		result = confirm_plan_item_funding(plan_item=added["plan_item"], user=bo)
		self.assertTrue(result["ok"], result)
		after = flt(frappe.db.get_value("Budget Line", funding["budget_line"], "amount_reserved"))
		self.assertAlmostEqual(after, before, places=2)
		self.assertEqual(result.get("reservation"), rsv.generated_reference)

	def test_return_requires_reason(self) -> None:
		ctx = self._ready_item()
		update_plan_item(plan_item=ctx["plan_item"], user=ctx["planner"], request_finance=True)
		missing = return_plan_item_from_finance(plan_item=ctx["plan_item"], reason="", user=ctx["bo"])
		self.assertFalse(missing.get("ok"))
		self.assertIn("reason", missing.get("errors") or {})
		ok = return_plan_item_from_finance(
			plan_item=ctx["plan_item"],
			reason="Funding source must be corrected by the planner.",
			user=ctx["bo"],
		)
		self.assertTrue(ok["ok"], ok)
		self.assertEqual(ok["finance_status"], FINANCE_RETURNED)

	def test_planner_requester_admin_denied(self) -> None:
		ctx = self._ready_item()
		update_plan_item(plan_item=ctx["plan_item"], user=ctx["planner"], request_finance=True)
		with self.assertRaises(frappe.PermissionError):
			get_plan_finance_task(plan_item=ctx["plan_item"], user=ctx["planner"])
		with self.assertRaises(frappe.PermissionError):
			confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["planner"])
		requester = ensure_user_with_roles(
			"pln.c05.requester@test.local",
			roles=(),
			pe=PE_MOH,
			org_unit=None,
			include_descendants=0,
		)
		with self.assertRaises(frappe.PermissionError):
			get_plan_finance_task(plan_item=ctx["plan_item"], user=requester)
		admin = ensure_admin_only()
		from kentender_procurement.procurement_planning.services.planning_permissions import (
			assert_can_open_finance_task,
		)

		with self.assertRaises(frappe.PermissionError):
			assert_can_open_finance_task(admin)

	def test_shortfall_rejects_confirm(self) -> None:
		ctx = self._ready_item(amount=1_000_000, approved=100_000)
		update_plan_item(plan_item=ctx["plan_item"], user=ctx["planner"], request_finance=True)
		task = get_plan_finance_task(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertTrue(task["ok"], task)
		self.assertEqual(task["variant"], "shortfall")
		self.assertFalse(task["can_confirm"])
		self.assertGreater(flt(task["shortfall"]), 0)
		denied = confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertFalse(denied.get("ok"))
		self.assertEqual(denied.get("error_code"), ERR_INSUFFICIENT_FUNDING)
		line = ctx["funding"]["budget_line"]
		self.assertEqual(flt(frappe.db.get_value("Budget Line", line, "amount_reserved")), 0)

	def test_stale_after_amount_change(self) -> None:
		ctx = self._ready_item()
		update_plan_item(plan_item=ctx["plan_item"], user=ctx["planner"], request_finance=True)
		confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["bo"])
		iv_name = frappe.db.get_value(
			"Procurement Plan Item", ctx["plan_item"], "draft_item_version"
		)
		frappe.db.set_value(
			"Procurement Plan Item Version",
			iv_name,
			"confirmed_estimate",
			2_000_000,
			update_modified=True,
		)
		builder = get_plan_builder(plan=ctx["plan"]["plan"], user=ctx["planner"])
		row = next(r for r in builder["items"] if r["plan_item"] == ctx["plan_item"])
		self.assertEqual(row["finance_status_label"], FINANCE_STALE)

	def test_draft_remove_cancels_awaiting_task(self) -> None:
		ctx = self._ready_item()
		update_plan_item(plan_item=ctx["plan_item"], user=ctx["planner"], request_finance=True)
		released = release_draft_finance_effects(
			plan_item=ctx["plan_item"], version=ctx["plan"]["version"]
		)
		self.assertTrue(released["ok"])
		self.assertTrue(released.get("cancelled_task"))
		remove = remove_plan_item_from_plan(
			plan=ctx["plan"]["plan"],
			plan_item=ctx["plan_item"],
			reason="Added for finance cancel coverage",
			concurrency_token=self._token(ctx["plan"]["version"]),
			user=ctx["planner"],
		)
		self.assertTrue(remove["ok"], remove)

	def _scn_shortfall_item(self) -> dict:
		from kentender_procurement.procurement_planning.seeds import scn_pln_fund_short_001 as scn

		result = scn.run(reset_first=True, force=True)
		self.assertTrue(result.get("ok"), result)
		item = frappe.db.get_value(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}, "name"
		)
		return {"plan_item": item, "bo": C.USER_BUD_DUAL, "seed": result}

	def test_scn_shortfall_task_is_80_25_55(self) -> None:
		ctx = self._scn_shortfall_item()
		task = get_plan_finance_task(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertTrue(task["ok"], task)
		self.assertEqual(task["variant"], "shortfall")
		self.assertFalse(task["can_confirm"])
		self.assertEqual(task["amount_display"], "KES 80,000,000.00")
		self.assertEqual(task["available_before_display"], "KES 25,000,000.00")
		self.assertEqual(task["shortfall_display"], "KES 55,000,000.00")
		self.assertIn(C.BUD_ACTIVE, cstr(task.get("budget_funding_route") or ""))
		self.assertFalse(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)

	def test_scn_shortfall_confirm_rejects_without_reserving(self) -> None:
		ctx = self._scn_shortfall_item()
		line = frappe.db.get_value("Budget Line", {"generated_reference": C.BL_HWD_2027}, "name")
		before = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		denied = confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertFalse(denied.get("ok"))
		self.assertEqual(denied.get("error_code"), ERR_INSUFFICIENT_FUNDING)
		self.assertAlmostEqual(
			flt(frappe.db.get_value("Budget Line", line, "amount_reserved")),
			before,
			places=2,
		)
		self.assertFalse(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)

	def test_scn_shortfall_recovers_after_releasing_hold(self) -> None:
		from kentender_budget.api.dia_budget_control import release_reservation

		ctx = self._scn_shortfall_item()
		released = release_reservation(reservation_id=C.RSV_SHORT_CODE)
		self.assertTrue(released.get("ok"), released)
		task = get_plan_finance_task(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertTrue(task["ok"], task)
		self.assertEqual(task["variant"], "sufficient")
		self.assertTrue(task["can_confirm"])
		self.assertEqual(task["finance_status"], FINANCE_AWAITING)
		confirmed = confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertTrue(confirmed.get("ok"), confirmed)
		self.assertTrue(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)
		retry = confirm_plan_item_funding(plan_item=ctx["plan_item"], user=ctx["bo"])
		self.assertTrue(retry.get("ok"), retry)
		self.assertTrue(retry.get("idempotent"))
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}),
			1,
		)
