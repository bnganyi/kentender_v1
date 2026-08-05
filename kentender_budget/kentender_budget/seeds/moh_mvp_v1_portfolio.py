# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""MOH_MVP_V1 portfolio seed — BUD-UI-01 / Overview / Lines fixture rows."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, today

from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

FIXTURE_NS = "MOH_MVP_V1"
PE_CODE = "PE-MOH"
PE_NAME = "Ministry of Health"

# Pack §9.1 / Stitch Prompt 5 — immutable display snapshots (not live Strategy titles).
_PVC_TREATMENTS_BL0001 = (
	{
		"pvc_code": "PVO-EFT-01",
		"pvc_name": "Improve infrastructure efficiency",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": (
			"Efficiency considerations are included in infrastructure sizing, "
			"energy use and operating requirements."
		),
	},
	{
		"pvc_code": "PVO-ECO-01",
		"pvc_name": "Reduce whole-life infrastructure cost",
		"requirement_level": "Required",
		"treatment": "Dedicated allocation",
		"dedicated_amount": 40_000_000,
		"rationale": (
			"Dedicated to whole-life costing, energy-efficiency and lifecycle-optimisation activities."
		),
	},
	{
		"pvc_code": "PVO-RES-01",
		"pvc_name": "Improve system resilience",
		"requirement_level": "Recommended",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Resilience is included in redundancy, continuity and support activities.",
	},
	{
		"pvc_code": "PVO-SUS-02",
		"pvc_name": "Ensure responsible asset disposal",
		"requirement_level": "Required",
		"treatment": "No direct allocation required",
		"dedicated_amount": 0,
		"rationale": (
			"Disposal costs are included within the asset-replacement activities funded by this line."
		),
	},
)

_PVC_TREATMENTS_BL0002 = (
	{
		"pvc_code": "PVO-EFT-01",
		"pvc_name": "Improve infrastructure efficiency",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Training delivery uses the existing digital-learning platform.",
	},
	{
		"pvc_code": "PVO-ECO-01",
		"pvc_name": "Reduce whole-life infrastructure cost",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Training and certification costs are included in the line amount.",
	},
	{
		"pvc_code": "PVO-RES-01",
		"pvc_name": "Improve system resilience",
		"requirement_level": "Recommended",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Continuity capability is included in the training programme.",
	},
	{
		"pvc_code": "PVO-SUS-02",
		"pvc_name": "Ensure responsible asset disposal",
		"requirement_level": "Required",
		"treatment": "Not applicable",
		"dedicated_amount": 0,
		"rationale": "The line does not acquire or replace physical assets.",
		"reviewer_accepted": 1,
	},
)

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
		"attention_note": "Actual expenditure is stale on 1 line",
		"readiness_issue_count": 0,
		"strategy_pvc_treated": 4,
		"strategy_pvc_applicable": 4,
		"lines": (
			{
				"generated_reference": "MOH-BL-0001",
				"title": "Digital clinical systems infrastructure",
				"approved_amount": 480_000_000,
				"amount_reserved": 145_000_000,
				"amount_committed": 310_000_000,
				"amount_actual": 180_000_000,
				# Prompt 5: stale actuals (~3 days) — Unknown/Stale not fake zero.
				"actual_as_at_offset_days": -3,
				"classification": "Capital expenditure",
				"external_financial_line_reference": "HLTH-INF-2027-004",
				"organisational_owner": "Head, ICT Infrastructure",
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": "MOH-TGT-0001",
				"primary_target_name": "At least 99.9% annual availability by 30 June 2028",
				"supporting_targets": (
					{
						"target_code": "MOH-TGT-0002",
						"target_name": "Restore critical services within 4 hours",
						"reason": (
							"Infrastructure investment supports service restoration "
							"and continuity requirements."
						),
					},
				),
				"value_treatments": _PVC_TREATMENTS_BL0001,
				"order_index": 1,
				# Pack §9.3 downstream funding scenario (activity ledger).
				"funding_activity": {
					"reservation": {
						"generated_reference": "RSV-MOH-0001",
						"demand_code": "DMD-MOH-2027-014",
						"demand_title": "National digital health infrastructure upgrade",
						"original_amount": 455_000_000,
						"remaining_reserved": 145_000_000,
						"status": "Partially converted",
						"event_date": "2027-09-12",
						"current_downstream_reference": "TND-MOH-2027-008",
						"idempotency_key": "MOH_MVP_V1:RSV-MOH-0001",
					},
					"commitment": {
						"generated_reference": "COM-MOH-0001",
						"contract_code": "CTR-MOH-2027-005",
						"contract_title": "Digital health infrastructure implementation contract",
						"original_amount": 310_000_000,
						"current_amount": 310_000_000,
						"actual_expenditure": 180_000_000,
						"status": "Active",
						"event_date": "2027-10-28",
					},
					"expenditure": {
						"generated_reference": "EXP-MOH-0001",
						"source_system": "Finance system",
						"source_reference": "FIN-SNAP-MOH-2027-11",
						"contract_code": "CTR-MOH-2027-005",
						"amount": 180_000_000,
						# Pack §9.3: stale reconciliation (not fake zero).
						"reconciliation_status": "Stale",
						"source_as_at_offset_days": -3,
					},
				},
			},
			{
				"generated_reference": "MOH-BL-0002",
				"title": "Digital health technical capability",
				"approved_amount": 80_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"amount_actual": 0,
				"actual_as_at": None,
				"classification": "Services",
				"organisational_owner": "Director, Digital Health",
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": "MOH-TGT-0003",
				"primary_target_name": "Digital health technical capability target",
				"value_treatments": _PVC_TREATMENTS_BL0002,
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
				"classification": "Capital expenditure",
				"organisational_owner": "Director, Digital Health",
				"primary_target_code": "MOH-TGT-0001",
				"primary_target_name": "At least 99.9% annual availability by 30 June 2028",
				"order_index": 1,
			},
			{
				"generated_reference": "MOH-BL-0004",
				"title": "Digital health technical capability",
				"approved_amount": 100_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Services",
				"organisational_owner": "Director, Digital Health",
				"primary_target_code": "MOH-TGT-0003",
				"primary_target_name": "Digital health technical capability target",
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
				"classification": "Capital expenditure",
				"organisational_owner": "Director, Digital Health",
				"order_index": 1,
			},
		),
	},
)


def _resolve_target_snapshot(code: str, fallback_name: str) -> dict[str, str]:
	"""Prefer live Active Performance Target; fall back to pack snapshot fields."""
	row = frappe.db.get_value(
		"Performance Target",
		{"target_code": code, "status": "Active"},
		["name", "title", "plan_version"],
		as_dict=True,
	)
	if row:
		return {
			"id": row.name,
			"code": code,
			"name": row.title or fallback_name,
			"plan_version_id": row.plan_version or "",
			"snapshot_label": row.title or fallback_name,
		}
	return {
		"id": "",
		"code": code,
		"name": fallback_name,
		"plan_version_id": "",
		"snapshot_label": fallback_name,
	}


def _resolve_pvc_id(code: str) -> str:
	"""Best-effort link to Plan Value Commitment / Public Value Objective code."""
	name = frappe.db.get_value(
		"Public Value Objective",
		{"objective_code": code, "status": "Active"},
		"name",
	)
	if not name:
		name = frappe.db.get_value("Public Value Objective", {"objective_code": code}, "name")
	if not name:
		return ""
	pvc = frappe.db.get_value(
		"Plan Value Commitment",
		{"public_value_objective_version": name},
		"name",
	)
	return pvc or ""


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
		"strategy_pvc_treated": int(spec.get("strategy_pvc_treated") or 0),
		"strategy_pvc_applicable": int(spec.get("strategy_pvc_applicable") or 0),
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

	# Replace fixture activity then lines (FK-safe order).
	_clear_fixture_activity(budget_name)
	for line_name in frappe.get_all(
		"Budget Line",
		filters={"budget": budget_name, "fixture_namespace": FIXTURE_NS},
		pluck="name",
	):
		frappe.delete_doc("Budget Line", line_name, force=1, ignore_permissions=True)

	for line in spec.get("lines") or ():
		actual_as_at = line.get("actual_as_at")
		if "actual_as_at_offset_days" in line:
			actual_as_at = add_days(today(), int(line["actual_as_at_offset_days"]))

		primary = None
		if line.get("primary_target_code"):
			primary = _resolve_target_snapshot(
				line["primary_target_code"],
				line.get("primary_target_name") or line["primary_target_code"],
			)

		supporting = []
		for st in line.get("supporting_targets") or ():
			snap = _resolve_target_snapshot(st["target_code"], st.get("target_name") or st["target_code"])
			supporting.append(
				{
					"target_id": snap["id"],
					"target_code": snap["code"],
					"target_name": snap["name"],
					"plan_version_id": snap["plan_version_id"],
					"snapshot_label": snap["snapshot_label"],
					"reason": st.get("reason") or "",
				}
			)

		treatments = []
		for tr in line.get("value_treatments") or ():
			treatments.append(
				{
					"pvc_id": _resolve_pvc_id(tr["pvc_code"]),
					"pvc_code": tr["pvc_code"],
					"pvc_name": tr["pvc_name"],
					"requirement_level": tr.get("requirement_level") or "",
					"treatment": tr["treatment"],
					"dedicated_amount": tr.get("dedicated_amount") or 0,
					"rationale": tr.get("rationale") or "",
					"reviewer_accepted": int(tr.get("reviewer_accepted") or 0),
				}
			)

		line_doc = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget": budget_name,
				"generated_reference": line["generated_reference"],
				"title": line["title"],
				"organisational_owner": line["organisational_owner"],
				"classification": line.get("classification") or "Capital expenditure",
				"funding_source_type": line.get("funding_source_type") or "Exchequer",
				"funding_source_name": line.get("funding_source_name")
				or "Government of Kenya Development Budget",
				"external_financial_line_reference": line.get("external_financial_line_reference")
				or "",
				"approved_amount": line["approved_amount"],
				"amount_reserved": line.get("amount_reserved") or 0,
				"amount_committed": line.get("amount_committed") or 0,
				"amount_actual": line.get("amount_actual") or 0,
				"actual_as_at": actual_as_at,
				"primary_target_id": (primary or {}).get("id") or "",
				"primary_target_code": (primary or {}).get("code") or "",
				"primary_target_name": (primary or {}).get("name") or "",
				"primary_plan_version_id": (primary or {}).get("plan_version_id") or "",
				"primary_snapshot_label": (primary or {}).get("snapshot_label") or "",
				"primary_strategy_linked": 1 if primary else 0,
				"supporting_targets": supporting,
				"value_treatments": treatments,
				"currency": "KES",
				"is_active": 1,
				"order_index": line.get("order_index") or 0,
				"fixture_namespace": FIXTURE_NS,
			}
		)
		line_doc.insert(ignore_permissions=True)
		_seed_line_activity(budget_name, line_doc.name, line.get("funding_activity"))
	return budget_name


def _clear_fixture_activity(budget_name: str) -> None:
	"""Delete fixture activity rows for a budget (snapshots → commitments → reservations)."""
	for doctype in ("Expenditure Snapshot", "Procurement Commitment", "Funding Reservation"):
		if not frappe.db.exists("DocType", doctype):
			continue
		for name in frappe.get_all(
			doctype,
			filters={"budget": budget_name, "fixture_namespace": FIXTURE_NS},
			pluck="name",
		):
			frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)


def _seed_line_activity(budget_name: str, line_name: str, activity: dict | None) -> None:
	"""Seed pack §9.3 reservation / commitment / expenditure for one line."""
	if not activity:
		return
	if not frappe.db.exists("DocType", "Funding Reservation"):
		return

	rsv_name = None
	rsv = activity.get("reservation")
	if rsv:
		rsv_doc = frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"budget": budget_name,
				"budget_line": line_name,
				"generated_reference": rsv["generated_reference"],
				"demand_code": rsv["demand_code"],
				"demand_title": rsv["demand_title"],
				"original_amount": rsv["original_amount"],
				"remaining_reserved": rsv["remaining_reserved"],
				"currency": "KES",
				"status": rsv["status"],
				"event_date": rsv["event_date"],
				"current_downstream_reference": rsv.get("current_downstream_reference") or "",
				"idempotency_key": rsv.get("idempotency_key") or "",
				"fixture_namespace": FIXTURE_NS,
			}
		)
		rsv_doc.insert(ignore_permissions=True)
		rsv_name = rsv_doc.name

	com_name = None
	com = activity.get("commitment")
	if com and frappe.db.exists("DocType", "Procurement Commitment"):
		com_doc = frappe.get_doc(
			{
				"doctype": "Procurement Commitment",
				"budget": budget_name,
				"budget_line": line_name,
				"reservation": rsv_name,
				"generated_reference": com["generated_reference"],
				"contract_code": com["contract_code"],
				"contract_title": com["contract_title"],
				"original_amount": com["original_amount"],
				"current_amount": com["current_amount"],
				"actual_expenditure": com.get("actual_expenditure") or 0,
				"currency": "KES",
				"status": com["status"],
				"event_date": com["event_date"],
				"fixture_namespace": FIXTURE_NS,
			}
		)
		com_doc.insert(ignore_permissions=True)
		com_name = com_doc.name

	exp = activity.get("expenditure")
	if exp and frappe.db.exists("DocType", "Expenditure Snapshot"):
		source_as_at = exp.get("source_as_at")
		if "source_as_at_offset_days" in exp:
			source_as_at = add_days(today(), int(exp["source_as_at_offset_days"]))
		frappe.get_doc(
			{
				"doctype": "Expenditure Snapshot",
				"budget": budget_name,
				"budget_line": line_name,
				"commitment": com_name,
				"generated_reference": exp["generated_reference"],
				"amount": exp["amount"],
				"currency": "KES",
				"source_system": exp["source_system"],
				"source_reference": exp.get("source_reference") or "",
				"contract_code": exp.get("contract_code") or "",
				"source_as_at": source_as_at,
				"reconciliation_status": exp.get("reconciliation_status") or "Matched",
				"fixture_namespace": FIXTURE_NS,
			}
		).insert(ignore_permissions=True)


def upsert_moh_mvp_v1_portfolio() -> dict[str, Any]:
	"""Idempotent portfolio seed for BUD-UI-01 / Overview / Lines."""
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
