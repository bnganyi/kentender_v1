# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""MOH_MVP_V1 portfolio seed — BUD-UI-01 / Overview / Lines fixture rows."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, flt, now_datetime, today

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
		"approval_evidence": "/private/files/moh-bud-0001-approval.pdf",
		"external_approved_total": 560_000_000,
		"attention_note": "Actual expenditure is stale on 1 line",
		"readiness_issue_count": 0,
		"strategy_pvc_treated": 4,
		"strategy_pvc_applicable": 4,
		# BUD-UI-11 — activation record on Active baseline.
		"submitted_by": "budget.rev.seed@example.com",
		"reviewed_by": "Administrator",
		"activated_by": "Administrator",
		"submitted_at_offset_days": -40,
		"reviewed_at_offset_days": -38,
		"activated_at_offset_days": -35,
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
						"plan_item_code": "PPI-MOH-2027-021",
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
		# BUD-UI-08/09 — Draft list smoke + Submitted review smoke (not applied).
		"budget_revisions": (
			{
				"generated_reference": "BR-MOH-0001",
				"status": "Draft",
				"revision_type": "Line amendment",
				"external_approval_reference": "MOF/2027/REV-MOH-01",
				"approval_date": "2027-11-01",
				"effective_date": "2027-11-15",
				"reason": "Externally approved uplift for digital clinical systems infrastructure.",
				"lines": (
					{
						"line_code": "MOH-BL-0001",
						"change_amount": 25_000_000,
					},
				),
			},
			{
				"generated_reference": "BR-MOH-0002",
				"status": "Submitted",
				"revision_type": "Line amendment",
				"external_approval_reference": "MOF/2027/REV-MOH-02",
				"approval_date": "2027-11-10",
				"effective_date": "2027-11-20",
				"reason": "Submitted uplift pending Budget Authority apply.",
				"approval_evidence": "/private/files/moh-rev-moh-02.pdf",
				# Non-Admin submitter so Authority/Admin can Apply (AC-018).
				"submitted_by": "budget.rev.seed@example.com",
				"lines": (
					{
						"line_code": "MOH-BL-0002",
						"change_amount": 5_000_000,
					},
				),
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
		"approval_evidence": "/private/files/moh-bud-0002-approval.pdf",
		"external_approved_total": 600_000_000,
		"attention_note": "",
		# Portfolio funding_exceptions attention (not live readiness blockers).
		"readiness_issue_count": 2,
		"submitted_by": "budget.rev.seed@example.com",
		"submitted_at_offset_days": -2,
		"lines": (
			{
				"generated_reference": "MOH-BL-0003",
				"title": "Digital clinical systems infrastructure",
				"approved_amount": 500_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Capital expenditure",
				"organisational_owner": "Director, Digital Health",
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": "MOH-TGT-0001",
				"primary_target_name": "At least 99.9% annual availability by 30 June 2028",
				"value_treatments": _PVC_TREATMENTS_BL0001,
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
		"generated_reference": "MOH-BUD-0003",
		"title": "Ministry of Health Procurement Budget FY 2026/27",
		"fiscal_period": "2026/27",
		"start_date": "2026-07-01",
		"end_date": "2027-06-30",
		"status": "Closed",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2026-01",
		"approval_date": "2026-06-12",
		"approval_evidence": "/private/files/moh-bud-0003-approval.pdf",
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
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": "MOH-TGT-0001",
				"primary_target_name": "At least 99.9% annual availability by 30 June 2028",
				"value_treatments": _PVC_TREATMENTS_BL0001,
				"order_index": 1,
			},
		),
	},
	# BUD-UI-11 — Draft with intentional readiness blockers (Stitch checklist smoke).
	{
		"generated_reference": "MOH-BUD-0004",
		"title": "Ministry of Health Procurement Budget FY 2029/30",
		"fiscal_period": "2029/30",
		"start_date": "2029-07-01",
		"end_date": "2030-06-30",
		"status": "Draft",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2029-01",
		"approval_date": "2029-06-10",
		"approval_evidence": "",
		"external_approved_total": 200_000_000,
		"attention_note": "",
		"readiness_issue_count": 3,
		"lines": (
			{
				"generated_reference": "MOH-BL-0006",
				"title": "Community health outreach supplies",
				"approved_amount": 120_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Goods",
				"organisational_owner": "Director, Primary Health",
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				# Intentional: missing primary Strategy target.
				"primary_target_code": "",
				"primary_target_name": "",
				"order_index": 1,
			},
			{
				"generated_reference": "MOH-BL-0007",
				"title": "Cold-chain maintenance services",
				"approved_amount": 80_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Services",
				"organisational_owner": "Director, Primary Health",
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": "MOH-TGT-0003",
				"primary_target_name": "Digital health technical capability target",
				# Intentional: no value treatments → Required PVC incomplete.
				"order_index": 2,
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
		"approval_evidence": spec.get("approval_evidence") or "",
		"external_approved_total": spec["external_approved_total"],
		"status": spec["status"],
		"attention_note": spec.get("attention_note") or "",
		"readiness_issue_count": int(spec.get("readiness_issue_count") or 0),
		"strategy_pvc_treated": int(spec.get("strategy_pvc_treated") or 0),
		"strategy_pvc_applicable": int(spec.get("strategy_pvc_applicable") or 0),
		"fixture_namespace": FIXTURE_NS,
		"return_reason": "",
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

	# Governance timestamps / actors (BUD-UI-11).
	gov_updates: dict[str, Any] = {}
	if spec.get("submitted_by"):
		gov_updates["submitted_by"] = spec["submitted_by"]
	elif spec["status"] in ("Draft",):
		gov_updates["submitted_by"] = None
		gov_updates["submitted_at"] = None
	if "submitted_at_offset_days" in spec:
		gov_updates["submitted_at"] = add_days(now_datetime(), int(spec["submitted_at_offset_days"]))
	if spec.get("reviewed_by"):
		gov_updates["reviewed_by"] = spec["reviewed_by"]
	elif spec["status"] in ("Draft", "Submitted", "Returned"):
		gov_updates["reviewed_by"] = None
		gov_updates["reviewed_at"] = None
	if "reviewed_at_offset_days" in spec:
		gov_updates["reviewed_at"] = add_days(now_datetime(), int(spec["reviewed_at_offset_days"]))
	if spec.get("activated_by"):
		gov_updates["activated_by"] = spec["activated_by"]
	elif spec["status"] != "Active":
		gov_updates["activated_by"] = None
		gov_updates["activated_at"] = None
	if "activated_at_offset_days" in spec:
		gov_updates["activated_at"] = add_days(now_datetime(), int(spec["activated_at_offset_days"]))
	if gov_updates:
		frappe.db.set_value("Budget", budget_name, gov_updates, update_modified=False)

	# Replace fixture revisions + activity then lines (FK-safe order).
	_clear_fixture_revisions(budget_name)
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

	rev_specs = spec.get("budget_revisions")
	if rev_specs is None and spec.get("budget_revision"):
		rev_specs = (spec["budget_revision"],)
	for rev_spec in rev_specs or ():
		_seed_budget_revision(budget_name, rev_spec)
	return budget_name


def _clear_fixture_revisions(budget_name: str) -> None:
	"""Delete Budget Revisions for this budget only (never cross-budget by code)."""
	if not frappe.db.exists("DocType", "Budget Revision"):
		return
	for name in frappe.get_all(
		"Budget Revision",
		filters={"budget": budget_name},
		pluck="name",
	):
		frappe.delete_doc("Budget Revision", name, force=1, ignore_permissions=True)


def _seed_budget_revision(budget_name: str, rev_spec: dict | None) -> None:
	"""Seed optional Draft/Submitted revision for BUD-UI-08/09 smoke."""
	if not rev_spec or not frappe.db.exists("DocType", "Budget Revision"):
		return

	# Idempotent — replace same business code if left from a prior seed.
	existing = frappe.db.get_value(
		"Budget Revision",
		{"generated_reference": rev_spec["generated_reference"]},
		"name",
	)
	if existing:
		frappe.delete_doc("Budget Revision", existing, force=1, ignore_permissions=True)

	line_rows = []
	for raw in rev_spec.get("lines") or ():
		line_code = raw["line_code"]
		line_name = frappe.db.get_value(
			"Budget Line",
			{"budget": budget_name, "generated_reference": line_code},
			"name",
		)
		if not line_name:
			continue
		line = frappe.get_doc("Budget Line", line_name)
		before = flt(line.approved_amount)
		change = flt(raw.get("change_amount") or 0)
		after = before + change
		reserved = flt(line.amount_reserved)
		committed = flt(line.amount_committed)
		impact = "Increase" if change > 0 else ("Decrease" if change < 0 else "Balanced")
		if after < reserved + committed:
			impact = "Below floor"
		line_rows.append(
			{
				"budget_line": line.name,
				"line_code": line.generated_reference,
				"line_title": line.title,
				"before_amount": before,
				"change_amount": change,
				"after_amount": after,
				"reserved_snapshot": reserved,
				"committed_snapshot": committed,
				"impact_status": impact,
			}
		)
	if not line_rows:
		return

	status = rev_spec.get("status") or "Draft"
	doc = frappe.get_doc(
		{
			"doctype": "Budget Revision",
			"budget": budget_name,
			"generated_reference": rev_spec["generated_reference"],
			"status": status,
			"revision_type": rev_spec.get("revision_type") or "Line amendment",
			"external_approval_reference": rev_spec.get("external_approval_reference") or "",
			"approval_date": rev_spec.get("approval_date"),
			"effective_date": rev_spec.get("effective_date"),
			"reason": rev_spec.get("reason") or "",
			"approval_evidence": rev_spec.get("approval_evidence") or "",
			"fixture_namespace": FIXTURE_NS,
			"lines": line_rows,
		}
	)
	if status == "Submitted":
		doc.submitted_by = rev_spec.get("submitted_by") or "Administrator"
		doc.submitted_at = now_datetime()
	doc.insert(ignore_permissions=True)


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
				"plan_item_code": rsv.get("plan_item_code") or "",
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


def _ensure_seed_revision_officer() -> str:
	"""User used as Submitted By on BR-MOH-0002 so Admin/Authority can Apply (AC-018)."""
	email = "budget.rev.seed@example.com"
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Budget",
				"last_name": "Revision Seed",
				"send_welcome_email": 0,
				"new_password": "Test@12345",
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Budget Officer")
	return email


def _clear_fixture_audit(budget_name: str) -> None:
	if not frappe.db.exists("DocType", "Budget Audit Event"):
		return
	frappe.flags.allow_budget_audit_purge = True
	try:
		for name in frappe.get_all(
			"Budget Audit Event",
			filters={"budget": budget_name, "fixture_namespace": FIXTURE_NS},
			pluck="name",
		):
			frappe.delete_doc("Budget Audit Event", name, force=1, ignore_permissions=True)
	finally:
		frappe.flags.allow_budget_audit_purge = False


def _seed_budget_audit(budget_name: str, budget_code: str) -> None:
	"""BUD-UI-12 — pack-aligned immutable audit ledger for MOH-BUD-0001."""
	if budget_code != "MOH-BUD-0001":
		return
	if not frappe.db.exists("DocType", "Budget Audit Event"):
		return

	from kentender_budget.services.budget_audit_contracts import record_event
	from kentender_budget.services.budget_line_contracts import format_kes_full

	_clear_fixture_audit(budget_name)
	officer = "budget.rev.seed@example.com"
	# Chronological pack §9.3 / governance story (newest-first display via event_at).
	events = (
		{
			"event_type": "Revision applied",
			"event_at": "2027-10-25 11:00:00",
			"actor": "Administrator",
			"actor_kind": "user",
			"record_code": "BR-MOH-0000",
			"record_doctype": "Budget Revision",
			"change_summary": f"Net Change: {format_kes_full(25_000_000)}",
			"source_reference": "MOF/2027/REV-MOH-00",
			"reason": "Historical externally approved uplift (audit seed only).",
		},
		{
			"event_type": "Budget activated",
			"event_at": "2027-10-24 09:15:00",
			"actor": "Administrator",
			"actor_kind": "user",
			"record_code": budget_code,
			"record_doctype": "Budget",
			"before_summary": "Submitted",
			"after_summary": "Active",
			"change_summary": "Status: Submitted → Active",
			"source_reference": "MOH-FIN-BUD-2027-01",
		},
		{
			"event_type": "Expenditure snapshot recorded",
			"event_at": "2027-11-05 08:00:00",
			"actor": "Finance system",
			"actor_kind": "integration",
			"record_code": "EXP-MOH-0001",
			"record_doctype": "Expenditure Snapshot",
			"change_summary": f"Actual: {format_kes_full(180_000_000)} (Stale)",
			"source_reference": "FIN-SNAP-MOH-2027-11",
		},
		{
			"event_type": "Contract commitment recorded",
			"event_at": "2027-10-28 10:00:00",
			"actor": "System",
			"actor_kind": "system",
			"record_code": "COM-MOH-0001",
			"record_doctype": "Procurement Commitment",
			"change_summary": f"Commitment: {format_kes_full(310_000_000)}",
			"source_reference": "CTR-MOH-2027-005",
		},
		{
			"event_type": "Reservation partially converted",
			"event_at": "2027-10-28 09:55:00",
			"actor": "System",
			"actor_kind": "system",
			"record_code": "RSV-MOH-0001",
			"record_doctype": "Funding Reservation",
			"change_summary": f"Remaining reserved: {format_kes_full(145_000_000)}",
			"source_reference": "TND-MOH-2027-008",
		},
		{
			"event_type": "Funding reserved",
			"event_at": "2027-09-12 14:30:00",
			"actor": "System",
			"actor_kind": "system",
			"record_code": "RSV-MOH-0001",
			"record_doctype": "Funding Reservation",
			"change_summary": f"Reserved: {format_kes_full(455_000_000)}",
			"source_reference": "DMD-MOH-2027-014",
		},
		{
			"event_type": "Budget submitted",
			"event_at": "2027-06-20 10:00:00",
			"actor": officer,
			"actor_kind": "user",
			"record_code": budget_code,
			"record_doctype": "Budget",
			"before_summary": "Draft",
			"after_summary": "Submitted",
			"change_summary": "Status: Draft → Submitted",
			"source_reference": "MOH-FIN-BUD-2027-01",
		},
		{
			"event_type": "Baseline registered",
			"event_at": "2027-06-15 10:00:00",
			"actor": "Direct capture",
			"actor_kind": "integration",
			"record_code": budget_code,
			"record_doctype": "Budget",
			"change_summary": "Initial baseline",
			"source_reference": "MOH-FIN-BUD-2027-01",
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
			before_summary=ev.get("before_summary") or "",
			after_summary=ev.get("after_summary") or "",
			change_summary=ev.get("change_summary") or "",
			source_reference=ev.get("source_reference") or "",
			reason=ev.get("reason") or "",
			fixture_namespace=FIXTURE_NS,
		)


def upsert_moh_mvp_v1_portfolio() -> dict[str, Any]:
	"""Idempotent portfolio seed for BUD-UI-01 / Overview / Lines."""
	frappe.only_for(("System Manager", "Administrator"))
	ensure_budget_roles()
	ensure_currency_kes()
	_ensure_seed_revision_officer()
	pe_name = ensure_procuring_entity(PE_CODE, PE_NAME)
	created: list[str] = []
	for spec in BUDGETS:
		name = _upsert_budget(pe_name, spec)
		created.append(name)
		_seed_budget_audit(name, spec["generated_reference"])
	frappe.db.commit()
	return {
		"ok": True,
		"fixture_namespace": FIXTURE_NS,
		"procuring_entity": pe_name,
		"budgets": created,
		"codes": [b["generated_reference"] for b in BUDGETS],
	}
