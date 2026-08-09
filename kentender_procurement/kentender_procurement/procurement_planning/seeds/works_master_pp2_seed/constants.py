# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master PP2 seed — business codes and field values (spec §4–§16)."""

from __future__ import annotations

from typing import Final

# Upstream
PE_CODE: Final[str] = "PE-MOH"
DEMAND_CODE: Final[str] = "DEM-MOH-2026-001"
DEMAND_ITEM_CODE: Final[str] = "DEMITEM-MOH-2026-001-001"
BUDGET_LINE_CODE: Final[str] = "MOH-BL-DHI-2027"  # Budget Line.generated_reference (MVP-1)
JOURNEY_CODE: Final[str] = "JRN-MOH-2026-001"
STD_VERSION_CODE: Final[str] = "STDTV-WORKS-BUILDING-CIVIL-APR2022"
TENDER_CODE: Final[str] = "TND-MOH-2026-001"

# Planning records
PLAN_CODE: Final[str] = "PLAN-MOH-2026"
PLAN_NAME: Final[str] = "Ministry of Health Procurement Plan FY 2026/2027"
PLAN_DESCRIPTION: Final[str] = (
	"Procurement plan for approved Ministry of Health needs for FY 2026/2027."
)
FISCAL_YEAR: Final[int] = 2026
PLAN_PLANNING_CYCLE_CODE: Final[str] = "BUDGET-MOH-2026"
PLAN_CREATOR_USER_CODE: Final[str] = "USER-PLAN-001"
PLAN_APPROVER_USER_CODE: Final[str] = "USER-HOP-001"
PLAN_CREATOR_EMAIL: Final[str] = "planner@moh.test"
PLAN_APPROVER_EMAIL: Final[str] = "planning.authority@moh.test"
PLAN_CREATED_AT: Final[str] = "2026-04-10 08:00:00"
PLAN_APPROVED_AT: Final[str] = "2026-04-10 08:30:00"

INCLUSION_CODE: Final[str] = "PLANINCL-MOH-2026-001"
INCLUSION_NOTE: Final[str] = "Approved Works demand included in FY 2026/2027 procurement plan."
INCLUSION_INCLUDED_AT: Final[str] = "2026-04-10 10:00:00"
INCLUSION_FISCAL_YEAR: Final[str] = "2026/2027"
INCLUSION_PROCUREMENT_CATEGORY: Final[str] = "Works"
INCLUSION_STATUS_INCLUDED: Final[str] = "Included"
INCLUSION_STATUS_PACKAGED: Final[str] = "Packaged"
SOURCE_DEMAND_STATUS_AT_INCLUSION: Final[str] = "Approved"
SOURCE_BUDGET_STATUS_AT_INCLUSION: Final[str] = "Approved / Confirmed"

PKG_CODE: Final[str] = "PKG-MOH-2026-001"
PKG_TITLE: Final[str] = "District Hospital Renovation Works"
PKG_DESCRIPTION: Final[str] = (
	"Procurement package for building and associated civil engineering renovation works "
	"at Makutano District Hospital."
)
PKG_PREPARED_AT: Final[str] = "2026-04-18 16:00:00"
PKG_FISCAL_YEAR: Final[str] = "2026/2027"
PKG_PROCUREMENT_CATEGORY: Final[str] = "Works"
PKG_REQUIRED_STD_CATEGORY: Final[str] = "Works"
PKG_REQUIRED_STD_TYPE: Final[str] = "Building and Associated Civil Engineering Works"
PKG_PRIORITY: Final[str] = "High"

PKG_LINE_CODE: Final[str] = "PKGLINE-MOH-2026-001-001"
PKG_LINE_TITLE: Final[str] = "Building and associated civil engineering renovation works"
PKG_LINE_DESCRIPTION: Final[str] = (
	"Consolidated Works package line derived from approved demand item "
	"for District Hospital Renovation Works."
)
PKG_LINE_UOM: Final[str] = "Lot"
PKG_LINE_QUANTITY: Final[float] = 1.0
PKG_LINE_STATUS_RELEASED: Final[str] = "Released"
METHDEC_CODE: Final[str] = "METHDEC-PKG-MOH-2026-001"
METHDEC_CONTRACT_TYPE: Final[str] = "Admeasurement / BOQ"
METHDEC_TEMPLATE_CODE: Final[str] = "WORKS-PROFILE-BUILDING-CIVIL"
METHDEC_RULE_PROFILE_CODE: Final[str] = "WORKS-PROFILE-BUILDING-CIVIL"
METHDEC_METHOD_BASIS: Final[str] = "Template"
METHDEC_THRESHOLD_RESULT: Final[str] = "PASS"
METHDEC_DECIDED_AT: Final[str] = "2026-04-18 16:10:00"
METHDEC_APPROVED_AT: Final[str] = "2026-04-20 09:30:00"
METHDEC_REVIEWER_USER_CODE: Final[str] = "USER-PLAN-REV-001"
METHDEC_REVIEWER_EMAIL: Final[str] = "planning.reviewer@moh.test"
PKGRDY_CODE: Final[str] = "PKGRDY-PKG-MOH-2026-001-001"
PKGRDY_RUN_AT: Final[str] = "2026-04-20 09:45:00"
PKGREV_CODE: Final[str] = "PKGREV-PKG-MOH-2026-001-001"
PKGREV_DECIDED_AT: Final[str] = "2026-04-20 09:30:00"
PKGREV_DECISION_REASON: Final[str] = (
	"Package approved for readiness and release to Tender Management."
)
PKGREV_FROM_STATE: Final[str] = "In Review"
PKGREV_TO_STATE: Final[str] = "Approved"
PKGREV_AUDIT_EVENT_REF: Final[str] = "PPAUD-MOH-2026-008"
PKGREL_CODE: Final[str] = "PKGREL-MOH-2026-001"
PKGREL_RELEASED_AT: Final[str] = "2026-04-20 10:15:00"
PKGREL_RELEASED_BY_USER_CODE: Final[str] = PLAN_APPROVER_USER_CODE
PKGREL_RELEASED_BY_EMAIL: Final[str] = PLAN_APPROVER_EMAIL
PKGREL_NEXT_ACTION: Final[str] = "Create and prepare tender using the official Works STD."
PKGREL_AUDIT_EVENT_REF: Final[str] = "PPAUD-MOH-2026-010"
PKGREL_PACKAGE_SCOPE: Final[str] = (
	"Building and associated civil engineering renovation works at Makutano District Hospital"
)
PKGCONSUME_CODE: Final[str] = "PKGCONSUME-MOH-2026-001"
PKGCONSUME_CONSUMED_AT: Final[str] = "2026-04-21 09:00:00"
PKGCONSUME_CONSUMED_BY_USER_CODE: Final[str] = "USER-PO-001"
PKGCONSUME_CONSUMED_BY_EMAIL: Final[str] = "procurement.officer@moh.test"
PKGCONSUME_AUDIT_EVENT_REF: Final[str] = "PPAUD-MOH-2026-012"

# Planning audit events (spec §17)
SEED_SYSTEM_ACTOR_USER_CODE: Final[str] = "SYSTEM"
SEED_SYSTEM_ACTOR_EMAIL: Final[str] = "system@moh.test"
PPAUD_001_DEMAND_ENTERED_AT: Final[str] = "2026-04-10 09:00:00"
PKG_LINE_CREATED_AT: Final[str] = "2026-04-18 16:05:00"
PPAUD_006_SUBMITTED_AT: Final[str] = "2026-04-19 09:00:00"
PPAUD_009_READY_AT: Final[str] = "2026-04-20 10:00:00"
PPAUD_011_LOCKED_AT: Final[str] = "2026-04-20 10:15:05"

MASTER_PLANNING_AUDIT_EVENT_CODES: Final[tuple[str, ...]] = tuple(
	f"PPAUD-MOH-2026-{seq:03d}" for seq in range(1, 13)
)

ESTIMATED_VALUE: Final[float] = 98_000_000.0
CURRENCY: Final[str] = "KES"

DEMAPP_CODE: Final[str] = "DEMAPP-MOH-2026-001"
BUDCONF_CODE: Final[str] = "BUDCONF-MOH-2026-001"

SEED_ACTOR: Final[str] = "Administrator"

CHECKPOINT_ORDER: Final[tuple[str, ...]] = (
	"APPROVED_DEMAND_READY",
	"INCLUDED_IN_PLAN",
	"PACKAGE_DRAFT",
	"READY_FOR_RELEASE",
	"RELEASED_TO_TENDER",
	"CONSUMED_BY_TENDER",
)

DEFAULT_CHECKPOINT: Final[str] = "CONSUMED_BY_TENDER"


def master_readiness_check_items(*, release_source_code: str | None = None) -> list[dict]:
	"""Spec §12.4 PP2-READY check rows for master seed readiness result."""
	release_source = (release_source_code or PKG_CODE).strip()
	return [
		{
			"check_id": "PP2-READY-001",
			"business_label": "Approved demand exists",
			"result": "PASS",
			"blocking": True,
			"message": "Approved demand exists.",
			"required_action": None,
			"source_object_type": "Demand",
			"source_object_code": DEMAND_CODE,
		},
		{
			"check_id": "PP2-READY-002",
			"business_label": "Demand approval certificate exists",
			"result": "PASS",
			"blocking": True,
			"message": "Demand approval certificate exists.",
			"required_action": None,
			"source_object_type": "Demand Approval Certificate",
			"source_object_code": DEMAPP_CODE,
		},
		{
			"check_id": "PP2-READY-003",
			"business_label": "Budget funding confirmation exists",
			"result": "PASS",
			"blocking": True,
			"message": "Budget funding confirmation exists.",
			"required_action": None,
			"source_object_type": "Budget Funding Confirmation",
			"source_object_code": BUDCONF_CODE,
		},
		{
			"check_id": "PP2-READY-004",
			"business_label": "Demand included in procurement plan",
			"result": "PASS",
			"blocking": True,
			"message": "Demand included in procurement plan.",
			"required_action": None,
			"source_object_type": "Planning Inclusion",
			"source_object_code": INCLUSION_CODE,
		},
		{
			"check_id": "PP2-READY-005",
			"business_label": "Package line exists",
			"result": "PASS",
			"blocking": True,
			"message": "Package line exists.",
			"required_action": None,
			"source_object_type": "Procurement Package Line",
			"source_object_code": PKG_LINE_CODE,
		},
		{
			"check_id": "PP2-READY-006",
			"business_label": "Package line maps to demand item",
			"result": "PASS",
			"blocking": True,
			"message": "Package line maps to demand item.",
			"required_action": None,
			"source_object_type": "Demand Item",
			"source_object_code": DEMAND_ITEM_CODE,
		},
		{
			"check_id": "PP2-READY-007",
			"business_label": "Package line maps to budget line",
			"result": "PASS",
			"blocking": True,
			"message": "Package line maps to budget line.",
			"required_action": None,
			"source_object_type": "Budget Line",
			"source_object_code": BUDGET_LINE_CODE,
		},
		{
			"check_id": "PP2-READY-008",
			"business_label": "Package total matches package lines",
			"result": "PASS",
			"blocking": True,
			"message": "Package total matches package lines.",
			"required_action": None,
			"source_object_type": "Procurement Package",
			"source_object_code": PKG_CODE,
		},
		{
			"check_id": "PP2-READY-009",
			"business_label": "Procurement category selected",
			"result": "PASS",
			"blocking": True,
			"message": "Procurement category selected.",
			"required_action": None,
			"source_object_type": "Package Method Decision",
			"source_object_code": METHDEC_CODE,
		},
		{
			"check_id": "PP2-READY-010",
			"business_label": "Procurement method selected",
			"result": "PASS",
			"blocking": True,
			"message": "Procurement method selected.",
			"required_action": None,
			"source_object_type": "Package Method Decision",
			"source_object_code": METHDEC_CODE,
		},
		{
			"check_id": "PP2-READY-011",
			"business_label": "Method justification/derivation recorded",
			"result": "PASS",
			"blocking": True,
			"message": "Method justification/derivation recorded.",
			"required_action": None,
			"source_object_type": "Package Method Decision",
			"source_object_code": METHDEC_CODE,
		},
		{
			"check_id": "PP2-READY-012",
			"business_label": "Required STD category identified",
			"result": "PASS",
			"blocking": True,
			"message": "Required STD category identified.",
			"required_action": None,
			"source_object_type": "STD Template",
			"source_object_code": STD_VERSION_CODE,
		},
		{
			"check_id": "PP2-READY-013",
			"business_label": "Planned schedule dates present",
			"result": "PASS",
			"blocking": False,
			"message": "Planned schedule dates present.",
			"required_action": None,
			"source_object_type": "Procurement Package",
			"source_object_code": PKG_CODE,
		},
		{
			"check_id": "PP2-READY-014",
			"business_label": "Required review/approval complete",
			"result": "PASS",
			"blocking": True,
			"message": "Required review/approval complete.",
			"required_action": None,
			"source_object_type": "Package Review Decision",
			"source_object_code": PKGREV_CODE,
		},
		{
			"check_id": "PP2-READY-015",
			"business_label": "Release handoff can be generated",
			"result": "PASS",
			"blocking": True,
			"message": "Release handoff can be generated.",
			"required_action": None,
			"source_object_type": "Planning Release Package",
			"source_object_code": release_source,
		},
	]


def strict_release_locked_summary() -> dict:
	"""Spec §14.4 locked summary for master planning release."""
	return {
		"package_code": PKG_CODE,
		"package_title": PKG_TITLE,
		"procurement_plan_code": PLAN_CODE,
		"planning_inclusion_code": INCLUSION_CODE,
		"demand_code": DEMAND_CODE,
		"demand_item_codes": [DEMAND_ITEM_CODE],
		"budget_line_code": BUDGET_LINE_CODE,
		"budget_line": BUDGET_LINE_CODE,
		"procurement_method": "Open Tender",
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"estimated_value": ESTIMATED_VALUE,
		"currency": CURRENCY,
		"required_std_category": PKG_REQUIRED_STD_CATEGORY,
		"required_std_type": PKG_REQUIRED_STD_TYPE,
		"package_line_codes": [PKG_LINE_CODE],
	}


def strict_release_passed_forward_summary() -> dict:
	"""Spec §14.5 passed-forward summary for master planning release."""
	return {
		"target_module": "Tender Management",
		"tender_title": PKG_TITLE,
		"package_scope": PKGREL_PACKAGE_SCOPE,
		"procurement_method": "Open Tender",
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"required_std_category": PKG_REQUIRED_STD_CATEGORY,
		"required_std_type": PKG_REQUIRED_STD_TYPE,
		"required_std_template_version_code": STD_VERSION_CODE,
		"estimated_value": ESTIMATED_VALUE,
		"currency": CURRENCY,
		"budget_line_code": BUDGET_LINE_CODE,
		"package_line_codes": [PKG_LINE_CODE],
		"source_approval_refs": [DEMAPP_CODE, BUDCONF_CODE],
		"readiness_code": PKGRDY_CODE,
	}


def strict_release_evidence_links(*, include_tender: bool = False) -> list[dict]:
	"""Spec §14.6 evidence links for master planning release."""
	links = [
		{
			"label": "Approved Demand",
			"object_type": "Demand",
			"object_code": DEMAND_CODE,
			"module": "Demands",
			"route": f"/app/demand/{DEMAND_CODE}",
			"visibility": "Internal",
		},
		{
			"label": "Budget Funding Confirmation",
			"object_type": "Budget Funding Confirmation",
			"object_code": BUDCONF_CODE,
			"module": "Budget & Funding",
			"route": f"/app/procurement-handoff-card/{BUDCONF_CODE}",
			"visibility": "Internal",
		},
		{
			"label": "Package Readiness Result",
			"object_type": "Package Readiness Result",
			"object_code": PKGRDY_CODE,
			"module": "Procurement Planning",
			"route": f"/app/package-readiness-result/{PKGRDY_CODE}",
			"visibility": "Internal",
		},
	]
	if include_tender:
		links.append(
			{
				"label": "TM2 Tender",
				"object_type": "TM2 Tender",
				"object_code": TENDER_CODE,
				"module": "Tender Management",
				"route": f"/app/tm2-tender/{TENDER_CODE}",
				"visibility": "Internal",
			}
		)
	return links


def strict_release_technical_refs() -> dict:
	"""Technical refs stored on the planning release handoff card."""
	return {
		"procurement_plan_code": PLAN_CODE,
		"planning_inclusion_code": INCLUSION_CODE,
		"demand_code": DEMAND_CODE,
		"budget_line_code": BUDGET_LINE_CODE,
		"package_line_code": PKG_LINE_CODE,
		"readiness_code": PKGRDY_CODE,
	}


def strict_consumption_result() -> dict:
	"""Spec §15.4 consumption result JSON for master consumption record."""
	return {
		"tender_code": TENDER_CODE,
		"tender_title": PKG_TITLE,
		"created_from_release": PKGREL_CODE,
		"planning_baseline_preserved": True,
		"changed_values": [],
	}


def strict_readiness_snapshot() -> dict:
	"""Spec §12.5 minimum source snapshot for master readiness result."""
	return {
		"package_code": PKG_CODE,
		"demand_code": DEMAND_CODE,
		"budget_line_code": BUDGET_LINE_CODE,
		"estimated_value": ESTIMATED_VALUE,
		"currency": CURRENCY,
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"procurement_method": "Open Tender",
		"package_line_codes": [PKG_LINE_CODE],
		"required_std_category": PKG_REQUIRED_STD_CATEGORY,
		"required_std_template_version_code": STD_VERSION_CODE,
	}


def master_planning_audit_event_specs() -> tuple[dict, ...]:
	"""Spec §17 — canonical WORKS master Planning Audit Event rows."""
	return (
		{
			"event_code": "PPAUD-MOH-2026-001",
			"occurred_at": PPAUD_001_DEMAND_ENTERED_AT,
			"event_type": "Demand Entered Planning Queue",
			"object_type": "Demand",
			"object_code": DEMAND_CODE,
			"actor_user_code": SEED_SYSTEM_ACTOR_USER_CODE,
			"from_state": None,
			"to_state": "Ready for Planning",
			"evidence_ref": DEMAPP_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-002",
			"occurred_at": INCLUSION_INCLUDED_AT,
			"event_type": "Demand Included in Plan",
			"object_type": "Planning Inclusion Record",
			"object_code": INCLUSION_CODE,
			"actor_user_code": PLAN_CREATOR_USER_CODE,
			"from_state": None,
			"to_state": INCLUSION_STATUS_INCLUDED,
			"evidence_ref": INCLUSION_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-003",
			"occurred_at": PKG_PREPARED_AT,
			"event_type": "Package Created",
			"object_type": "Procurement Package",
			"object_code": PKG_CODE,
			"actor_user_code": PLAN_CREATOR_USER_CODE,
			"from_state": None,
			"to_state": "Draft",
			"evidence_ref": PKG_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-004",
			"occurred_at": PKG_LINE_CREATED_AT,
			"event_type": "Package Line Created",
			"object_type": "Procurement Package Line",
			"object_code": PKG_LINE_CODE,
			"actor_user_code": PLAN_CREATOR_USER_CODE,
			"from_state": None,
			"to_state": "Draft",
			"evidence_ref": PKG_LINE_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-005",
			"occurred_at": METHDEC_DECIDED_AT,
			"event_type": "Method Decision Recorded",
			"object_type": "Package Method Decision",
			"object_code": METHDEC_CODE,
			"actor_user_code": PLAN_CREATOR_USER_CODE,
			"from_state": None,
			"to_state": "Current",
			"evidence_ref": METHDEC_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-006",
			"occurred_at": PPAUD_006_SUBMITTED_AT,
			"event_type": "Package Submitted for Review",
			"object_type": "Procurement Package",
			"object_code": PKG_CODE,
			"actor_user_code": PLAN_CREATOR_USER_CODE,
			"from_state": "Draft",
			"to_state": "In Review",
			"evidence_ref": PKG_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-007",
			"occurred_at": PKGREV_DECIDED_AT,
			"event_type": "Package Approved",
			"object_type": "Procurement Package",
			"object_code": PKG_CODE,
			"actor_user_code": METHDEC_REVIEWER_USER_CODE,
			"from_state": PKGREV_FROM_STATE,
			"to_state": PKGREV_TO_STATE,
			"evidence_ref": PKGREV_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-008",
			"occurred_at": PKGRDY_RUN_AT,
			"event_type": "Readiness Check Run",
			"object_type": "Package Readiness Result",
			"object_code": PKGRDY_CODE,
			"actor_user_code": PLAN_CREATOR_USER_CODE,
			"from_state": None,
			"to_state": "Passed",
			"evidence_ref": PKGRDY_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-009",
			"occurred_at": PPAUD_009_READY_AT,
			"event_type": "Package Marked Ready for Release",
			"object_type": "Procurement Package",
			"object_code": PKG_CODE,
			"actor_user_code": PLAN_APPROVER_USER_CODE,
			"from_state": "Approved",
			"to_state": "Ready for Release",
			"evidence_ref": PKGRDY_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-010",
			"occurred_at": PKGREL_RELEASED_AT,
			"event_type": "Package Released to Tender Management",
			"object_type": "Planning Release Package",
			"object_code": PKGREL_CODE,
			"actor_user_code": PLAN_APPROVER_USER_CODE,
			"from_state": "Ready for Release",
			"to_state": "Released to Tender",
			"evidence_ref": PKGREL_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-011",
			"occurred_at": PPAUD_011_LOCKED_AT,
			"event_type": "Package Locked After Release",
			"object_type": "Procurement Package",
			"object_code": PKG_CODE,
			"actor_user_code": SEED_SYSTEM_ACTOR_USER_CODE,
			"from_state": "Ready for Release",
			"to_state": "Released to Tender",
			"evidence_ref": PKGREL_CODE,
		},
		{
			"event_code": "PPAUD-MOH-2026-012",
			"occurred_at": PKGCONSUME_CONSUMED_AT,
			"event_type": "Release Consumed by Tender Management",
			"object_type": "Planning Release Consumption Record",
			"object_code": PKGCONSUME_CODE,
			"actor_user_code": PKGCONSUME_CONSUMED_BY_USER_CODE,
			"from_state": "Released to Tender",
			"to_state": "Consumed",
			"evidence_ref": TENDER_CODE,
		},
	)


def master_planning_audit_events_for_checkpoint(checkpoint: str) -> tuple[dict, ...]:
	"""Return the audit-event slice required for a checkpoint (spec §17 order)."""
	cp = (checkpoint or DEFAULT_CHECKPOINT).strip().upper()
	try:
		idx = CHECKPOINT_ORDER.index(cp)
	except ValueError:
		return ()
	counts = {
		1: 2,
		2: 5,
		3: 9,
		4: 11,
		5: 12,
	}
	count = counts.get(idx, 0)
	return master_planning_audit_event_specs()[:count]


def works_method_payload() -> dict:
	return {
		"procurement_category": PKG_PROCUREMENT_CATEGORY,
		"procurement_method": "Open Tender",
		"required_std_category": PKG_REQUIRED_STD_CATEGORY,
		"required_std_type": PKG_REQUIRED_STD_TYPE,
		"required_std_template_version_code": STD_VERSION_CODE,
		"contract_type_expectation": METHDEC_CONTRACT_TYPE,
		"method_basis": METHDEC_METHOD_BASIS,
		"threshold_check_result": METHDEC_THRESHOLD_RESULT,
		"template_code": METHDEC_TEMPLATE_CODE,
		"rule_profile_code": METHDEC_RULE_PROFILE_CODE,
		"override_flag": False,
	}
