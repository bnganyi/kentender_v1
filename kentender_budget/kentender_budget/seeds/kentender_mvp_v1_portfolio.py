# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 portfolio seed — Contract v2.0 Budget fixtures."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, flt, get_datetime, today

from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_core.seeds.kentender_mvp_v1 import constants as C

FIXTURE_NS = C.FIXTURE_NS
TEST_ACTIVITY_NS = "KENTENDER_MVP_V1_BUDGET_TEST_ACT"
PE_CODE = C.PE_MOH
PE_NAME = C.PE_MOH_NAME


def _fixture_now():
	return get_datetime(C.FIXTURE_NOW_STR)


def _fixture_date_offset(days: int):
	return C.fixture_date_offset_days(days)


def _fixture_datetime_offset(days: int):
	return get_datetime(C.fixture_datetime_offset_days(days))


def _wall_clock_stale_as_at():
	"""Date old enough to render Stale against real `today()` (fixture clock is narrative)."""
	from kentender_budget.services.budget_line_contracts import ACTUAL_STALE_DAYS

	return add_days(today(), -(int(ACTUAL_STALE_DAYS) + 1))


# Contract §6 — treatments keyed by Strategy Value Commitment codes.
_PVC_TREATMENTS_DHI = (
	{
		"pvc_code": "MOH-PVC-EFT-01",
		"pvc_name": "Improve availability of critical health services",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Infrastructure supports reliable critical health services",
	},
	{
		"pvc_code": "MOH-PVC-ECO-01",
		"pvc_name": "Reduce whole-life infrastructure cost",
		"requirement_level": "Required",
		"treatment": "Dedicated allocation",
		"dedicated_amount": 40_000_000,
		"rationale": (
			"KES 40,000,000 for whole-life costing, energy efficiency and lifecycle optimisation"
		),
	},
	{
		"pvc_code": "MOH-PVC-RES-01",
		"pvc_name": "Improve continuity of critical services",
		"requirement_level": "Recommended",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Redundancy, continuity and support requirements are included",
	},
	{
		"pvc_code": "MOH-PVC-SUS-02",
		"pvc_name": "Ensure compliant handling of replaced ICT equipment",
		"requirement_level": "Required",
		"treatment": "No direct allocation required",
		"dedicated_amount": 0,
		"rationale": "Disposal cost is included in funded asset-replacement activities",
	},
)

_PVC_TREATMENTS_HWD = (
	{
		"pvc_code": "MOH-PVC-LOC-01",
		"pvc_name": "Develop internal and local technical capability",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Training and certification build internal technical capability",
	},
	{
		"pvc_code": "MOH-PVC-EFT-01",
		"pvc_name": "Improve availability of critical health services",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Capability supports continuity of digital clinical services",
	},
	{
		"pvc_code": "MOH-PVC-ECO-01",
		"pvc_name": "Reduce whole-life infrastructure cost",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Training and certification costs are included in the line amount",
	},
	{
		"pvc_code": "MOH-PVC-RES-01",
		"pvc_name": "Improve continuity of critical services",
		"requirement_level": "Recommended",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Continuity capability is included in the training programme",
	},
)

_PVC_TREATMENTS_CGK = (
	{
		"pvc_code": "CGK-PVC-EFT-01",
		"pvc_name": "Improve availability of critical health services",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Equipment supports reliable vaccine services",
	},
	{
		"pvc_code": "CGK-PVC-ECO-01",
		"pvc_name": "Reduce whole-life infrastructure cost",
		"requirement_level": "Required",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Acquisition, maintenance and operating cost are considered together",
	},
	{
		"pvc_code": "CGK-PVC-SUS-01",
		"pvc_name": "Reduce infrastructure energy consumption",
		"requirement_level": "Recommended",
		"treatment": "Embedded in line",
		"dedicated_amount": 0,
		"rationale": "Solar power reduces reliance on unstable grid supply and operating energy",
	},
)

BUDGETS = (
	{
		"generated_reference": C.BUD_ACTIVE,
		"title": "Ministry of Health Procurement Budget FY 2027/28",
		"fiscal_period": "2027/28",
		"start_date": "2027-07-01",
		"end_date": "2028-06-30",
		"status": "Active",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2027-01",
		"approval_date": "2027-06-15",
		"approval_evidence": "/private/files/moh-bud-2027-approval.pdf",
		"external_approved_total": 560_000_000,
		"attention_note": "",
		"readiness_issue_count": 0,
		"strategy_pvc_treated": 4,
		"strategy_pvc_applicable": 4,
		"submitted_by": C.USER_MEDICAL,
		"reviewed_by": C.USER_BUD_REVIEWER,
		"activated_by": C.USER_BUD_AUTHORITY,
		"submitted_at_offset_days": -40,
		"reviewed_at_offset_days": -38,
		"activated_at_offset_days": -35,
		"lines": (
			{
				"generated_reference": C.BL_DHI_2027,
				"title": "Digital clinical systems infrastructure",
				"approved_amount": 480_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"amount_actual": 0,
				"classification": "Capital expenditure",
				"external_financial_line_reference": "HLTH-INF-2027-004",
				"organisational_owner": C.DIR_DHP_NAME,
				"owner_org_unit": C.OU_DIR_DHP,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_AVAIL_2028,
				"primary_target_name": "At least 99.9% annual availability by 30 June 2028",
				"supporting_targets": (
					{
						"target_code": C.TGT_RESTORE_2028,
						"target_name": "Restore critical services within four hours by 30 June 2028",
						"reason": "Infrastructure investment supports service restoration and continuity.",
					},
				),
				"value_treatments": _PVC_TREATMENTS_DHI,
				"order_index": 1,
			},
			{
				"generated_reference": C.BL_HWD_2027,
				"title": "Digital Health Workforce Capacity Development",
				"approved_amount": 80_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"amount_actual": 0,
				"actual_as_at": None,
				"classification": "Services",
				"organisational_owner": C.DIR_HRMD_NAME,
				"owner_org_unit": C.OU_DIR_HRMD,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_SKILLS_2029,
				"primary_target_name": "Train and certify 150 digital-health technical staff by 30 June 2029",
				"value_treatments": _PVC_TREATMENTS_HWD,
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
						"line_code": C.BL_DHI_2027,
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
				"submitted_by": "budget.rev.seed@example.com",
				"lines": (
					{
						"line_code": C.BL_HWD_2027,
						"change_amount": 5_000_000,
					},
				),
			},
		),
	},
	{
		"generated_reference": C.BUD_DRAFT,
		"title": "Ministry of Health Procurement Budget FY 2028/29",
		"fiscal_period": "2028/29",
		"start_date": "2028-07-01",
		"end_date": "2029-06-30",
		"status": "Draft",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2028-01",
		"approval_date": "2028-06-10",
		"approval_evidence": "/private/files/moh-bud-2028-approval.pdf",
		"external_approved_total": 600_000_000,
		"attention_note": "",
		"readiness_issue_count": 0,
		"lines": (
			{
				"generated_reference": C.BL_DHI_2028,
				"title": "Digital clinical systems infrastructure",
				"approved_amount": 480_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Capital expenditure",
				"organisational_owner": C.DIR_DHP_NAME,
				"owner_org_unit": C.OU_DIR_DHP,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_AVAIL_2029,
				"primary_target_name": "Maintain at least 99.95% annual availability by 30 June 2029",
				"supporting_targets": (
					{
						"target_code": C.TGT_RESTORE_2029,
						"target_name": "Restore critical services within two hours by 30 June 2029",
						"reason": "Successor restoration target for FY 2028/29 infrastructure line.",
					},
				),
				"value_treatments": _PVC_TREATMENTS_DHI,
				"order_index": 1,
			},
			{
				"generated_reference": C.BL_HWD_2028,
				"title": "Digital-health workforce capability",
				"approved_amount": 120_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Services",
				"organisational_owner": C.DIR_HRMD_NAME,
				"owner_org_unit": C.OU_DIR_HRMD,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_SKILLS_2030,
				"primary_target_name": "Train and certify 220 digital-health technical staff by 30 June 2030",
				"value_treatments": _PVC_TREATMENTS_HWD,
				"order_index": 2,
			},
		),
	},
	{
		"generated_reference": C.BUD_CLOSED,
		"title": "Ministry of Health Procurement Budget FY 2026/27",
		"fiscal_period": "2026/27",
		"start_date": "2026-07-01",
		"end_date": "2027-06-30",
		"status": "Closed",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2026-01",
		"approval_date": "2026-06-12",
		"approval_evidence": "/private/files/moh-bud-2026-approval.pdf",
		"external_approved_total": 520_000_000,
		"attention_note": "",
		"readiness_issue_count": 0,
		"lines": (
			{
				"generated_reference": "MOH-BL-CLOSED-2026",
				"title": "Prior-year digital health envelope",
				"approved_amount": 520_000_000,
				"amount_reserved": 0,
				"amount_committed": 520_000_000,
				"classification": "Capital expenditure",
				"organisational_owner": C.DIR_DHP_NAME,
				"owner_org_unit": C.OU_DIR_DHP,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_AVAIL_2028,
				"primary_target_name": "At least 99.9% annual availability by 30 June 2028",
				"value_treatments": _PVC_TREATMENTS_DHI,
				"order_index": 1,
			},
		),
	},
	{
		"generated_reference": C.CGK_BUD_ACTIVE,
		"title": "County Government of Kisumu Procurement Budget FY 2027/28",
		"fiscal_period": "2027/28",
		"start_date": "2027-07-01",
		"end_date": "2028-06-30",
		"status": "Active",
		"budget_owner": "County Director of Finance",
		"authoritative_reference": "CGK-FIN-BUD-2027-01",
		"approval_date": "2027-06-20",
		"approval_evidence": "/private/files/cgk-bud-2027-approval.pdf",
		"external_approved_total": 24_000_000,
		"attention_note": "",
		"readiness_issue_count": 0,
		"strategy_pvc_treated": 3,
		"strategy_pvc_applicable": 3,
		"pe_code": C.PE_CGKIS,
		"pe_name": C.PE_CGKIS_NAME,
		"submitted_by": C.USER_KISUMU_OFFICER,
		"lines": (
			{
				"generated_reference": C.CGK_BL_COLDCHAIN,
				"title": "Solar-powered vaccine refrigerators and temperature monitoring",
				"approved_amount": 24_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"amount_actual": 0,
				"actual_as_at": None,
				"classification": "Capital expenditure",
				"organisational_owner": C.OU_CGK_HEALTH_NAME,
				"owner_org_unit": C.OU_CGK_HEALTH,
				"funding_source_type": "Exchequer",
				"funding_source_name": "County Government of Kisumu Development Budget",
				"primary_target_code": C.CGK_TGT_COLDCHAIN,
				"primary_target_name": (
					"At least 95% of supported facilities meet the uptime standard by 30 June 2028"
				),
				"value_treatments": _PVC_TREATMENTS_CGK,
				"order_index": 1,
			},
		),
	},
)

# Test-only edges (not loaded by canonical orchestrator). Kept for readiness /
# role-matrix / XMOD-STR-001 Playwright that need Submitted + incomplete Draft.
EDGE_NS = "KENTENDER_MVP_V1_EDGE"
EDGE_BUDGETS = (
	{
		"generated_reference": "MOH-BUD-0002",
		"title": "Ministry of Health Procurement Budget FY 2028/29 (Submitted edge)",
		"fiscal_period": "2028/29",
		"start_date": "2028-07-01",
		"end_date": "2029-06-30",
		"status": "Submitted",
		"budget_owner": "Director, Finance and Accounts",
		"authoritative_reference": "MOH-FIN-BUD-2028-EDGE-01",
		"approval_date": "2028-06-10",
		"approval_evidence": "/private/files/moh-bud-0002-approval.pdf",
		"external_approved_total": 600_000_000,
		"attention_note": "",
		"readiness_issue_count": 2,
		"submitted_by": "budget.rev.seed@example.com",
		"submitted_at_offset_days": -2,
		"fixture_namespace": EDGE_NS,
		"lines": (
			{
				"generated_reference": "MOH-BL-0003",
				"title": "Digital clinical systems infrastructure",
				"approved_amount": 500_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Capital expenditure",
				"organisational_owner": C.DIR_DHP_NAME,
				"owner_org_unit": C.OU_DIR_DHP,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_AVAIL_2029,
				"primary_target_name": "Maintain at least 99.95% annual availability by 30 June 2029",
				"value_treatments": _PVC_TREATMENTS_DHI,
				"order_index": 1,
			},
			{
				"generated_reference": "MOH-BL-0004",
				"title": "Digital health technical capability",
				"approved_amount": 100_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Services",
				"organisational_owner": C.DIR_HRMD_NAME,
				"owner_org_unit": C.OU_DIR_HRMD,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_SKILLS_2029,
				"primary_target_name": "Train and certify 150 digital-health technical staff by 30 June 2029",
				"value_treatments": _PVC_TREATMENTS_HWD,
				"order_index": 2,
			},
		),
	},
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
		"fixture_namespace": EDGE_NS,
		"lines": (
			{
				"generated_reference": "MOH-BL-0006",
				"title": "Community health outreach supplies",
				"approved_amount": 120_000_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"classification": "Goods",
				"organisational_owner": "Director, Primary Health",
				"owner_org_unit": C.OU_DIR_HRMD,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
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
				"owner_org_unit": C.OU_DIR_HRMD,
				"funding_source_type": "Exchequer",
				"funding_source_name": "Government of Kenya Development Budget",
				"primary_target_code": C.TGT_SKILLS_2029,
				"primary_target_name": "Train and certify 150 digital-health technical staff by 30 June 2029",
				"order_index": 2,
			},
		),
	},
)


def _resolve_target_snapshot(code: str, fallback_name: str) -> dict[str, str]:
	"""Prefer live Active Performance Target on an Active plan; fall back to pack snapshot."""
	try:
		from kentender_strategy.services.strategy_consumer import resolve_performance_target_id

		target_id = resolve_performance_target_id(target_code=code)
	except ImportError:
		target_id = frappe.db.get_value(
			"Performance Target", {"target_code": code, "status": "Active"}, "name"
		)
	if target_id:
		row = frappe.db.get_value(
			"Performance Target",
			target_id,
			["name", "title", "plan_version", "target_code"],
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
	return frappe.db.get_value("Strategy Value Commitment", {"commitment_code": code}, "name") or ""


def _upsert_budget(pe_name: str, spec: dict[str, Any]) -> str:
	ns = spec.get("fixture_namespace") or FIXTURE_NS
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
		"fixture_namespace": ns,
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
		gov_updates["submitted_at"] = _fixture_datetime_offset(int(spec["submitted_at_offset_days"]))
	if spec.get("reviewed_by"):
		gov_updates["reviewed_by"] = spec["reviewed_by"]
	elif spec["status"] in ("Draft", "Submitted", "Returned"):
		gov_updates["reviewed_by"] = None
		gov_updates["reviewed_at"] = None
	if "reviewed_at_offset_days" in spec:
		gov_updates["reviewed_at"] = _fixture_datetime_offset(int(spec["reviewed_at_offset_days"]))
	if spec.get("activated_by"):
		gov_updates["activated_by"] = spec["activated_by"]
	elif spec["status"] != "Active":
		gov_updates["activated_by"] = None
		gov_updates["activated_at"] = None
	if "activated_at_offset_days" in spec:
		gov_updates["activated_at"] = _fixture_datetime_offset(int(spec["activated_at_offset_days"]))
	if gov_updates:
		frappe.db.set_value("Budget", budget_name, gov_updates, update_modified=False)

	# Replace fixture revisions + activity then lines (FK-safe order).
	_clear_fixture_revisions(budget_name)
	_clear_fixture_activity(budget_name)
	for line_name in frappe.get_all(
		"Budget Line",
		filters={"budget": budget_name, "fixture_namespace": ns},
		pluck="name",
	):
		frappe.delete_doc("Budget Line", line_name, force=1, ignore_permissions=True)

	for line in spec.get("lines") or ():
		actual_as_at = line.get("actual_as_at")
		if line.get("actual_as_at_stale"):
			actual_as_at = _wall_clock_stale_as_at()
		elif "actual_as_at_offset_days" in line:
			actual_as_at = _fixture_date_offset(int(line["actual_as_at_offset_days"]))

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
				"owner_org_unit": line.get("owner_org_unit") or "",
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
				"fixture_namespace": ns,
			}
		)
		# Fixture may snapshot historical / non-selectable-for-new targets; API save enforces Active.
		line_doc.flags.skip_budget_strategy_validate = True
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
		doc.submitted_at = _fixture_now()
	doc.insert(ignore_permissions=True)


def _clear_fixture_activity(budget_name: str) -> None:
	"""Delete fixture activity rows for a budget (snapshots → commitments → reservations)."""
	namespaces = (FIXTURE_NS, TEST_ACTIVITY_NS)
	for doctype in ("Expenditure Snapshot", "Procurement Commitment", "Funding Reservation"):
		if not frappe.db.exists("DocType", doctype):
			continue
		for ns in namespaces:
			for name in frappe.get_all(
				doctype,
				filters={"budget": budget_name, "fixture_namespace": ns},
				pluck="name",
			):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)


def _seed_line_activity(budget_name: str, line_name: str, activity: dict | None) -> None:
	"""Seed pack §9.3 reservation / commitment / expenditure for one line."""
	if not activity:
		return
	if not frappe.db.exists("DocType", "Funding Reservation"):
		return

	ns = activity.get("fixture_namespace") or FIXTURE_NS
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
				"fixture_namespace": ns,
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
				"fixture_namespace": ns,
			}
		)
		com_doc.insert(ignore_permissions=True)
		com_name = com_doc.name

	exp = activity.get("expenditure")
	if exp and frappe.db.exists("DocType", "Expenditure Snapshot"):
		source_as_at = exp.get("source_as_at")
		if "source_as_at_offset_days" in exp:
			source_as_at = _fixture_date_offset(int(exp["source_as_at_offset_days"]))
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
				"fixture_namespace": ns,
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
		for ns in (FIXTURE_NS, TEST_ACTIVITY_NS):
			for name in frappe.get_all(
				"Budget Audit Event",
				filters={"budget": budget_name, "fixture_namespace": ns},
				pluck="name",
			):
				frappe.delete_doc("Budget Audit Event", name, force=1, ignore_permissions=True)
	finally:
		frappe.flags.allow_budget_audit_purge = False


def _seed_budget_audit(budget_name: str, budget_code: str) -> None:
	"""BUD-UI-12 — pack-aligned immutable audit ledger for Active FY Budget."""
	if budget_code != C.BUD_ACTIVE:
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


def upsert_kentender_mvp_v1_portfolio(
	*, include_test_edges: bool = True, commit: bool = True
) -> dict[str, Any]:
	"""Idempotent portfolio seed for BUD-UI-01 / Overview / Lines.

	Canonical orchestrator passes include_test_edges=False.
	Domain/UI tests keep edges (Submitted 0002 + incomplete Draft 0004).
	"""
	frappe.only_for(("System Manager", "Administrator"))
	ensure_budget_roles()
	ensure_currency_kes()
	_ensure_seed_revision_officer()
	pe_moh = ensure_procuring_entity(PE_CODE, PE_NAME, entity_type="Ministry", short_name="MoH")
	pe_cgk = ensure_procuring_entity(
		C.PE_CGKIS, C.PE_CGKIS_NAME, entity_type="County Government", short_name="Kisumu"
	)
	specs = list(BUDGETS)
	if include_test_edges:
		specs.extend(EDGE_BUDGETS)
	created: list[str] = []
	for spec in specs:
		pe_name = pe_cgk if spec.get("pe_code") == C.PE_CGKIS else pe_moh
		if spec.get("pe_code") and spec.get("pe_code") not in (C.PE_MOH, C.PE_CGKIS):
			pe_name = ensure_procuring_entity(spec["pe_code"], spec.get("pe_name") or spec["pe_code"])
		name = _upsert_budget(pe_name, spec)
		created.append(name)
		if spec.get("fixture_namespace", FIXTURE_NS) == FIXTURE_NS and spec.get("pe_code") != C.PE_CGKIS:
			_seed_budget_audit(name, spec["generated_reference"])
	if commit:
		frappe.db.commit()
	return {
		"ok": True,
		"fixture_namespace": FIXTURE_NS,
		"procuring_entity": pe_moh,
		"procuring_entity_cgkis": pe_cgk,
		"budgets": created,
		"codes": [b["generated_reference"] for b in specs],
		"include_test_edges": include_test_edges,
	}


def clear_moh_bl_0006_primary_for_e2e() -> dict[str, Any]:
	"""XMOD-STR-001 Playwright — restore MOH-BL-0006 missing-primary fixture state."""
	frappe.only_for(("System Manager", "Administrator"))
	name = frappe.db.get_value("Budget Line", {"generated_reference": "MOH-BL-0006"}, "name")
	if not name:
		return {"ok": False, "error": "MOH-BL-0006 not found"}
	frappe.db.set_value(
		"Budget Line",
		name,
		{
			"primary_target_id": "",
			"primary_target_code": "",
			"primary_target_name": "",
			"primary_plan_version_id": "",
			"primary_snapshot_label": "",
			"primary_strategy_linked": 0,
		},
		update_modified=False,
	)
	frappe.db.commit()
	return {"ok": True, "line": name}


def set_budget_line_allocation_by_code(line_code: str, amount: float) -> dict[str, Any]:
	"""Playwright helper — set amount_allocated by Budget Line.generated_reference when present."""
	frappe.only_for(("System Manager", "Administrator"))
	code = (line_code or "").strip()
	name = frappe.db.get_value("Budget Line", {"generated_reference": code}, "name")
	if not name and frappe.db.exists("Budget Line", code):
		name = code
	if not name:
		return {"ok": False, "error": f"Budget Line {code} not found"}
	meta = frappe.get_meta("Budget Line")
	if not meta.has_field("amount_allocated"):
		return {"ok": False, "error": "amount_allocated field not on Budget Line", "skipped": True}
	frappe.db.set_value("Budget Line", name, "amount_allocated", amount, update_modified=False)
	frappe.db.commit()
	return {"ok": True, "line": name, "amount_allocated": amount}
