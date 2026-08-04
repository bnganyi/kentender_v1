# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""MOH_MVP_V1 portfolio seed — BUD-UI-01 Stitch / pack fixture rows."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

FIXTURE_NS = "MOH_MVP_V1"
PE_CODE = "PE-MOH"
PE_NAME = "Ministry of Health"

BUDGETS = (
	{
		"generated_reference": "MOH-BUD-0001",
		"title": "Ministry of Health Procurement Budget FY 2027/28",
		"fiscal_period": "2027/28",
		"start_date": "2027-07-01",
		"end_date": "2028-06-30",
		"status": "Active",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2027-01",
		"approval_date": "2027-06-15",
		"external_approved_total": 560_000_000,
		"attention_note": "Actual expenditure stale on 1 line",
		"readiness_issue_count": 0,
		"lines": (
			{
				"generated_reference": "MOH-BL-0001",
				"title": "Digital clinical systems infrastructure",
				"approved_amount": 480_000_000,
				"amount_reserved": 145_000_000,
				"amount_committed": 310_000_000,
				"organisational_owner": "Director, Digital Health",
				"order_index": 1,
			},
			{
				"generated_reference": "MOH-BL-0002",
				"title": "Digital health technical capability",
				"approved_amount": 80_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"organisational_owner": "Director, Digital Health",
				"order_index": 2,
			},
		),
	},
	{
		"generated_reference": "MOH-BUD-0002",
		"title": "Ministry of Health Procurement Budget FY 2028/29",
		"fiscal_period": "2028/29",
		"start_date": "2028-07-01",
		"end_date": "2029-06-30",
		"status": "Submitted",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2028-01",
		"approval_date": "2028-06-10",
		"external_approved_total": 600_000_000,
		"attention_note": "",
		"readiness_issue_count": 2,
		"lines": (
			{
				"generated_reference": "MOH-BL-0003",
				"title": "Digital clinical systems infrastructure",
				"approved_amount": 500_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"organisational_owner": "Director, Digital Health",
				"order_index": 1,
			},
			{
				"generated_reference": "MOH-BL-0004",
				"title": "Digital health technical capability",
				"approved_amount": 100_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"organisational_owner": "Director, Digital Health",
				"order_index": 2,
			},
		),
	},
	{
		"generated_reference": "MOH-BUD-0003",
		"title": "Ministry of Health Procurement Budget FY 2026/27",
		"fiscal_period": "2026/27",
		"start_date": "2026-07-01",
		"end_date": "2027-06-30",
		"status": "Closed",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2026-01",
		"approval_date": "2026-06-12",
		"external_approved_total": 520_000_000,
		"attention_note": "",
		"readiness_issue_count": 0,
		"lines": (
			{
				"generated_reference": "MOH-BL-0005",
				"title": "Prior-year digital health envelope",
				"approved_amount": 520_000_000,
				"amount_reserved": 0,
				"amount_committed": 520_000_000,
				"organisational_owner": "Director, Digital Health",
				"order_index": 1,
			},
		),
	},
)


def _upsert_budget(pe_name: str, spec: dict[str, Any]) -> str:
	existing = frappe.db.get_value(
		"Budget", {"generated_reference": spec["generated_reference"]}, "name"
	)
	payload = {
		"doctype": "Budget",
		"generated_reference": spec["generated_reference"],
		"title": spec["title"],
		"procuring_entity": pe_name,
		"fiscal_period": spec["fiscal_period"],
		"start_date": spec["start_date"],
		"end_date": spec["end_date"],
		"currency": "KES",
		"budget_owner": spec["budget_owner"],
		"registration_source": "Direct capture",
		"authoritative_reference": spec["authoritative_reference"],
		"approval_date": spec["approval_date"],
		"external_approved_total": spec["external_approved_total"],
		"status": spec["status"],
		"attention_note": spec.get("attention_note") or "",
		"readiness_issue_count": int(spec.get("readiness_issue_count") or 0),
		"fixture_namespace": FIXTURE_NS,
	}
	if existing:
		doc = frappe.get_doc("Budget", existing)
		doc.update(payload)
		doc.save(ignore_permissions=True)
		budget_name = doc.name
	else:
		doc = frappe.get_doc(payload)
		doc.insert(ignore_permissions=True)
		budget_name = doc.name

	# Replace fixture lines for this budget
	for line_name in frappe.get_all(
		"Budget Line",
		filters={"budget": budget_name, "fixture_namespace": FIXTURE_NS},
		pluck="name",
	):
		frappe.delete_doc("Budget Line", line_name, force=1, ignore_permissions=True)

	for line in spec.get("lines") or ():
		frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget": budget_name,
				"generated_reference": line["generated_reference"],
				"title": line["title"],
				"organisational_owner": line["organisational_owner"],
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"approved_amount": line["approved_amount"],
				"amount_reserved": line.get("amount_reserved") or 0,
				"amount_committed": line.get("amount_committed") or 0,
				"currency": "KES",
				"is_active": 1,
				"order_index": line.get("order_index") or 0,
				"fixture_namespace": FIXTURE_NS,
			}
		).insert(ignore_permissions=True)
	return budget_name


def upsert_moh_mvp_v1_portfolio() -> dict[str, Any]:
	"""Idempotent portfolio seed for BUD-UI-01."""
	frappe.only_for(("System Manager", "Administrator"))
	ensure_budget_roles()
	ensure_currency_kes()
	pe_name = ensure_procuring_entity(PE_CODE, PE_NAME)
	created: list[str] = []
	for spec in BUDGETS:
		created.append(_upsert_budget(pe_name, spec))
	frappe.db.commit()
	return {
		"ok": True,
		"fixture_namespace": FIXTURE_NS,
		"procuring_entity": pe_name,
		"budgets": created,
		"codes": [b["generated_reference"] for b in BUDGETS],
	}
