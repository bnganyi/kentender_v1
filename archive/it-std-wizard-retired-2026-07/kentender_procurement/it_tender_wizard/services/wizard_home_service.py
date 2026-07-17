# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Configuration Home (Screen 02 v2) — canonical home payload builder."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_instance_service import (
	_get_instance,
	_validation_status_label,
)
from kentender_procurement.it_tender_wizard.services.wizard_overview_service import (
	CONFIGURABLE_OVERVIEW_STEP_CODES,
	OVERVIEW_STEP_CODES,
	STEP_OWNER_ROLE_LABELS,
	SYSTEM_STEP_CODES,
	_all_prior_configurable_complete,
	_derive_overview_completion_percent,
	_derive_overview_state_label,
	_latest_snapshot,
	list_wizard_steps,
	map_step_rail_status,
)

V2_HOME_STATUS_LABELS = frozenset(
	{
		"Not started",
		"In progress",
		"Needs attention",
		"Complete",
		"Available later",
	}
)

STEP_DESK_ROUTES: dict[str, str] = {
	"TENDER_PROFILE": "it-tender-configuration-tender-profile",
	"TDS": "it-tender-configuration-tds",
	"IT_REQUIREMENTS": "it-tender-configuration-it-requirements",
	"IMPLEMENTATION_SCHEDULE": "it-tender-configuration-implementation-schedule",
	"SYSTEM_INVENTORY": "it-tender-configuration-system-inventory",
	"PRICE_SCHEDULE": "it-tender-configuration-price-schedule",
	"EVALUATION_SETUP": "it-tender-configuration-evaluation-setup",
	"FORMS_AND_EVIDENCE": "it-tender-configuration-forms-and-evidence",
	"SCC": "it-tender-configuration-scc",
	"VALIDATION_REPORT": "it-tender-configuration-validation-report",
	"REVIEW_AND_APPROVAL": "it-tender-configuration-review-and-approval",
	"RENDER_PREVIEW": "it-tender-configuration-render-preview",
	"PUBLICATION_READINESS": "it-tender-configuration-publication-readiness",
}

HOME_STEP_CATALOG: tuple[dict[str, Any], ...] = (
	{
		"step_code": "TENDER_PROFILE",
		"step_number": 1,
		"step_key": "tender_profile",
		"step_label": "Tender Profile",
		"card_description": (
			"Confirm the tender title, scope summary, lot structure, participation settings, "
			"and basic context for this IT tender configuration."
		),
		"drawer_purpose": (
			"Confirm the basic identity and scope of the IT tender before detailed STD configuration begins."
		),
		"configure_there": [
			"Tender display title",
			"Scope summary",
			"Lot structure",
			"Alternatives setting",
			"Joint venture setting",
			"Reserved procurement setting where applicable",
			"Tender security applicability indicator",
			"Basic participation context",
		],
	},
	{
		"step_code": "TDS",
		"step_number": 2,
		"step_key": "tender_data_sheet",
		"step_label": "Tender Data Sheet",
		"card_description": (
			"Set tender-specific dates, submission rules, contacts, securities, currency, language, "
			"and other tender parameters."
		),
		"drawer_purpose": "Set the tender-specific data that customizes the standard IT tender instructions.",
		"configure_there": [
			"Dates and deadlines",
			"Clarification rules",
			"Submission rules",
			"Tender security settings",
			"Contact details",
			"Currency and language",
			"Preference/reservation applicability where allowed",
		],
	},
	{
		"step_code": "IT_REQUIREMENTS",
		"step_number": 3,
		"step_key": "it_requirements",
		"step_label": "IT Requirements",
		"card_description": (
			"Define the functional, technical, security, integration, support, warranty, deliverable, "
			"and acceptance requirements bidders must respond to."
		),
		"drawer_purpose": "Define what bidders must supply, implement, support, prove, and satisfy.",
		"configure_there": [
			"Functional requirements",
			"Technical requirements",
			"Security and compliance requirements",
			"Integration requirements",
			"Support and warranty requirements",
			"Deliverables",
			"Bidder response expectations",
			"Evidence instructions",
			"Acceptance criteria",
		],
	},
	{
		"step_code": "IMPLEMENTATION_SCHEDULE",
		"step_number": 4,
		"step_key": "implementation_schedule",
		"step_label": "Implementation Schedule",
		"card_description": (
			"Define whether delivery is phased or single-turnkey, then set delivery milestones, "
			"expected durations, deliverables, and acceptance checkpoints."
		),
		"drawer_purpose": "Define how the IT solution will be delivered.",
		"configure_there": [
			"Delivery approach",
			"Phased or single-turnkey delivery",
			"Milestones",
			"Expected durations",
			"Start triggers",
			"Deliverables",
			"Acceptance checkpoints",
			"Delivery evidence",
		],
	},
	{
		"step_code": "SYSTEM_INVENTORY",
		"step_number": 5,
		"step_key": "system_inventory",
		"step_label": "System Inventory",
		"card_description": (
			"Describe bidder-relevant existing systems, sites, users, integrations, data, infrastructure, "
			"licenses, and background context needed to understand the tender."
		),
		"drawer_purpose": (
			"Provide the bidder-relevant context needed to understand the existing environment and scope."
		),
		"configure_there": [
			"Existing systems",
			"Sites and locations",
			"User groups",
			"Integrations",
			"Data migration context",
			"Infrastructure context",
			"Licensing/support context",
			"Security disclosure context",
			"Background information",
		],
	},
	{
		"step_code": "PRICE_SCHEDULE",
		"step_number": 6,
		"step_key": "price_schedule",
		"step_label": "Price Schedule",
		"card_description": (
			"Define how bidders must price supply, installation, services, recurrent costs, optional items, "
			"taxes, currency, quantities, and evaluated price components."
		),
		"drawer_purpose": "Define how bidders must price the tender in a comparable way.",
		"configure_there": [
			"Supply and installation prices",
			"Recurrent costs",
			"Optional items",
			"Quantities and units",
			"Pricing basis",
			"Taxes and currency",
			"Evaluated price inclusion",
			"Bidder pricing instructions",
		],
	},
	{
		"step_code": "EVALUATION_SETUP",
		"step_number": 7,
		"step_key": "evaluation_setup",
		"step_label": "Evaluation Setup",
		"card_description": (
			"Define responsiveness checks, qualification criteria, technical scoring, financial evaluation "
			"method, pass marks, preferences, and post-qualification rules."
		),
		"drawer_purpose": "Define how bids will be assessed.",
		"configure_there": [
			"Preliminary responsiveness",
			"Eligibility and qualification checks",
			"Technical criteria",
			"Scoring weights",
			"Pass marks",
			"Financial evaluation method",
			"Preferences/reservations",
			"Post-qualification checks",
		],
	},
	{
		"step_code": "FORMS_AND_EVIDENCE",
		"step_number": 8,
		"step_key": "forms_evidence",
		"step_label": "Forms & Evidence",
		"card_description": (
			"Define the forms, declarations, certificates, technical evidence, financial forms, "
			"and supporting documents bidders must submit."
		),
		"drawer_purpose": "Define what bidders must submit with their bids.",
		"configure_there": [
			"Standard forms",
			"Declarations",
			"Eligibility evidence",
			"Qualification evidence",
			"Technical evidence",
			"Implementation evidence",
			"Financial forms",
			"Conditional or optional submissions",
		],
	},
	{
		"step_code": "SCC",
		"step_number": 9,
		"step_key": "scc_contract_values",
		"step_label": "SCC / Contract Values",
		"card_description": (
			"Confirm tender-specific contract values, SCC parameters, delivery obligations, "
			"warranty/support obligations, acceptance obligations, and contract attachments."
		),
		"drawer_purpose": "Confirm which configured tender values become contract-facing obligations.",
		"configure_there": [
			"SCC parameters",
			"Delivery obligations",
			"Technical obligations",
			"Support and warranty obligations",
			"Acceptance obligations",
			"Contract schedules",
			"Contract attachments",
		],
	},
	{
		"step_code": "VALIDATION_REPORT",
		"step_number": 10,
		"step_key": "validation",
		"step_label": "Validation",
		"card_description": (
			"Check whether the configured tender package is complete, internally consistent, "
			"and ready for formal review."
		),
		"drawer_purpose": "Check whether the tender configuration is complete and internally consistent.",
		"configure_there": [
			"Blockers",
			"Warnings",
			"Missing required values",
			"Inconsistent cross-links",
			"Readiness summary",
			"Links back to owning screens",
		],
	},
	{
		"step_code": "REVIEW_AND_APPROVAL",
		"step_number": 11,
		"step_key": "review_approval",
		"step_label": "Review & Approval",
		"card_description": (
			"Submit the Tender STD Configuration for procurement, technical, legal/compliance, "
			"and final configuration review."
		),
		"drawer_purpose": "Route the completed configuration through formal review.",
		"configure_there": [
			"Reviewer stages",
			"Submitted package summary",
			"Reviewer comments",
			"Return reasons",
			"Approval status",
			"Review history",
		],
	},
	{
		"step_code": "RENDER_PREVIEW",
		"step_number": 12,
		"step_key": "final_preview",
		"step_label": "Final Preview",
		"card_description": (
			"Review the generated tender package exactly as it will be handed forward, "
			"without editing configuration content on this screen."
		),
		"drawer_purpose": "Confirm the generated tender package before publication readiness.",
		"configure_there": [
			"Rendered tender document",
			"Generated schedules",
			"Generated forms",
			"Configuration comparison summary",
			"Preview confirmation checklist",
		],
	},
	{
		"step_code": "PUBLICATION_READINESS",
		"step_number": 13,
		"step_key": "publication_readiness",
		"step_label": "Publication Readiness",
		"card_description": (
			"Confirm that the approved and preview-confirmed package is ready to hand over to "
			"Tender Management for publication workflow."
		),
		"drawer_purpose": "Mark the package ready for handoff to Tender Management.",
		"configure_there": [
			"Publication-readiness checklist",
			"Final package contents",
			"Handoff summary",
			"Next owner",
			"Tender Management handoff action",
		],
	},
)

_CATALOG_BY_CODE = {row["step_code"]: row for row in HOME_STEP_CATALOG}


def map_rail_to_home_status(rail_status: str, *, blockers: int = 0, warnings: int = 0) -> str:
	if rail_status in {"LOCKED", "NOT_AVAILABLE"}:
		return "Available later"
	if blockers or rail_status == "HAS_BLOCKERS":
		return "Needs attention"
	if rail_status == "IN_PROGRESS":
		return "In progress"
	if rail_status in {"COMPLETE", "HAS_WARNINGS"}:
		return "Complete"
	return "Not started"


def map_home_action_label(
	step_code: str,
	rail_status: str,
	status_label: str,
) -> str:
	if status_label == "Available later":
		return "View dependency"
	if status_label == "Needs attention":
		return "Fix"
	if status_label == "In progress":
		return "Continue"
	if status_label == "Complete":
		return "Review"
	if step_code == "VALIDATION_REPORT":
		return "Run Validation"
	if step_code == "REVIEW_AND_APPROVAL":
		return "Submit for Review"
	if step_code == "RENDER_PREVIEW":
		return "Open Final Preview"
	if step_code == "PUBLICATION_READINESS":
		return "Open Publication Readiness"
	return "Start"


def _step_route(step_code: str) -> str:
	return STEP_DESK_ROUTES.get(step_code, "")


def _resolve_tender_ref(doc) -> str:
	tender_number = frappe.db.get_value(
		"Wizard Step Instance",
		{"tender_std_instance": doc.name, "step_code": "TDS"},
		"step_title",
	)
	if doc.bound_tender_id:
		return doc.bound_tender_id
	return doc.instance_code


def _issues_summary(blockers: int, warnings: int) -> str:
	if blockers and warnings:
		return f"{blockers} Blocker{'s' if blockers != 1 else ''} / {warnings} Warning{'s' if warnings != 1 else ''}"
	if blockers:
		return f"{blockers} Blocker{'s' if blockers != 1 else ''}"
	if warnings:
		return f"{warnings} Warning{'s' if warnings != 1 else ''}"
	return "No issues"


def _dependency_step_label(step_code: str, steps: list[dict[str, Any]]) -> str | None:
	for row in steps:
		if row["step_code"] == step_code:
			break
		if row["step_code"] not in CONFIGURABLE_OVERVIEW_STEP_CODES:
			continue
		if (row.get("status") or "").strip() != "COMPLETE":
			catalog = _CATALOG_BY_CODE.get(row["step_code"])
			return (catalog or {}).get("step_label") or row.get("step_title")
	return None


def _availability_reason(step_code: str, rail_status: str, steps: list[dict[str, Any]]) -> str | None:
	if rail_status not in {"LOCKED", "NOT_AVAILABLE"}:
		return None
	dependency = _dependency_step_label(step_code, steps)
	if dependency:
		return f"Complete {dependency} first."
	return "Complete previous steps first."


def _serialize_home_steps(
	doc,
	steps: list[dict[str, Any]],
	snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
	current_code = (doc.current_step_code or "").strip()
	result: list[dict[str, Any]] = []
	for catalog in HOME_STEP_CATALOG:
		step_code = catalog["step_code"]
		row = next((item for item in steps if item["step_code"] == step_code), None)
		if not row:
			continue
		is_current = step_code == current_code
		all_prior_complete = _all_prior_configurable_complete(steps, step_code)
		blockers = 0
		warnings = 0
		if is_current:
			blockers = int(snapshot.get("blocking_findings_count") or 0)
			warnings = int(snapshot.get("warning_findings_count") or 0)
		rail_status = map_step_rail_status(
			row,
			all_prior_configurable_complete=all_prior_complete,
			is_current=is_current,
			blockers=blockers,
			warnings=warnings,
		)
		status_label = map_rail_to_home_status(rail_status, blockers=blockers, warnings=warnings)
		action_label = map_home_action_label(step_code, rail_status, status_label)
		last_updated = row.get("modified") or row.get("creation")
		result.append(
			{
				"step_code": step_code,
				"step_number": catalog["step_number"],
				"step_key": catalog["step_key"],
				"step_label": catalog["step_label"],
				"card_description": catalog["card_description"],
				"drawer_purpose": catalog["drawer_purpose"],
				"configure_there": list(catalog["configure_there"]),
				"status_label": status_label,
				"blocker_count": blockers,
				"warning_count": warnings,
				"availability_reason": _availability_reason(step_code, rail_status, steps),
				"last_updated_at": str(last_updated) if last_updated else None,
				"action_label": action_label,
				"route": _step_route(step_code),
				"is_current": is_current,
				"_rail_status": rail_status,
			}
		)
	return result


def resolve_next_action(
	home_steps: list[dict[str, Any]],
	*,
	doc,
	blockers: int,
	warnings: int,
) -> dict[str, Any]:
	for step in home_steps:
		if step["status_label"] == "Needs attention":
			return {
				"label": f"Fix {step['step_label']}",
				"reason": step["drawer_purpose"],
				"button_label": "Fix",
				"route": step["route"],
			}

	current_code = (doc.current_step_code or "").strip()
	for step in home_steps:
		if step["step_code"] == current_code and step["status_label"] == "In progress":
			return {
				"label": f"Continue {step['step_label']}",
				"reason": step["drawer_purpose"],
				"button_label": "Continue",
				"route": step["route"],
			}

	for step in home_steps:
		if step["status_label"] == "In progress":
			return {
				"label": f"Continue {step['step_label']}",
				"reason": step["drawer_purpose"],
				"button_label": "Continue",
				"route": step["route"],
			}

	for step in home_steps:
		if step["status_label"] == "Not started" and step["step_code"] in CONFIGURABLE_OVERVIEW_STEP_CODES:
			return {
				"label": f"Start {step['step_label']}",
				"reason": step["drawer_purpose"],
				"button_label": "Start",
				"route": step["route"],
			}

	configurable_complete = all(
		step["status_label"] in {"Complete", "Needs attention"}
		for step in home_steps
		if step["step_code"] in CONFIGURABLE_OVERVIEW_STEP_CODES
	)
	validation_step = next((s for s in home_steps if s["step_code"] == "VALIDATION_REPORT"), None)
	review_step = next((s for s in home_steps if s["step_code"] == "REVIEW_AND_APPROVAL"), None)
	preview_step = next((s for s in home_steps if s["step_code"] == "RENDER_PREVIEW"), None)
	publication_step = next((s for s in home_steps if s["step_code"] == "PUBLICATION_READINESS"), None)

	if configurable_complete and validation_step and validation_step["status_label"] == "Not started":
		return {
			"label": "Run Validation",
			"reason": validation_step["drawer_purpose"],
			"button_label": "Run Validation",
			"route": validation_step["route"],
		}

	if validation_step and validation_step["status_label"] == "Complete" and not blockers:
		if review_step and review_step["status_label"] in {"Not started", "In progress"}:
			return {
				"label": "Submit for Review",
				"reason": review_step["drawer_purpose"],
				"button_label": "Submit for Review",
				"route": review_step["route"],
			}

	if doc.wizard_state in {ws.READY_FOR_REVIEW, ws.PROCUREMENT_REVIEW, ws.TECHNICAL_REVIEW, ws.LEGAL_REVIEW} and review_step:
		return {
			"label": f"Continue {review_step['step_label']}",
			"reason": review_step["drawer_purpose"],
			"button_label": "Submit for Review",
			"route": review_step["route"],
		}

	if preview_step and preview_step["status_label"] in {"Not started", "In progress"}:
		if doc.wizard_state in {ws.APPROVED_FOR_TENDER_CREATION, ws.READY_FOR_REVIEW}:
			return {
				"label": "Open Final Preview",
				"reason": preview_step["drawer_purpose"],
				"button_label": "Open Final Preview",
				"route": preview_step["route"],
			}

	if publication_step and publication_step["status_label"] in {"Not started", "In progress"}:
		return {
			"label": "Open Publication Readiness",
			"reason": publication_step["drawer_purpose"],
			"button_label": "Open Publication Readiness",
			"route": publication_step["route"],
		}

	fallback = next((s for s in home_steps if s["is_current"]), home_steps[0] if home_steps else None)
	if fallback:
		return {
			"label": f"Review {fallback['step_label']}",
			"reason": fallback["drawer_purpose"],
			"button_label": fallback["action_label"],
			"route": fallback["route"],
		}
	return {
		"label": "Review configuration progress",
		"reason": "Review the configuration steps and continue where you left off.",
		"button_label": "Review",
		"route": STEP_DESK_ROUTES["TENDER_PROFILE"],
	}


def build_configuration_home(configuration_id: str) -> dict[str, Any]:
	doc = _get_instance(configuration_id)
	snapshot = _latest_snapshot(doc.name)
	blockers = int(snapshot.get("blocking_findings_count") or 0)
	warnings = int(snapshot.get("warning_findings_count") or 0)
	steps = list_wizard_steps(doc.name)
	home_steps = _serialize_home_steps(doc, steps, snapshot)
	wizard_steps_legacy = [
		{
			"step_code": row["step_code"],
			"step_order": row["step_number"],
			"step_title": row["step_label"],
			"rail_status": row["_rail_status"],
			"is_current": row["is_current"],
			"blockers": row["blocker_count"],
			"warnings": row["warning_count"],
			"owner_role_label": STEP_OWNER_ROLE_LABELS.get(row["step_code"], "Procurement Officer"),
			"action_label": row["action_label"],
		}
		for row in home_steps
	]
	derived_completion_percent = _derive_overview_completion_percent(wizard_steps_legacy)
	derived_state_label = _derive_overview_state_label(
		doc,
		wizard_steps_legacy,
		derived_completion_percent=derived_completion_percent,
	)
	next_action = resolve_next_action(
		home_steps,
		doc=doc,
		blockers=blockers,
		warnings=warnings,
	)
	wizard_steps_legacy = [
		{
			"step_code": row["step_code"],
			"step_order": row["step_number"],
			"step_title": row["step_label"],
			"rail_status": row["_rail_status"],
			"is_current": row["is_current"],
			"blockers": row["blocker_count"],
			"warnings": row["warning_count"],
			"owner_role_label": STEP_OWNER_ROLE_LABELS.get(row["step_code"], "Procurement Officer"),
			"action_label": row["action_label"],
		}
		for row in home_steps
	]
	public_steps = [{key: value for key, value in row.items() if not key.startswith("_")} for row in home_steps]
	return {
		"configuration_id": doc.instance_code,
		"tender_ref": _resolve_tender_ref(doc),
		"tender_title": doc.instance_title,
		"planning_package_ref": doc.planning_package_code or "",
		"procuring_entity_name": doc.procuring_entity_name or "",
		"procurement_method_label": doc.procurement_method_name or "",
		"wizard_state_label": derived_state_label,
		"blocker_count": blockers,
		"warning_count": warnings,
		"issues_summary": _issues_summary(blockers, warnings),
		"next_action": next_action,
		"steps": public_steps,
		"title": doc.instance_title,
		"state": doc.wizard_state,
		"state_label": derived_state_label,
		"completion_percent": derived_completion_percent,
		"validation": {
			"status": _validation_status_label(doc.current_validation_status, blockers, warnings),
			"blockers": blockers,
			"warnings": warnings,
			"last_run_at": str(snapshot.get("snapshot_at")) if snapshot.get("snapshot_at") else None,
		},
	}
