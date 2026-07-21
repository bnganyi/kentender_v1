# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-family configuration step profiles for UI-01 (C1-M3 §§6–10)."""

from __future__ import annotations

from typing import Any

# Allowed step status labels (UI-01 §8) — never Ready / Locked
STEP_NOT_STARTED = "Not started"
STEP_IN_PROGRESS = "In progress"
STEP_NEEDS_ATTENTION = "Needs attention"
STEP_COMPLETE = "Complete"
STEP_NOT_AVAILABLE = "Not available yet"

STEP_ACTION_BY_STATUS = {
	STEP_NOT_STARTED: "Start",
	STEP_IN_PROGRESS: "Continue",
	STEP_NEEDS_ATTENTION: "Fix",
	STEP_COMPLETE: "Review",
	STEP_NOT_AVAILABLE: "View required step",
}

ALLOWED_STEP_STATUSES = frozenset(STEP_ACTION_BY_STATUS)

# Desk page slugs (existing Page DocTypes)
STEP_ROUTES: dict[str, str] = {
	"CFG-01": "it-tender-configuration-tender-profile",
	"CFG-02": "it-tender-configuration-tds",
	"CFG-03": "it-tender-configuration-it-requirements",
	"CFG-04": "it-tender-configuration-implementation-schedule",
	"CFG-05": "it-tender-configuration-system-inventory",
	"CFG-06": "it-tender-configuration-price-schedule",
	"CFG-07": "it-tender-configuration-evaluation-setup",
	"CFG-08": "it-tender-configuration-forms-and-evidence",
	"CFG-09": "it-tender-configuration-scc",
}

HANDOFF_ROUTES = {
	"readiness_check": "it-tender-configuration-validation-report",
	"review_status": "it-tender-configuration-review-and-approval",
	"tender_document_preview": "it-tender-configuration-render-preview",
	"package_review": "it-tender-package-review",
	"publications": "publications",
	"publication_setup": "publication-setup",
	# Legacy key — Package Review is the primary surface after approval.
	"publication_handoff": "it-tender-package-review",
}

# Exact catalog from C1-M3 §§6–10 for Information Technology
_IT_STEPS: list[dict[str, str]] = [
	{
		"id": "CFG-01",
		"title": "Tender Profile",
		"description": (
			"Confirm the tender identity, procuring entity, procurement method, "
			"lot structure, planning reference, and basic setup context before detailed configuration."
		),
		"will_configure": (
			"Tender identity, procuring entity, procurement method, lot structure, "
			"planning reference, and basic setup context."
		),
		"will_not_configure": (
			"TDS parameters, technical requirements, pricing, evaluation, contract values, "
			"review, preview, or publication."
		),
	},
	{
		"id": "CFG-02",
		"title": "Tender Data Sheet",
		"description": (
			"Enter the tender-specific instructions and parameters that complete the "
			"Instructions to Tenderers through the Tender Data Sheet."
		),
		"will_configure": (
			"Tender-specific instructions, deadlines, submission rules, securities, "
			"language, currency, and permitted ITT parameters."
		),
		"will_not_configure": (
			"Technical specifications, price rows, evaluation scores, bidder submissions, "
			"contract administration, or publication."
		),
	},
	{
		"id": "CFG-03",
		"title": "IT Requirements",
		"description": (
			"Define what bidders must supply, deliver, integrate, support, or prove, "
			"including bidder response, evidence, and acceptance expectations."
		),
		"will_configure": (
			"Requirement statements, bidder response instructions, evidence expectations, "
			"and acceptance expectations."
		),
		"will_not_configure": (
			"Scoring marks, price lines, actual bidder responses, evaluation results, "
			"contract administration, or publication."
		),
	},
	{
		"id": "CFG-04",
		"title": "Implementation Schedule",
		"description": (
			"Choose the delivery approach and define milestones, durations, deliverables, "
			"and acceptance checkpoints."
		),
		"will_configure": (
			"Delivery approach, milestones, durations, deliverables, start triggers, "
			"and acceptance checkpoints."
		),
		"will_not_configure": (
			"Live project execution, inspection records, payment certification, "
			"contract administration, or publication."
		),
	},
	{
		"id": "CFG-05",
		"title": "System Inventory & Bidder Background",
		"description": (
			"Describe bidder-relevant inventory, sites, existing systems, integrations, "
			"recurrent context, and background information without creating hidden requirements."
		),
		"will_configure": (
			"Bidder-relevant inventory, sites, existing systems, integrations, "
			"recurrent context, and background materials."
		),
		"will_not_configure": (
			"Full pricing setup, evaluation scoring, hidden requirements in background text, "
			"contract administration, or publication."
		),
	},
	{
		"id": "CFG-06",
		"title": "Price Schedule",
		"description": "Define the supply, installation, and recurrent cost items bidders must price.",
		"will_configure": (
			"Supply, installation, and recurrent cost items, pricing basis, units, "
			"quantities, and pricing instructions."
		),
		"will_not_configure": (
			"Technical requirement wording, actual bid prices, evaluation scoring, "
			"contract administration, or publication."
		),
	},
	{
		"id": "CFG-07",
		"title": "Evaluation Setup",
		"description": (
			"Set the preliminary, technical, financial, preference, qualification, "
			"and post-qualification evaluation rules."
		),
		"will_configure": (
			"Preliminary, technical, financial, preference, qualification, "
			"and post-qualification evaluation rules."
		),
		"will_not_configure": (
			"Actual bid evaluation, award recommendation, requirement drafting, "
			"price entry, or publication."
		),
	},
	{
		"id": "CFG-08",
		"title": "Forms & Evidence",
		"description": (
			"Define all non-price forms, declarations, qualification documents, "
			"securities, and evidence bidders must submit."
		),
		"will_configure": (
			"Non-price forms, declarations, qualification forms, securities, "
			"evidence instructions, and submission requirements."
		),
		"will_not_configure": (
			"Actual bidder uploads, evidence verification, evaluation scoring, "
			"price schedule forms, or publication."
		),
	},
	{
		"id": "CFG-09",
		"title": "Contract Values",
		"description": (
			"Confirm the Special Conditions of Contract values and contract-facing "
			"obligations that vary from the standard contract."
		),
		"will_configure": (
			"SCC values, contract-facing parameters, obligations, warranties, "
			"securities, and contract appendices carried from the configuration."
		),
		"will_not_configure": (
			"Post-award contract administration, change orders, inspections, "
			"payment certification, or publication."
		),
	},
]

_FAMILY_STEPS: dict[str, list[dict[str, str]]] = {
	"IT": _IT_STEPS,
	"INFORMATION TECHNOLOGY": _IT_STEPS,
}


def get_steps_for_family(std_family_key: str | None) -> list[dict[str, str]]:
	"""Return ordered step catalog for the STD family (IT for current implementation)."""
	key = (std_family_key or "IT").strip().upper().replace("-", "_").replace(" ", "_")
	if key in ("IT", "INFORMATION_TECHNOLOGY", "KE_PPRA_IT"):
		return [dict(s) for s in _IT_STEPS]
	# Future families: empty until profiles exist — fall back to IT for wizard v3 IT path
	return [dict(s) for s in _IT_STEPS]


def action_for_status(status_label: str) -> str:
	return STEP_ACTION_BY_STATUS.get(status_label, "Start")


def desk_route_for_step(step_id: str) -> str:
	return STEP_ROUTES.get(step_id, "")


def merge_step_rows(
	catalog: list[dict[str, str]],
	steps_state: dict[str, Any] | None,
	doc: Any | None = None,
) -> list[dict[str, Any]]:
	"""Merge catalog with persisted steps_state into UI-01 configuration_steps rows.

	Progress comes from exit-condition checklists (see step_progress.py), not decorative defaults.
	Pass ``doc`` so registered CFG checkers (e.g. CFG-01) can read live fields.
	"""
	from kentender_procurement.tender_configurations.services.step_progress import (
		compute_step_progress,
	)

	state = steps_state or {}
	rows: list[dict[str, Any]] = []
	for meta in catalog:
		sid = meta["id"]
		st = state.get(sid) or {}
		status = st.get("status_label") or STEP_NOT_STARTED
		if status not in ALLOWED_STEP_STATUSES:
			status = STEP_NOT_STARTED
		blockers = int(st.get("blocker_count") or 0)
		warnings = int(st.get("warning_count") or 0)
		route = desk_route_for_step(sid)
		progress = compute_step_progress(sid, status_label=status, doc=doc, step_state=st)
		rows.append(
			{
				"id": sid,
				"title": meta["title"],
				"description": meta["description"],
				"status_label": status,
				"blocker_count": blockers,
				"warning_count": warnings,
				"last_updated_label": st.get("last_updated_label") or None,
				"progress_pct": progress["progress_pct"],
				"progress_met_count": progress["met_count"],
				"progress_required_count": progress["required_count"],
				"show_progress_bar": progress["show_progress_bar"],
				"action_label": action_for_status(status),
				"route": route,
				"will_configure": meta["will_configure"],
				"will_not_configure": meta["will_not_configure"],
			}
		)
	return rows
