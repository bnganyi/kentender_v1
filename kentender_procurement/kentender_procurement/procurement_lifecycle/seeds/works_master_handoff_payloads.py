# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master handoff payloads — seed data specification §16 (evidence links omit ``route``; loader injects)."""

from __future__ import annotations

from typing import Any, Final

JOURNEY_CODE: Final[str] = "JRN-MOH-2026-001"

BASE_HANDOFF_CODES: Final[tuple[str, ...]] = (
	"STRATREF-MOH-2026-001",
	"BUDCONF-MOH-2026-001",
	"DEMAPP-MOH-2026-001",
	"PLANINCL-MOH-2026-001",
	"PKGREL-MOH-2026-001",
	"STDREADY-TND-MOH-2026-001",
	"PUBCERT-TND-MOH-2026-001",
)

OPENING_HANDOFF_CODES: Final[tuple[str, ...]] = (
	"CLOSECERT-TND-MOH-2026-001",
	"OPENREADY-TND-MOH-2026-001",
)


def _el(
	label: str,
	object_type: str,
	object_code: str,
	module: str,
	visibility: str = "Internal",
) -> dict[str, str]:
	return {
		"label": label,
		"object_type": object_type,
		"object_code": object_code,
		"module": module,
		"visibility": visibility,
	}


def base_handoff_blueprints() -> list[dict[str, Any]]:
	"""Return seven base-checkpoint handoff definitions (§16.2–16.8)."""
	return [
		{
			"handoff_code": "STRATREF-MOH-2026-001",
			"handoff_title": "Strategy Alignment Reference",
			"source_module": "Strategy",
			"target_module": "Budget",
			"source_object_type": "Strategy Objective",
			"source_object_code": "OBJ-MOH-HOSP-RENOV",
			"target_object_type": "Procurement Budget Line",
			"target_object_code": "BUD-MOH-INFRA-2026-001",
			"status": "Consumed",
			"generated_by": "USER-STRAT-001",
			"generated_at": "2026-01-15 10:00:00",
			"consumed_by": "USER-BUD-001",
			"consumed_at": "2026-02-10 11:00:00",
			"next_action": "Fund this strategic infrastructure priority through an approved budget line.",
			"locked_summary": {
				"strategy_plan": "STRAT-MOH-2026",
				"programme": "PROG-MOH-INFRA",
				"objective": "OBJ-MOH-HOSP-RENOV",
				"priority_level": "High",
			},
			"passed_forward_summary": {
				"strategic_priority": "Improve district hospital infrastructure readiness",
				"target": "Renovate priority district hospital facilities in FY 2026/2027",
				"recommended_budget_area": "Healthcare infrastructure rehabilitation",
			},
			"evidence_links": [
				_el("Strategy Objective", "Strategy Objective", "OBJ-MOH-HOSP-RENOV", "Strategy"),
			],
			"technical_refs": {
				"strategy_plan_code": "STRAT-MOH-2026",
				"programme_code": "PROG-MOH-INFRA",
				"target_code": "TGT-MOH-HOSP-RENOV-2026",
			},
		},
		{
			"handoff_code": "BUDCONF-MOH-2026-001",
			"handoff_title": "Budget Funding Confirmation",
			"source_module": "Budget",
			"target_module": "Demands",
			"source_object_type": "Procurement Budget Line",
			"source_object_code": "BUD-MOH-INFRA-2026-001",
			"target_object_type": "Demand",
			"target_object_code": "DEM-MOH-2026-001",
			"status": "Consumed",
			"generated_by": "USER-BUD-001",
			"generated_at": "2026-02-10 11:00:00",
			"consumed_by": "USER-REQ-001",
			"consumed_at": "2026-03-03 09:20:00",
			"next_action": "Raise demand against the approved infrastructure budget line.",
			"locked_summary": {
				"budget_line": "BUD-MOH-INFRA-2026-001",
				"approved_amount": 120_000_000,
				"currency": "KES",
				"funding_source": "Government of Kenya Development Budget",
				"fiscal_year": "2026/2027",
			},
			"passed_forward_summary": {
				"available_for_procurement_request": True,
				"reserved_for_master_demand": 98_000_000,
				"strategic_objective": "OBJ-MOH-HOSP-RENOV",
			},
			"evidence_links": [
				_el("Procurement Budget Line", "Procurement Budget Line", "BUD-MOH-INFRA-2026-001", "Budget"),
			],
			"technical_refs": {
				"budget_code": "BUDGET-MOH-2026",
				"strategy_objective_code": "OBJ-MOH-HOSP-RENOV",
			},
		},
		{
			"handoff_code": "DEMAPP-MOH-2026-001",
			"handoff_title": "Demand Approval Certificate",
			"source_module": "Demands",
			"target_module": "Procurement Planning",
			"source_object_type": "Demand",
			"source_object_code": "DEM-MOH-2026-001",
			"target_object_type": "Procurement Plan",
			"target_object_code": "PLAN-MOH-2026",
			"status": "Consumed",
			"generated_by": "USER-DA-001",
			"generated_at": "2026-03-05 14:30:00",
			"consumed_by": "USER-PLAN-001",
			"consumed_at": "2026-04-10 10:00:00",
			"next_action": "Include the approved Works demand in the procurement plan and package it for tendering.",
			"locked_summary": {
				"demand_code": "DEM-MOH-2026-001",
				"demand_title": "District Hospital Renovation Works",
				"approved_estimated_value": 98_000_000,
				"currency": "KES",
				"budget_line": "BUD-MOH-INFRA-2026-001",
				"procurement_category": "Works",
			},
			"passed_forward_summary": {
				"approved_need": "Building and associated civil engineering renovation works",
				"requesting_department": "Infrastructure and Facilities Directorate",
				"planning_action": "Create procurement package",
			},
			"evidence_links": [
				_el("Approved Demand", "Demand", "DEM-MOH-2026-001", "Demands"),
				_el(
					"Demand Approval Record",
					"Demand Approval",
					"DEMAPPROVAL-MOH-2026-001",
					"Demands",
				),
			],
			"technical_refs": {
				"demand_item_code": "DEMITEM-MOH-2026-001-001",
				"budget_line_code": "BUD-MOH-INFRA-2026-001",
			},
		},
		{
			"handoff_code": "PLANINCL-MOH-2026-001",
			"handoff_title": "Planning Inclusion Record",
			"source_module": "Procurement Planning",
			"target_module": "Procurement Planning",
			"source_object_type": "Demand",
			"source_object_code": "DEM-MOH-2026-001",
			"target_object_type": "Procurement Plan",
			"target_object_code": "PLAN-MOH-2026",
			"status": "Consumed",
			"generated_by": "USER-PLAN-001",
			"generated_at": "2026-04-10 10:00:00",
			"consumed_by": "USER-PLAN-001",
			"consumed_at": "2026-04-18 16:00:00",
			"next_action": "Prepare a procurement package for the approved Works demand.",
			"locked_summary": {
				"procurement_plan": "PLAN-MOH-2026",
				"included_demand": "DEM-MOH-2026-001",
				"budget_line": "BUD-MOH-INFRA-2026-001",
			},
			"passed_forward_summary": {
				"package_candidate": "District Hospital Renovation Works",
				"category": "Works",
				"estimated_value": 98_000_000,
				"currency": "KES",
			},
			"evidence_links": [
				_el("Procurement Plan", "Procurement Plan", "PLAN-MOH-2026", "Procurement Planning"),
			],
			"technical_refs": {"inclusion_code": "PLANINCL-MOH-2026-001"},
		},
		{
			"handoff_code": "PKGREL-MOH-2026-001",
			"handoff_title": "Planning Release Package",
			"source_module": "Procurement Planning",
			"target_module": "Tender Management",
			"source_object_type": "Procurement Package",
			"source_object_code": "PKG-MOH-2026-001",
			"target_object_type": "TM2 Tender",
			"target_object_code": "TND-MOH-2026-001",
			"status": "Consumed",
			"generated_by": "USER-PLAN-001",
			"generated_at": "2026-04-20 10:15:00",
			"consumed_by": "USER-PO-001",
			"consumed_at": "2026-04-21 09:00:00",
			"next_action": "Create and prepare tender using the official Works STD.",
			"locked_summary": {
				"package_code": "PKG-MOH-2026-001",
				"package_title": "District Hospital Renovation Works",
				"procurement_method": "Open Tender",
				"procurement_category": "Works",
				"budget_line": "BUD-MOH-INFRA-2026-001",
				"estimated_value": 98_000_000,
				"currency": "KES",
			},
			"passed_forward_summary": {
				"required_std_category": "Works",
				"tender_title": "District Hospital Renovation Works",
				"package_scope": (
					"Building and associated civil engineering renovation works at Makutano District Hospital"
				),
			},
			"evidence_links": [
				_el(
					"Released Procurement Package",
					"Procurement Package",
					"PKG-MOH-2026-001",
					"Procurement Planning",
				),
				_el("Created TM2 Tender", "TM2 Tender", "TND-MOH-2026-001", "Tender Management"),
			],
			"technical_refs": {
				"procurement_plan_code": "PLAN-MOH-2026",
				"package_line_code": "PKGLINE-MOH-2026-001-001",
				"tm2_tender_code": "TND-MOH-2026-001",
			},
		},
		{
			"handoff_code": "STDREADY-TND-MOH-2026-001",
			"handoff_title": "Tender Document Readiness Certificate",
			"source_module": "STD Engine / Tender Management",
			"target_module": "Tender Publication",
			"source_object_type": "Tender STD Instance",
			"source_object_code": "STDINST-TND-MOH-2026-001",
			"target_object_type": "TM2 Tender",
			"target_object_code": "TND-MOH-2026-001",
			"status": "Consumed",
			"generated_by": "USER-PO-001",
			"generated_at": "2026-04-28 15:45:00",
			"consumed_by": "USER-PO-001",
			"consumed_at": "2026-04-29 10:00:00",
			"next_action": "Submit tender for publication review.",
			"locked_summary": {
				"std_template_version": "STDTV-WORKS-BUILDING-CIVIL-APR2022",
				"tender_std_instance": "STDINST-TND-MOH-2026-001",
				"readiness_status": "Ready",
			},
			"passed_forward_summary": {
				"tender_document_package_ready": True,
				"supplier_submission_checklist_ready": True,
				"opening_register_rules_ready": True,
				"evaluation_rules_ready": True,
				"contract_carry_forward_terms_ready": True,
			},
			"evidence_links": [
				_el(
					"Tender STD Instance",
					"Tender STD Instance",
					"STDINST-TND-MOH-2026-001",
					"STD Engine",
				),
			],
			"technical_refs": {
				"bundle_output_code": "GB-TND-MOH-2026-001-V2",
				"dsm_output_code": "DSM-TND-MOH-2026-001-V2",
				"dom_output_code": "DOM-TND-MOH-2026-001-V2",
				"dem_output_code": "DEM-TND-MOH-2026-001-V2",
				"dcm_output_code": "DCM-TND-MOH-2026-001-V2",
			},
		},
		{
			"handoff_code": "PUBCERT-TND-MOH-2026-001",
			"handoff_title": "Tender Publication Certificate",
			"source_module": "Tender Management",
			"target_module": "Suppliers / Tender Closing",
			"source_object_type": "TM2 Tender",
			"source_object_code": "TND-MOH-2026-001",
			"target_object_type": "Supplier Portal / Tender Closing",
			"target_object_code": "TND-MOH-2026-001",
			"status": "Handed Off",
			"generated_by": "USER-PO-001",
			"generated_at": "2026-05-01 10:03:00",
			"consumed_by": "",
			"consumed_at": "",
			"next_action": "Suppliers may access the tender and submit bids before the revised submission deadline.",
			"locked_summary": {
				"published_tender": "TND-MOH-2026-001",
				"publication_snapshot": "PUBSNAP-TND-MOH-2026-001-V2",
				"procurement_method": "Open Tender",
				"procurement_category": "Works",
				"submission_deadline": "2026-06-05T11:00:00+03:00",
			},
			"passed_forward_summary": {
				"supplier_access_active": True,
				"tender_documents_available": True,
				"addendum_acknowledgement_required": True,
				"current_addendum": "ADD-TND-MOH-2026-001-01",
			},
			"evidence_links": [
				_el("Published Tender", "TM2 Tender", "TND-MOH-2026-001", "Tender Management"),
				_el(
					"Publication Snapshot",
					"Publication Snapshot",
					"PUBSNAP-TND-MOH-2026-001-V2",
					"Tender Management / STD Engine",
				),
				_el("Addendum 01", "Tender Addendum", "ADD-TND-MOH-2026-001-01", "Tender Management"),
			],
			"technical_refs": {
				"publication_code": "PUB-TND-MOH-2026-001-001",
				"publication_snapshot_code": "PUBSNAP-TND-MOH-2026-001-V2",
				"bundle_output_code": "GB-TND-MOH-2026-001-V2",
				"dsm_output_code": "DSM-TND-MOH-2026-001-V2",
				"dom_output_code": "DOM-TND-MOH-2026-001-V2",
				"dem_output_code": "DEM-TND-MOH-2026-001-V2",
				"dcm_output_code": "DCM-TND-MOH-2026-001-V2",
			},
		},
	]


def opening_handoff_blueprints() -> list[dict[str, Any]]:
	"""§16.9–16.10 — optional ``OPENING_READY`` checkpoint only."""
	return [
		{
			"handoff_code": "CLOSECERT-TND-MOH-2026-001",
			"handoff_title": "Tender Closing Certificate",
			"source_module": "Tender Management",
			"target_module": "Bid Opening",
			"source_object_type": "Tender Closing Record",
			"source_object_code": "CLS-TND-MOH-2026-001",
			"target_object_type": "Opening Readiness Record",
			"target_object_code": "ORR-TND-MOH-2026-001",
			"status": "Consumed",
			"generated_by": "SYSTEM",
			"generated_at": "2026-06-05 11:00:05",
			"consumed_by": "SYSTEM",
			"consumed_at": "2026-06-05 11:05:00",
			"next_action": "Prepare opening readiness using the opening register rules.",
			"locked_summary": {
				"submission_deadline": "2026-06-05T11:00:00+03:00",
				"closed_at": "2026-06-05T11:00:05+03:00",
				"official_time_source": "Server Time",
				"submission_window_closed": True,
			},
			"passed_forward_summary": {
				"valid_submission_count": 2,
				"late_attempt_count": 1,
				"sealed_submission_refs_available": True,
			},
			"evidence_links": [
				_el(
					"Tender Closing Record",
					"Tender Closing Record",
					"CLS-TND-MOH-2026-001",
					"Tender Management",
				),
			],
			"technical_refs": {
				"tender_code": "TND-MOH-2026-001",
				"publication_snapshot_code": "PUBSNAP-TND-MOH-2026-001-V2",
			},
		},
		{
			"handoff_code": "OPENREADY-TND-MOH-2026-001",
			"handoff_title": "Opening Readiness Record",
			"source_module": "Tender Management",
			"target_module": "Bid Opening",
			"source_object_type": "Opening Readiness Record",
			"source_object_code": "ORR-TND-MOH-2026-001",
			"target_object_type": "Bid Opening Session",
			"target_object_code": "",
			"status": "Handed Off",
			"generated_by": "SYSTEM",
			"generated_at": "2026-06-05 11:05:00",
			"consumed_by": "",
			"consumed_at": "",
			"next_action": "Conduct bid opening session using the opening register rules.",
			"locked_summary": {
				"opening_model": "DOM-TND-MOH-2026-001-V2",
				"publication_snapshot": "PUBSNAP-TND-MOH-2026-001-V2",
				"opening_scheduled_at": "2026-06-05T11:30:00+03:00",
				"arithmetic_correction_at_opening": False,
			},
			"passed_forward_summary": {
				"sealed_submission_refs": [
					"BID-TND-MOH-2026-001-SUP-ALPHA-01",
					"BID-TND-MOH-2026-001-SUP-BETA-01",
				],
				"opening_register_rules_ready": True,
				"display_submitted_total_only": True,
			},
			"evidence_links": [
				_el(
					"Opening Readiness Record",
					"Opening Readiness Record",
					"ORR-TND-MOH-2026-001",
					"Tender Management",
				),
			],
			"technical_refs": {
				"dom_output_code": "DOM-TND-MOH-2026-001-V2",
				"publication_snapshot_code": "PUBSNAP-TND-MOH-2026-001-V2",
			},
		},
	]
