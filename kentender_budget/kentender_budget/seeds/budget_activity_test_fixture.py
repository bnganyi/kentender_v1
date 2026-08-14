# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Isolated Budget activity fixture — not RSV-MOH-0001 / not canonical demo."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_budget.seeds.kentender_mvp_v1_portfolio import (
	TEST_ACTIVITY_NS,
	_seed_line_activity,
	_wall_clock_stale_as_at,
	upsert_kentender_mvp_v1_portfolio,
)
from kentender_budget.services.budget_line_contracts import format_kes_full

TEST_RSV_CODE = "RSV-MOH-TEST-ACT-0001"
TEST_COM_CODE = "COM-MOH-TEST-ACT-0001"
TEST_EXP_CODE = "EXP-MOH-TEST-ACT-0001"
TEST_DEMAND_CODE = "DMD-MOH-TEST-ACT-0001"
TEST_DEMAND_TITLE = "Budget activity test reservation"
TEST_CONTRACT_CODE = "CTR-MOH-TEST-ACT-0001"
TEST_PLAN_ITEM_CODE = "PPI-MOH-TEST-ACT-0001"
TEST_TENDER_CODE = "TND-MOH-TEST-ACT-0001"


def upsert_budget_activity_test_fixture() -> dict[str, Any]:
	"""Reservation coverage for Budget tests — never uses RSV-MOH-0001."""
	frappe.only_for(("System Manager", "Administrator"))
	portfolio = upsert_kentender_mvp_v1_portfolio()
	budget_name = frappe.db.get_value(
		"Budget", {"generated_reference": "MOH-BUD-2027-2028"}, "name"
	)
	line_name = frappe.db.get_value(
		"Budget Line", {"generated_reference": "MOH-BL-DHI-2027"}, "name"
	)
	if not budget_name or not line_name:
		raise frappe.ValidationError("Budget activity test fixture requires MOH-BUD-2027-2028")

	_seed_line_activity(
		budget_name,
		line_name,
		{
			"fixture_namespace": TEST_ACTIVITY_NS,
			"reservation": {
				"generated_reference": TEST_RSV_CODE,
				"demand_code": TEST_DEMAND_CODE,
				"demand_title": TEST_DEMAND_TITLE,
				"original_amount": 455_000_000,
				"remaining_reserved": 145_000_000,
				"status": "Partially converted",
				"event_date": "2027-09-12",
				"plan_item_code": TEST_PLAN_ITEM_CODE,
				"current_downstream_reference": TEST_TENDER_CODE,
				"idempotency_key": f"{TEST_ACTIVITY_NS}:{TEST_RSV_CODE}",
			},
			"commitment": {
				"generated_reference": TEST_COM_CODE,
				"contract_code": TEST_CONTRACT_CODE,
				"contract_title": "Budget activity test contract",
				"original_amount": 310_000_000,
				"current_amount": 310_000_000,
				"actual_expenditure": 180_000_000,
				"status": "Active",
				"event_date": "2027-10-28",
			},
			"expenditure": {
				"generated_reference": TEST_EXP_CODE,
				"source_system": "Finance system",
				"source_reference": "FIN-SNAP-MOH-TEST-ACT",
				"contract_code": TEST_CONTRACT_CODE,
				"amount": 180_000_000,
				"reconciliation_status": "Stale",
				"source_as_at_offset_days": -3,
			},
		},
	)
	frappe.db.set_value(
		"Budget Line",
		line_name,
		{
			"amount_reserved": 145_000_000,
			"amount_committed": 310_000_000,
			"amount_actual": 180_000_000,
			"actual_as_at": _wall_clock_stale_as_at(),
		},
		update_modified=False,
	)
	frappe.db.set_value(
		"Budget",
		budget_name,
		{"attention_note": "Actual expenditure is stale on 1 line"},
		update_modified=False,
	)
	_seed_test_activity_audit(budget_name)
	return {
		"ok": True,
		"portfolio": portfolio,
		"reservation": TEST_RSV_CODE,
		"commitment": TEST_COM_CODE,
		"expenditure": TEST_EXP_CODE,
		"line_reserved": flt(145_000_000),
	}


def _seed_test_activity_audit(budget_name: str) -> None:
	if not frappe.db.exists("DocType", "Budget Audit Event"):
		return
	from kentender_budget.services.budget_audit_contracts import record_event

	events = (
		{
			"event_type": "Expenditure snapshot recorded",
			"event_at": "2027-11-05 08:00:00",
			"actor": "Finance system",
			"actor_kind": "integration",
			"record_code": TEST_EXP_CODE,
			"record_doctype": "Expenditure Snapshot",
			"change_summary": f"Actual: {format_kes_full(180_000_000)} (Stale)",
			"source_reference": "FIN-SNAP-MOH-TEST-ACT",
		},
		{
			"event_type": "Contract commitment recorded",
			"event_at": "2027-10-28 10:00:00",
			"actor": "System",
			"actor_kind": "system",
			"record_code": TEST_COM_CODE,
			"record_doctype": "Procurement Commitment",
			"change_summary": f"Commitment: {format_kes_full(310_000_000)}",
			"source_reference": TEST_CONTRACT_CODE,
		},
		{
			"event_type": "Reservation partially converted",
			"event_at": "2027-10-28 09:55:00",
			"actor": "System",
			"actor_kind": "system",
			"record_code": TEST_RSV_CODE,
			"record_doctype": "Funding Reservation",
			"change_summary": f"Remaining reserved: {format_kes_full(145_000_000)}",
			"source_reference": TEST_TENDER_CODE,
		},
		{
			"event_type": "Funding reserved",
			"event_at": "2027-09-12 14:30:00",
			"actor": "System",
			"actor_kind": "system",
			"record_code": TEST_RSV_CODE,
			"record_doctype": "Funding Reservation",
			"change_summary": f"Reserved: {format_kes_full(455_000_000)}",
			"source_reference": TEST_DEMAND_CODE,
		},
	)
	for ev in events:
		record_event(
			budget=budget_name,
			event_type=ev["event_type"],
			event_at=ev["event_at"],
			actor=ev["actor"],
			actor_kind=ev["actor_kind"],
			record_code=ev["record_code"],
			record_doctype=ev.get("record_doctype") or "",
			change_summary=ev.get("change_summary") or "",
			source_reference=ev.get("source_reference") or "",
			fixture_namespace=TEST_ACTIVITY_NS,
		)
