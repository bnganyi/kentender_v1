# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PE-neutral Technical Proposal subsection fixtures for lean seeds."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

FIXTURE_CORE = "core"
FIXTURE_FULL = "full"
FIXTURE_CONDITIONAL = "conditional"

SUB_ORG = "project_organization_and_coordination"
SUB_INTEGRATION = "integration_responsibility_confirmation"
SUB_APPROACH = "technical_approach"
SUB_WORK_PLAN = "implementation_work_plan"
SUB_TRAINING = "training_and_knowledge_transfer"
SUB_TESTING = "testing_and_quality_assurance"
SUB_WARRANTY = "warranty_defect_repair_and_support"
SUB_TRANSITION = "transition_and_handover"
SUB_RISKS = "risks_assumptions_and_dependencies"
SUB_ALTERNATIVES = "technical_alternatives"

MODE_REQUIRED = "required"
MODE_OPTIONAL = "optional"
MODE_CONDITIONAL = "conditional"
MODE_EXCLUDED = "excluded"

SCOPE_TENDER = "tender"
SCOPE_LOT = "lot"

CONDITION_ALWAYS = "always"
CONDITION_ALT_PERMITTED = "technical_alternatives_permitted"
CONDITION_TRAINING = "training_required_by_tds"
CONDITION_WARRANTY = "warranty_support_required_by_tds"
CONDITION_MIGRATION = "data_migration_in_requirements"
CONDITION_LOT_TOPIC = "lot_topic_selected"

RENDERER_ORG = "project_organization_and_coordination"
RENDERER_APPROACH = "technical_approach"
RENDERER_WORK_PLAN = "implementation_work_plan"
RENDERER_TRAINING = "training_and_knowledge_transfer"
RENDERER_TESTING = "testing_and_quality_assurance"
RENDERER_WARRANTY = "warranty_defect_repair_and_support"
RENDERER_TRANSITION = "transition_and_handover"
RENDERER_RISKS = "risks_assumptions_and_dependencies"
RENDERER_ALTERNATIVES = "technical_alternatives"
RENDERER_INTEGRATION = "integration_responsibility_confirmation"


def _q(
	qid: str,
	title: str,
	*,
	required: bool = True,
	response_type: str = "narrative",
	guidance: str = "",
) -> dict[str, Any]:
	row = {
		"question_id": qid,
		"title": title,
		"required": required,
		"response_type": response_type,
	}
	if guidance:
		row["guidance"] = guidance
	return row


def _base_subsections() -> list[dict[str, Any]]:
	return [
		{
			"subsection_key": SUB_ORG,
			"title": "Project organization and coordination",
			"description": "Describe management, resources and coordination with the Procuring Entity and third parties.",
			"renderer": RENDERER_ORG,
			"display_order": 10,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [
				_q("org-mgmt", "Overall project-management approach"),
				_q("org-reporting", "Reporting arrangements"),
				_q("org-comms", "Communication arrangements"),
				_q("org-escalation", "Decision-making and escalation"),
				_q("org-coord", "Coordination between involved parties"),
			],
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_APPROACH,
			"title": "Technical approach",
			"description": "Explain the proposed solution, architecture and delivery methodology.",
			"renderer": RENDERER_APPROACH,
			"display_order": 20,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [
				_q(
					"ta-overview",
					"Proposed solution overview",
					guidance=(
						"Provide a high-level summary of your proposed solution, detailing how it "
						"addresses the core objectives of this procurement."
					),
				),
				_q(
					"ta-architecture",
					"Technical architecture",
					guidance=(
						"Describe the system architecture, including major software components, "
						"hardware requirements, and data flow models."
					),
				),
				_q(
					"ta-components",
					"Major solution components",
					guidance="Identify the major solution components and how they fit together.",
				),
				_q(
					"ta-methodology",
					"Delivery methodology",
					guidance=(
						"Detail your preferred project management methodology and how it will be "
						"applied to this implementation."
					),
				),
				_q(
					"ta-integration",
					"Integration approach",
					guidance=(
						"Explain your strategy for integrating the proposed system with existing "
						"enterprise systems and APIs."
					),
				),
				_q(
					"ta-interop",
					"Interoperability approach",
					guidance="Describe interoperability standards, interfaces and data exchange arrangements.",
				),
			],
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_WORK_PLAN,
			"title": "Implementation work plan",
			"description": "Provide structured activities with timing from Contract Effective Date.",
			"renderer": RENDERER_WORK_PLAN,
			"display_order": 30,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [],
			"min_activities": 1,
			"max_completion_weeks": 52,
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_TRAINING,
			"title": "Training and knowledge transfer",
			"description": "Define training audiences, topics and delivery arrangements.",
			"renderer": RENDERER_TRAINING,
			"display_order": 40,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [],
			"min_activities": 1,
			"audiences": ["End users", "Administrators", "Technical support"],
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_TESTING,
			"title": "Testing and quality assurance",
			"description": "Describe QA approach and test stages through operational acceptance.",
			"renderer": RENDERER_TESTING,
			"display_order": 50,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [
				_q("qa-approach", "Quality assurance approach"),
				_q("qa-config", "Configuration control"),
				_q("qa-change", "Change control"),
				_q("qa-defect", "Defect management"),
				_q("qa-commission", "Commissioning"),
				_q("qa-oa", "Operational-acceptance preparation"),
			],
			"min_test_stages": 1,
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_WARRANTY,
			"title": "Warranty, defect repair and support",
			"description": "Describe warranty, defect reporting and support arrangements.",
			"renderer": RENDERER_WARRANTY,
			"display_order": 60,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [
				_q("warr-approach", "Warranty-support approach"),
				_q("warr-defect", "Defect-reporting process"),
				_q("warr-response", "Response and restoration arrangements"),
				_q("warr-escalation", "Escalation"),
				_q("warr-channels", "Support channels and hours"),
			],
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_TRANSITION,
			"title": "Transition and handover",
			"description": "Plan cutover, continuity and operational handover.",
			"renderer": RENDERER_TRANSITION,
			"display_order": 70,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [
				_q("tr-cutover", "Cutover approach"),
				_q("tr-continuity", "Service continuity"),
				_q("tr-docs", "Documentation handover"),
				_q("tr-admin", "Administrator handover"),
			],
			"handover_deliverables": [
				{"deliverable_id": "hd-ops-manual", "title": "Operations manual", "required": 1},
				{"deliverable_id": "hd-admin-guide", "title": "Administrator guide", "required": 1},
				{
					"deliverable_id": "hd-source-access",
					"title": "Source / configuration access credentials",
					"required": 1,
				},
				{"deliverable_id": "hd-training-pack", "title": "Training materials pack", "required": 0},
			],
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_RISKS,
			"title": "Risks, assumptions and dependencies",
			"description": "Record risks, assumptions and dependencies with mitigations.",
			"renderer": RENDERER_RISKS,
			"display_order": 80,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [],
			"min_risks": 1,
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_ALTERNATIVES,
			"title": "Technical alternatives",
			"description": "Propose permitted alternatives without replacing the base proposal.",
			"renderer": RENDERER_ALTERNATIVES,
			"display_order": 90,
			"requirement_mode": MODE_CONDITIONAL,
			"condition_key": CONDITION_ALT_PERMITTED,
			"scope": SCOPE_TENDER,
			"questions": [],
			# Illustrative permitted modules — PE config may override; never NSSF-hardcoded.
			"permitted_scope": [
				{"scope_id": "ps-storage", "title": "Data storage layer", "icon": "database"},
				{"scope_id": "ps-mobile", "title": "Mobile application framework", "icon": "smartphone"},
			],
			"evidence_required": False,
		},
		{
			"subsection_key": SUB_INTEGRATION,
			"title": "Integration and interoperability confirmation",
			"description": "Confirm responsibility for successful integration and interoperability.",
			"renderer": RENDERER_INTEGRATION,
			"display_order": 100,
			"requirement_mode": MODE_REQUIRED,
			"condition_key": CONDITION_ALWAYS,
			"scope": SCOPE_TENDER,
			"questions": [],
			"evidence_required": False,
		},
	]


def cstr_fixture(fixture: str | None) -> str:
	raw = (fixture or FIXTURE_FULL).strip().lower()
	if raw in (FIXTURE_CORE, FIXTURE_FULL, FIXTURE_CONDITIONAL):
		return raw
	if raw in ("reduced",):
		return FIXTURE_CORE
	return FIXTURE_FULL


def lean_technical_proposal_subsections(fixture: str = FIXTURE_FULL) -> list[dict[str, Any]]:
	"""Return subsection configuration for core / full / conditional fixtures."""
	subs = deepcopy(_base_subsections())
	key = cstr_fixture(fixture)
	if key == FIXTURE_CORE:
		keep = {SUB_ORG, SUB_INTEGRATION}
		for sub in subs:
			if sub["subsection_key"] in keep:
				sub["requirement_mode"] = MODE_REQUIRED
				sub["condition_key"] = CONDITION_ALWAYS
			else:
				sub["requirement_mode"] = MODE_EXCLUDED
				sub["condition_key"] = CONDITION_ALWAYS
		return subs
	if key == FIXTURE_CONDITIONAL:
		for sub in subs:
			sk = sub["subsection_key"]
			if sk in (SUB_ORG, SUB_INTEGRATION, SUB_APPROACH, SUB_WORK_PLAN):
				sub["requirement_mode"] = MODE_REQUIRED
				sub["condition_key"] = CONDITION_ALWAYS
			elif sk == SUB_TRAINING:
				sub["requirement_mode"] = MODE_OPTIONAL
				sub["condition_key"] = CONDITION_ALWAYS
			elif sk == SUB_TRANSITION:
				# Migration-style topic excluded unless migration condition is wired later
				sub["requirement_mode"] = MODE_EXCLUDED
				sub["condition_key"] = CONDITION_MIGRATION
			elif sk == SUB_ALTERNATIVES:
				sub["requirement_mode"] = MODE_CONDITIONAL
				sub["condition_key"] = CONDITION_ALT_PERMITTED
			elif sk == SUB_WARRANTY:
				sub["requirement_mode"] = MODE_CONDITIONAL
				sub["condition_key"] = CONDITION_WARRANTY
			elif sk in (SUB_TESTING, SUB_RISKS):
				sub["requirement_mode"] = MODE_REQUIRED
				sub["condition_key"] = CONDITION_ALWAYS
			else:
				sub["requirement_mode"] = MODE_EXCLUDED
		# Lot-specific work-plan topic (additional row for conditional fixture)
		subs.append(
			{
				"subsection_key": "lot_implementation_topic",
				"title": "Lot-specific implementation topic",
				"description": "Answer once per selected lot when this topic applies.",
				"renderer": RENDERER_APPROACH,
				"display_order": 95,
				"requirement_mode": MODE_CONDITIONAL,
				"condition_key": CONDITION_LOT_TOPIC,
				"scope": SCOPE_LOT,
				"questions": [
					_q("lot-impl", "Lot-specific implementation approach"),
				],
				"evidence_required": False,
			}
		)
		return subs
	# full — exclude only alternatives unless permitted (keep conditional)
	for sub in subs:
		if sub["subsection_key"] == SUB_ALTERNATIVES:
			sub["requirement_mode"] = MODE_CONDITIONAL
			sub["condition_key"] = CONDITION_ALT_PERMITTED
	return subs


def merge_technical_proposal_into_evaluation(
	evaluation: dict[str, Any] | None,
	*,
	fixture: str = FIXTURE_FULL,
	flags: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Attach technical_proposal_subsections (+ optional TDS flags) to evaluation_setup."""
	out = dict(evaluation) if isinstance(evaluation, dict) else {}
	out["technical_proposal_subsections"] = lean_technical_proposal_subsections(fixture)
	out["technical_proposal_fixture"] = cstr_fixture(fixture)
	base_flags = {
		"technical_alternatives_permitted": 0,
		"training_required_by_tds": 1,
		"warranty_support_required_by_tds": 1,
		"data_migration_in_requirements": 0,
		"lot_topic_selected": 0,
	}
	if cstr_fixture(fixture) == FIXTURE_FULL:
		base_flags["technical_alternatives_permitted"] = 0
	if cstr_fixture(fixture) == FIXTURE_CONDITIONAL:
		base_flags["technical_alternatives_permitted"] = 0
		base_flags["warranty_support_required_by_tds"] = 0
		base_flags["data_migration_in_requirements"] = 0
		base_flags["lot_topic_selected"] = 1
	if isinstance(flags, dict):
		base_flags.update(flags)
	out["technical_proposal_flags"] = base_flags
	return out
